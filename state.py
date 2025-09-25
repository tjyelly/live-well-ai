from typing import TypedDict, Optional


class State(TypedDict):
    """
    Overall state of the entire LangGraph system.
    """
    user_goal: str
    nutrition_plan: str
    fitness_plan: str
    supplements: str