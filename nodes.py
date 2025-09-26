from state import State
from agents.fitness_planner import fitness_planner
from agents.nutritionist import nutritionist
from agents.hydration_supplement import hydration_supplement
from agents.summarizer import summarizer


def human_node(state: State) -> dict:
    """
    Human input node - collects user goal and resets downstream fields.
    """
    user_input = input("\nYou: ").strip()

    return {
        "user_goal": user_input,
        "fitness_plan": "",
        "nutrition_plan": "",
        "hydration_supplement": ""
    }


def fitness_planner_node(state: State) -> dict:
    """
    Fitness Planner node - generates a workout plan.
    """
    result = fitness_planner(state)

    if result:
        print("\n=== FITNESS PLAN ===\n")
        print(result)
        return {
            "fitness_plan": result,
            "user_context": state.get("user_goal", "")
        }

    return {}


def nutritionist_node(state: State) -> dict:
    """
    Nutritionist node - generates a 7-day nutrition plan.
    """
    result = nutritionist(state)
    plan_text = (result or {}).get("nutrition_plan", "").strip()

    if plan_text:
        print("\n=== NUTRITION PLAN ===\n")
        print(plan_text)
        return {"nutrition_plan": plan_text}

    return {}


def hydration_supplement_node(state: State) -> dict:
    """
    Hydration & Supplement node - generates hydration and supplement plan.
    """
    result = hydration_supplement(state)

    if result:
        print("\n=== HYDRATION & SUPPLEMENT PLAN ===\n")
        print(result)
        return {"hydration_supplement": result}

    return {}


def summarizer_node(state: State) -> dict:
    """
    Summarizer node - generates and displays conversation summary.
    """
    print("\n=== CONVERSATION ENDING ===\n")

    summary = summarizer(state, detailed=True)
    print(summary)
    print("\nThank you! Live Well AI is rooting for you!")

    return {}


__all__ = [
    "human_node",
    "fitness_planner_node",
    "nutritionist_node",
    "hydration_supplement_node",
    "summarizer_node",
]
