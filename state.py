from typing import TypedDict, Optional


class State(TypedDict):
    """
    Overall state of the entire LangGraph system.
    """
    user_goal: str
    user_context: str
    nutrition_plan: str
    fitness_plan: str
    hydration_supplement: str