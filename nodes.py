from typing import Literal
from state import State

from agents.fitness_planner import fitness_planner as fitness_planner
#from agents.nutritionist import nutritionist as nutritionist_node
#from agents.hydration_supplement import hydration_supplement_node as hydration_supplement_node
from agents.summarizer import summarizer as summarizer


def human_node(state: State) -> dict:
    """
    Fitness Planner node - gets user input and plans workout routine.
    """
    user_input = input("\nYou: ").strip()

    return {
        "user_goal": user_input,
        "nutrition_plan": '',
        "fitness_plan": '',
        "supplements": ''
    }

def fitness_planner_node(state: State) -> dict:
    """
    Fitness Planner node - gets user input and plans workout routine.
    """
    result = fitness_planner(state)

    # Print and return messages
    if result:
        print(result)

        return {"fitness_plan": result}

    return {}


def summarizer_node(state: State) -> dict:
    """
    Summarizer node - generates and displays conversation summary.
    """
    print("\n=== CONVERSATION ENDING ===\n")

    # Generate and print summary
    summary = summarizer(state, detailed=True)
    print(summary)
    print("\nThank you! Live Well AI is rooting for you!")

    return {}

__all__ = [
    "human_node",
    "fitness_planner_node",
    "summarizer_node"
]