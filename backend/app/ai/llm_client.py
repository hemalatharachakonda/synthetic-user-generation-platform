"""
Thin async wrapper around LiteLLM. Tries each ModelRouter candidate in order
(Gemini -> Ollama) and returns the first successful structured JSON response.
Raises LLMUnavailableError if every candidate fails, so callers (agents) can
decide how to degrade gracefully (e.g. synthetic Faker fallback).
"""
import json

from loguru import logger

from app.ai.model_router import ModelCandidate, ModelRouter
from app.core.config import get_settings
from app.exceptions.llm_exceptions import (
    LLMRateLimitError,
    LLMResponseParsingError,
    LLMTimeoutError,
    LLMUnavailableError,
)

try:
    import litellm
except Exception as exc:  # pragma: no cover - environment-dependent
    litellm = None
    _litellm_import_error = exc
else:
    _litellm_import_error = None
    litellm.drop_params = True  # ignore provider-unsupported params instead of raising


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.router = ModelRouter()

    async def _call_one(self, candidate: ModelCandidate, system_prompt: str, user_prompt: str) -> str:
        if litellm is None:
            raise LLMUnavailableError(
                f"LiteLLM could not be imported: {_litellm_import_error}"
            ) from _litellm_import_error

        kwargs = {
            "model": candidate.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.settings.LLM_TEMPERATURE,
            "max_tokens": self.settings.LLM_MAX_TOKENS,
            "timeout": self.settings.LLM_TIMEOUT_SECONDS,
            "response_format": {"type": "json_object"},
        }
        if candidate.api_key:
            kwargs["api_key"] = candidate.api_key
        if candidate.api_base:
            kwargs["api_base"] = candidate.api_base

        response = await litellm.acompletion(**kwargs)
        return response.choices[0].message.content

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Attempts each configured provider in order. Returns a parsed dict on
        first success. Raises LLMUnavailableError if all candidates fail.
        """
        last_error: Exception | None = None

        for candidate in self.router.candidates():
            try:
                raw = await self._call_one(candidate, system_prompt, user_prompt)
                return self._parse_json(raw)
            except LLMResponseParsingError:
                raise  # a provider responded but gave unusable content; don't mask this
            except Exception as e:  # noqa: BLE001 - genuinely want to try the next provider
                last_error = e
                logger.warning(f"[{candidate.provider}] call failed ({e}), trying next candidate")

        raise LLMUnavailableError(
            f"All LLM providers failed. Last error: {last_error}"
        ) from last_error

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMResponseParsingError(f"Could not parse LLM output as JSON: {e}\nRaw: {raw[:500]}") from e
