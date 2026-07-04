"""
Central configuration for the Synthetic User Generation Platform frontend.

IMPORTANT — SWAPPING FROM MOCK DATA TO YOUR REAL BACKEND:
1. Set USE_MOCK_DATA = False below.
2. Set BACKEND_BASE_URL to your real backend (e.g. Spring Boot / FastAPI / Flask server).
3. Set GROQ_API_KEY (only needed if this frontend calls Groq directly instead of
   going through your backend — most setups will have the backend call Groq).
Everything else in the app calls services/api_client.py, which already branches
on USE_MOCK_DATA, so no other files need to change.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Mode toggle ──────────────────────────────────────────────────────────────
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# ── Backend ──────────────────────────────────────────────────────────────────
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000/api")
API_TIMEOUT_SECONDS = 30

# ── Groq (only used if frontend calls the LLM directly; optional) ───────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── App metadata ─────────────────────────────────────────────────────────────
APP_NAME = "Synthetic User Generation Platform"
APP_ICON = "🚀"
APP_TAGLINE = "Validate products without real users"

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_PERSONA_COUNT = 5
MIN_PERSONA_COUNT = 3
MAX_PERSONA_COUNT = 12
