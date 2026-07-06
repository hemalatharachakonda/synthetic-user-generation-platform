"""
API client — the ONLY file that needs to know whether we're using mock data
or your real backend. Every page/component calls functions from here.

TO GO LIVE:
  1. In config.py set USE_MOCK_DATA = False and BACKEND_BASE_URL to your server.
  2. Make sure your backend exposes the endpoints listed below (paths match the
     spec doc: POST /api/personas/generate, POST /api/survey/run, etc).
  3. Nothing else changes — pages import these same function names.
"""

import json
import requests
import streamlit as st
from config import USE_MOCK_DATA, BACKEND_BASE_URL, API_TIMEOUT_SECONDS, GROQ_API_KEY, GROQ_MODEL
from services import mock_data

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _post(path: str, payload: dict) -> dict:
    url = f"{BACKEND_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=API_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Backend request failed ({url}): {e}")
        return {}


def _get(path: str) -> dict:
    url = f"{BACKEND_BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=API_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Backend request failed ({url}): {e}")
        return {}


# ── Experiments ───────────────────────────────────────────────────────────────

def create_experiment(product_name, description, target_audience, objectives) -> dict:
    experiment = {
        "id": f"exp_{abs(hash(product_name)) % 100000}",
        "product_name": product_name,
        "description": description,
        "target_audience": target_audience,
        "objectives": objectives,
        "status": "draft",
    }
    if USE_MOCK_DATA:
        return experiment
    return _post("/experiments", {
        "title": product_name,
        "product_description": description,
        "target_audience": target_audience,
        "research_objectives": objectives,
        "persona_count": 5
    })


# ── Personas ──────────────────────────────────────────────────────────────────

def generate_personas(experiment_id, count) -> list[dict]:
    if USE_MOCK_DATA:
        return mock_data.generate_personas("", "", "", "", count)
    result = _post("/personas/generate", {
        "experiment_id": experiment_id,
        "persona_count": count,
        "regenerate": False
    })
    return result.get("items", [])


# ── Survey ────────────────────────────────────────────────────────────────────

def create_survey(experiment_id, title, questions) -> dict:
    if USE_MOCK_DATA:
        return {"id": f"survey_{abs(hash(title)) % 100000}", "title": title, "questions": questions}
    return _post("/surveys", {
        "experiment_id": experiment_id,
        "title": title,
        "questions": questions
    })


def execute_survey(survey_id) -> dict:
    if USE_MOCK_DATA:
        return {"survey_id": survey_id, "persona_responses": []}
    return _post("/surveys/execute", {
        "survey_id": survey_id,
        "regenerate": False
    })


def get_survey_responses(survey_id) -> dict:
    if USE_MOCK_DATA:
        return {"survey_id": survey_id, "persona_responses": []}
    return _get(f"/surveys/{survey_id}/responses")


def run_survey_question(personas: list[dict], question: str) -> dict:
    # Legacy function for backward compatibility
    if USE_MOCK_DATA:
        return mock_data.run_survey_question(personas, question)
    # This would need to be implemented via the new survey endpoints
    return mock_data.run_survey_question(personas, question)


# ── Interview ─────────────────────────────────────────────────────────────────

def _call_groq(messages: list[dict], max_tokens: int = 220) -> str:
    """Direct call to Groq's OpenAI-compatible chat completions endpoint.

    Used for interview responses so personas feel like a real (simulated)
    person reacting to the actual question, instead of a canned line.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.8,
    }
    try:
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=API_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.RequestException as e:
        st.error(f"Groq request failed: {e}")
        return ""
    except (KeyError, IndexError):
        st.error("Unexpected response format from Groq.")
        return ""


def _persona_system_prompt(persona: dict) -> str:
    experiment = st.session_state.get("experiment") or {}
    return (
        f"You are role-playing as {persona['name']}, a {persona['age']}-year-old "
        f"{persona['occupation']}. Personality traits: {', '.join(persona.get('tags', []))}. "
        f"Background: {persona.get('bio', '')} "
        f"You are being interviewed as a potential user of a product called "
        f"\"{experiment.get('product_name', 'this product')}\": "
        f"{experiment.get('description', 'No description provided.')} "
        f"Target audience it's built for: {experiment.get('target_audience', 'not specified')}. "
        "Answer the interviewer's questions fully in character, in first person. "
        "Keep answers conversational and concise (2-4 sentences), grounded in your "
        "persona's life, priorities, and personality — not generic marketing-speak. "
        "Give honest, specific opinions: if skeptical, say so and why; if enthusiastic, "
        "say so and why. Directly address what was actually asked. Never break character "
        "or mention that you are an AI."
    )


def get_persona_response(persona: dict, message: str, history: list[dict]) -> str:
    if GROQ_API_KEY:
        messages = [{"role": "system", "content": _persona_system_prompt(persona)}]
        # history already includes the just-sent user message as its last entry
        for turn in history[-10:]:
            role = "assistant" if turn["role"] == "assistant" else "user"
            messages.append({"role": role, "content": turn["content"]})
        reply = _call_groq(messages)
        if reply:
            return reply
        # fall through to mock on any failure so the UI never shows a blank response
    if USE_MOCK_DATA:
        return mock_data.get_persona_response(persona, message, history)
    result = _post("/interview/message", {
        "persona_id": persona["id"],
        "message": message,
        "history": history,
    })
    return result.get("response", "")


# ── Insights ──────────────────────────────────────────────────────────────────

def _build_feedback_transcript(personas: list[dict], survey_responses: dict, chat_history: dict) -> str:
    """Flattens actual survey comments + interview replies into one text block
    so the "what users want" analysis is grounded in real feedback, not guesses."""
    id_to_name = {p["id"]: p["name"] for p in personas}
    lines = []
    for q_idx, responses in (survey_responses or {}).items():
        for pid, r in (responses or {}).items():
            name = id_to_name.get(pid, pid)
            lines.append(f"[Survey] {name} (score {r.get('score')}): {r.get('comment')}")
    for pid, turns in (chat_history or {}).items():
        name = id_to_name.get(pid, pid)
        for turn in turns or []:
            if turn.get("role") == "user":
                continue
            lines.append(f"[Interview] {name}: {turn.get('content', '')}")
    return "\n".join(lines)[:6000]


def _extract_suggestions_via_groq(personas: list[dict], survey_responses: dict, chat_history: dict):
    """Asks Groq to read the real feedback transcript and return a grounded summary
    of what users want plus concrete, prioritized suggestions. Returns None on any
    failure so callers can fall back cleanly to the mock/heuristic version."""
    transcript = _build_feedback_transcript(personas, survey_responses, chat_history)
    if not transcript.strip():
        return None

    system_prompt = (
        "You are a product research analyst reviewing raw feedback from simulated "
        "user interviews and surveys. Respond with ONLY a JSON object — no markdown, "
        "no code fences, no commentary before or after — in exactly this shape:\n"
        '{"user_wants_summary": "2-3 plain-English sentences summarizing what users '
        'want overall", "suggestions": [{"suggestion": "specific actionable improvement", '
        '"category": "short label like Pricing, Feature, UX, Trust, Support, Performance, Design", '
        '"priority": "high|medium|low", "personas": ["names who raised it"]}]}\n'
        "Base every suggestion strictly on what the transcript actually says — do not "
        "invent feedback. Return 4 to 6 suggestions, most important first."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Feedback transcript:\n{transcript}"},
    ]
    raw = _call_groq(messages, max_tokens=700)
    if not raw:
        return None

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned.split("\n", 1)[-1]
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and isinstance(data.get("suggestions"), list):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def extract_insights(personas: list[dict], survey_responses: dict, chat_history: dict) -> dict:
    if USE_MOCK_DATA:
        insights = mock_data.extract_insights(personas, survey_responses, chat_history)
    else:
        insights = _post("/insights/extract", {
            "persona_ids": [p["id"] for p in personas],
            "survey_responses": survey_responses,
            "chat_history": chat_history,
        }) or {}

    # When a Groq key is configured and there's real conversation/survey content,
    # ground the "what users want" section in that actual feedback instead of the
    # generic mock/backend version.
    if GROQ_API_KEY and (chat_history or survey_responses):
        grounded = _extract_suggestions_via_groq(personas, survey_responses, chat_history)
        if grounded:
            insights["user_wants_summary"] = grounded.get(
                "user_wants_summary", insights.get("user_wants_summary", "")
            )
            insights["suggestions"] = grounded.get("suggestions", insights.get("suggestions", []))

    insights.setdefault("suggestions", [])
    insights.setdefault("user_wants_summary", "")
    return insights


# ── Reports ───────────────────────────────────────────────────────────────────

def generate_report(experiment: dict, personas: list[dict], insights: dict) -> dict:
    if USE_MOCK_DATA:
        return {
            "experiment": experiment,
            "personas": personas,
            "insights": insights,
        }
    return _post("/reports/generate", {
        "experiment": experiment,
        "personas": personas,
        "insights": insights,
    })
