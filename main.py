from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from state import State
from nodes import (
    human_node,
    fitness_planner_node,
    summarizer_node
)


load_dotenv(override=True)  # Override, so it would use your local .env file


def build_graph():
    """
    Build the LangGraph workflow.
    """

    builder = StateGraph(State)

    builder.add_node("human", human_node)
    builder.add_node("fitness planner", fitness_planner_node)
    # builder.add_node("nutritionist", nutritionist)
    # builder.add_node("hydration", hydration_supplement)
    # builder.add_node("summarizer", summarizer)

    # Edges
    builder.add_edge(START, "human")

    builder.add_edge("human", "fitness planner")
    # builder.add_edge("fitness planner", "nutritionist")
    # builder.add_edge("nutritionist", "hydration")
    # builder.add_edge("hydration", "summarizer")
    #
    # builder.add_edge("summarizer", END)
    builder.add_edge("fitness planner", END)

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
        nutrition_plan='',
        fitness_plan='',
        supplements=''
    )

    try:
        graph.invoke(initial_state)
    except KeyboardInterrupt:
        print("\n\nConversation interrupted. Goodbye!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Ending conversation...")


if __name__ == "__main__":
    main()
