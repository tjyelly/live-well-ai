# agents/nutritionist.py
from typing import Dict

def nutritionist(state) -> Dict[str, str]:
    """
    Simple Nutritionist agent function.
    Always returns a dict with 'nutrition_plan'.
    """
    user_goal = (state.get("user_goal") or "").strip()
    user_context = (state.get("user_context") or "").strip()

    if not user_goal and not user_context:
        return {"nutrition_plan": "Please provide your nutrition goal in 'user_goal'."}

    # For now just return a stub text plan (you can later add OpenAI API calls here).
    plan_text = (
        f"Nutrition Plan based on your goal: {user_goal}\n\n"
        "- Eat balanced meals with protein, carbs, and healthy fats.\n"
        "- Drink enough water daily.\n"
        "- Include fruits and vegetables.\n"
        "- Adjust calories to match your goal.\n"
        "- Prep in advance to stay consistent."
    )

    return {"nutrition_plan": plan_text}


__all__ = ["nutritionist"]
