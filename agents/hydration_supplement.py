# hydration_supplement.py

from typing import Dict
import os
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------
# Setup
# -----------------------------
load_dotenv()  # reads .env at project root
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Put it in a .env or export it in your shell.")
_client = OpenAI(api_key=_api_key)

# -----------------------------
# System prompt
# -----------------------------
_SYSTEM = (
    "You are a sports nutritionist and hydration specialist. "
    "Create safe, practical hydration and supplement guidance for adults. "
    "Always consider workout intensity, climate, and health constraints. "
    "Be precise but easy to follow."
)

# -----------------------------
# Prompt builder
# -----------------------------
def _build_user_prompt(user_context: str) -> str:
    return (
        "User profile, climate, and workouts:\n"
        f"{user_context.strip()}\n\n"
        "Please produce a **4-week hydration & supplement plan** following these rules:\n"
        "1) Give daily baseline water intake in ml (based on body weight).\n"
        "2) For workouts: pre, during, post hydration rules (with sodium if needed).\n"
        "3) Consider heat, humidity, and altitude in recommendations.\n"
        "4) Add supplement cheatsheet (protein, creatine, vitamin D, etc.) "
        "with notes on when to avoid.\n"
        "5) Output as plain text with the following sections:\n"
        "   - Overview (2–3 lines)\n"
        "   - Baseline Hydration (per day)\n"
        "   - Weekly Workout Hydration (week-by-week, day-by-day bullets)\n"
        "   - Supplement Cheatsheet (bullets)\n"
        "   - Safety & Special Notes (bullets)\n"
    )

# -----------------------------
# Public API
# -----------------------------
def hydration_supplement(state) -> Dict[str, str]:
    """Reads state['user_context'] and returns a plain-text 4-week hydration & supplement plan."""
    ctx = (state.get("user_context") or state.get("user_goal") or "").strip()
    if not ctx:
        return {"hydration_supplement": "Please provide your profile, climate, and workouts in 'user_context'."}

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": _build_user_prompt(ctx)},
    ]

    try:
        resp = _client.responses.create(model="gpt-4o-mini", messages=messages, temperature=0.6)
        plan_text = resp.output_text.strip()
    except Exception:
        chat = _client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.6)
        plan_text = chat.choices[0].message.content.strip()

    return {"hydration_supplement": plan_text}
