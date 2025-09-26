import traceback
import logging

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from state import State
from nodes import (
    human_node,
    fitness_planner_node,
    nutritionist_node,
    hydration_supplement_node,
    summarizer_node
)

load_dotenv(override=True)  # Override, so it would use your local .env file


def build_graph():
    """
    Build the LangGraph workflow.
    """

    builder = StateGraph(State)

    builder.add_node("human", human_node)
    builder.add_node("fitness_planner", fitness_planner_node)   # use underscore consistently
    builder.add_node("nutritionist", nutritionist_node)
    builder.add_node("hydration", hydration_supplement_node)    # keep this name consistent
    builder.add_node("summarizer", summarizer_node)

    # Edges
    builder.add_edge(START, "human")
    builder.add_edge("human", "fitness_planner")
    builder.add_edge("fitness_planner", "nutritionist")
    builder.add_edge("nutritionist", "hydration")
    builder.add_edge("hydration", "summarizer")
    builder.add_edge("summarizer", END)

    return builder.compile()


def main():
    print("=== LIVE WELL AI ===")
    print("Get started with your wellness journey today!\n")
    print("Let us know your goals and we will tackle them together!\n")
    print("Type 'exit' to end.\n")

    graph = build_graph()

    print(graph.get_graph().draw_ascii())

    initial_state = State(
        user_goal='',
        fitness_plan='',
        nutrition_plan='',
        hydration_supplement=''
    )

    try:
        graph.invoke(initial_state)
    except KeyboardInterrupt:
        print("\n\nConversation interrupted. Goodbye!")
    except Exception as e:
        print("\n=== ERROR ===")
        print(f"Type     : {e.__class__.__name__}")
        print(f"Message  : {e}")
        print(f"Args     : {e.args}")
        print("Traceback:")
        print(traceback.format_exc())  # full stack with lines
        print("Ending conversation...")


if __name__ == "__main__":
    main()
