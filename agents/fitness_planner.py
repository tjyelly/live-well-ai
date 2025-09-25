# fitness_planner.py

from typing import TypedDict, Dict
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads .env at project root
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
     raise RuntimeError("OPENAI_API_KEY is not set. Put it in a .env or export it in your shell.")
_client = OpenAI(api_key=_api_key)

_SYSTEM = (
    "You are a certified fitness coach. Create safe, practical workout plans for adults. "
    "Balance cardio and strength, include warm-up and cool-down, and respect user constraints."
)

# Single, clear prompt asking for a 2-week plan in readable text (not JSON)
def _build_user_prompt(user_goal: str) -> str:
    return (
        "User goal & constraints:\n"
        f"{user_goal.strip()}\n\n"
        "Please produce a **2-week fitness plan** following these rules:\n"
        "1) 3–5 sessions per week as appropriate for the goal and fitness level.\n"
        "2) Include warm-up and cool-down for each session.\n"
        "3) Mix cardio and strength; suggest sets×reps or time.\n"
        "4) Respect stated constraints (e.g., injuries, dietary restrictions for brief notes).\n"
        "5) Output as plain text with the following sections:\n"
        "   - Overview (2–3 lines)\n"
        "   - Week 1 (Day-by-day bullets)\n"
        "   - Week 2 (Day-by-day bullets)\n"
        "   - Progression & Safety (bullets)\n"
        "   - Optional Tips (bullets)\n"
    )

def fitness_planner(state) -> Dict[str, str]:
    """Reads state['user_goal'] and returns a plain-text 2-week fitness plan."""
    goal = (state.get("user_goal") or "").strip()
    if not goal:
        return {"fitness_plan": "Please provide your goal and constraints in 'user_goal'."}

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": _build_user_prompt(goal)},
    ]

    # Prefer the modern Responses API; fall back if needed.
    try:
        resp = _client.responses.create(model="gpt-4o-mini", messages=messages, temperature=0.6)
        plan_text = resp.output_text.strip()
    except Exception:
        # Fallback to chat.completions if your environment uses the older API
        chat = _client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.6)
        plan_text = chat.choices[0].message.content.strip()

    return {"fitness_plan": plan_text}
