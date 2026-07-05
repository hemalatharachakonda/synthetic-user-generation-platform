"""
Mock data generator.

This simulates what your real backend (calling Groq) will eventually return.
Every function here mirrors an endpoint in api_client.py's REAL_MODE branch,
so when USE_MOCK_DATA=False, api_client.py calls your backend instead of these
functions, and every page above it keeps working unchanged.
"""

import random
import uuid
from utils.constants import PERSONALITY_TAG_POOL, OCCUPATIONS_POOL

FIRST_NAMES = ["Sarah", "Mike", "Priya", "David", "Emma", "Raj", "Lucia",
               "Tom", "Aisha", "Noah", "Wei", "Fatima"]

SAMPLE_QUOTES_POSITIVE = [
    "This would save me hours every week!",
    "Exactly what my team has been missing.",
    "I'd recommend this to my colleagues immediately.",
    "The onboarding felt effortless.",
]
SAMPLE_QUOTES_NEUTRAL = [
    "It's fine, but I'm not sure it beats what I already use.",
    "I'd need to try it longer before deciding.",
]
SAMPLE_QUOTES_NEGATIVE = [
    "Too complex for daily use.",
    "The pricing feels steep for what it offers.",
    "I ran into a few confusing steps early on.",
]

THEMES_POOL = ["Privacy", "Speed", "Pricing", "Mobile Experience",
               "Onboarding", "Integrations", "Customer Support", "Design"]


def _random_avatar_seed():
    return random.randint(1, 9999)


def generate_personas(product_name: str, description: str,
                       target_audience: str, objectives: str, count: int) -> list[dict]:
    """Mocks POST /api/personas/generate"""
    personas = []
    used_names = random.sample(FIRST_NAMES, min(count, len(FIRST_NAMES)))
    for i in range(count):
        name = used_names[i] if i < len(used_names) else f"Persona {i+1}"
        age = random.randint(22, 55)
        occupation = random.choice(OCCUPATIONS_POOL)
        tags = random.sample(PERSONALITY_TAG_POOL, k=3)
        adoption_score = round(random.uniform(3.0, 9.5), 1)
        personas.append({
            "id": f"p_{uuid.uuid4().hex[:8]}",
            "name": name,
            "age": age,
            "occupation": occupation,
            "tags": tags,
            "adoption_score": adoption_score,
            "avatar_seed": _random_avatar_seed(),
            "bio": (
                f"{name} is a {age}-year-old {occupation.lower()} who fits the "
                f"target profile: {target_audience.strip()[:120]}."
            ),
        })
    return personas


def run_survey_question(personas: list[dict], question: str) -> dict:
    """Mocks POST /api/survey/run for a single question. Returns {persona_id: {score, comment}}"""
    results = {}
    for p in personas:
        score = max(1, min(10, round(random.gauss(p["adoption_score"], 1.5))))
        if score >= 7:
            comment = random.choice(SAMPLE_QUOTES_POSITIVE)
        elif score >= 4:
            comment = random.choice(SAMPLE_QUOTES_NEUTRAL)
        else:
            comment = random.choice(SAMPLE_QUOTES_NEGATIVE)
        results[p["id"]] = {"score": score, "comment": comment}
    return results


def get_persona_response(persona: dict, message: str, history: list[dict]) -> str:
    """Mocks POST /api/interview/message — a persona's conversational reply."""
    canned = [
        f"As someone balancing a lot day-to-day, I'd want this to save me time, not add steps.",
        f"Honestly, price matters to me — I'd expect something in the $10-15/month range.",
        f"I like the idea, but I'd need to see how it fits with tools I already use.",
        f"That's a good question. My biggest concern would be data privacy.",
        f"If it worked smoothly on mobile, I'd probably use it daily.",
    ]
    return random.choice(canned)


def extract_insights(personas: list[dict], survey_responses: dict, chat_history: dict) -> dict:
    """Mocks POST /api/insights/extract"""
    all_scores = [p["adoption_score"] for p in personas] or [0]
    would_use_pct = round((sum(1 for s in all_scores if s >= 6) / len(all_scores)) * 100)
    would_pay_pct = max(0, would_use_pct - random.randint(5, 15))

    themes = random.sample(THEMES_POOL, k=4)
    theme_data = [{"theme": t, "mentions_pct": random.randint(20, 50)} for t in themes]
    theme_data.sort(key=lambda x: x["mentions_pct"], reverse=True)

    pos = random.randint(35, 55)
    neg = random.randint(15, 30)
    neu = max(0, 100 - pos - neg)

    quotes = [
        {"quote": random.choice(SAMPLE_QUOTES_POSITIVE), "persona": random.choice(personas)["name"] if personas else "N/A"},
        {"quote": random.choice(SAMPLE_QUOTES_NEGATIVE), "persona": random.choice(personas)["name"] if personas else "N/A"},
    ]

    return {
        "would_use_pct": would_use_pct,
        "would_pay_pct": would_pay_pct,
        "themes": theme_data,
        "sentiment": {"Positive": pos, "Neutral": neu, "Negative": neg},
        "key_quotes": quotes,
    }
