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
from config import USE_MOCK_DATA, BACKEND_BASE_URL, API_TIMEOUT_SECONDS
from services import mock_data


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

def get_persona_response(persona: dict, message: str, history: list[dict]) -> str:
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
