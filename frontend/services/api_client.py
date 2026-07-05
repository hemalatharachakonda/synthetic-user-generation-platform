"""
API client — the ONLY file that needs to know whether we're using mock data
or your real backend. Every page/component calls functions from here.

TO GO LIVE:
  1. In config.py set USE_MOCK_DATA = False and BACKEND_BASE_URL to your server.
  2. Make sure your backend exposes the endpoints listed below (paths match the
     spec doc: POST /api/personas/generate, POST /api/survey/run, etc).
  3. Nothing else changes — pages import these same function names.
"""

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
    return _post("/experiments", experiment)


# ── Personas ──────────────────────────────────────────────────────────────────

def generate_personas(product_name, description, target_audience, objectives, count) -> list[dict]:
    if USE_MOCK_DATA:
        return mock_data.generate_personas(product_name, description, target_audience, objectives, count)
    result = _post("/personas/generate", {
        "product_name": product_name,
        "description": description,
        "target_audience": target_audience,
        "objectives": objectives,
        "count": count,
    })
    return result.get("personas", [])


# ── Survey ────────────────────────────────────────────────────────────────────

def run_survey_question(personas: list[dict], question: str) -> dict:
    if USE_MOCK_DATA:
        return mock_data.run_survey_question(personas, question)
    result = _post("/survey/run", {
        "persona_ids": [p["id"] for p in personas],
        "question": question,
    })
    return result.get("responses", {})


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

def extract_insights(personas: list[dict], survey_responses: dict, chat_history: dict) -> dict:
    if USE_MOCK_DATA:
        return mock_data.extract_insights(personas, survey_responses, chat_history)
    result = _post("/insights/extract", {
        "persona_ids": [p["id"] for p in personas],
        "survey_responses": survey_responses,
        "chat_history": chat_history,
    })
    return result


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
