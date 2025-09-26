# agents/nutritionist.py
from typing import Dict
import os
from dotenv import load_dotenv

# OpenAI SDK v1.x
from openai import OpenAI

load_dotenv()  # loads OPENAI_API_KEY from .env at project root

_SYSTEM = (
    "You are a registered dietitian. Create safe, practical nutrition plans for adults. "
    "Factor in goals (lose/maintain/gain), dietary constraints, allergies, and prep time. "
    "Keep advice general (not medical), actionable, and supermarket-friendly."
)

def _build_user_prompt(user_goal: str, user_context: str) -> str:
    goal = (user_goal or "").strip()
    ctx  = (user_context or "").strip()
    return (
        "User goal & constraints (nutrition):\n"
        f"{goal}\n\n"
        "Extra context (if any):\n"
        f"{ctx}\n\n"
        "Please produce a 14-day nutrition plan with:\n"
        "1) Daily calorie target + macro targets (protein, fat, carbs) and brief rationale.\n"
        "2) Simple meal outline per day (Breakfast / Lunch / Dinner; add Snack if relevant) with 1–2 swaps.\n"
        "3) Respect restrictions/allergies.\n"
        "4) End with: Grocery List (grouped), Prep & Batch Tips (bullets), Safety Notes (bullets).\n"
    )

def nutritionist(state) -> Dict[str, str]:
    """
    LLM-backed Nutritionist agent.
    Expects state['user_goal'] (and optional state['user_context']).
    Returns {'nutrition_plan': '<plan text>'}.
    """
    user_goal = (state.get("user_goal") or "").strip()
    user_context = (state.get("user_context") or "").strip()

    if not user_goal and not user_context:
        return {"nutrition_plan": "Please provide your nutrition goal in 'user_goal' (and optional 'user_context')."}

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"nutrition_plan": "OPENAI_API_KEY is missing. Add it to your .env at the project root."}

    client = OpenAI(api_key=api_key)

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": _build_user_prompt(user_goal, user_context)},
    ]

    # Prefer modern Responses API; gracefully fall back to Chat Completions if needed.
    try:
        resp = client.responses.create(model="gpt-4o-mini", messages=messages, temperature=0.6)
        plan_text = resp.output_text.strip()
    except Exception:
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.6)
        plan_text = chat.choices[0].message.content.strip()

    return {"nutrition_plan": plan_text}

__all__ = ["nutritionist"]
