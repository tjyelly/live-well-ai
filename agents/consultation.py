import json
from agents.hydration_supplement import (
    HydrationSupplementAgent,
    UserProfile,
    Climate,
    Workout,
)
from agents.summarizer import summarizer


def run_consultation(user_input: str):
    """
    Orchestrates fitness, nutrition, hydration/supplement agents and
    generates a final summarized action plan.
    """

    # -------------------------------
    # 1. Capture user goals
    # -------------------------------
    state = {
        "messages": [],
        "user_goals": {"goal": user_input}
    }

    # -------------------------------
    # 2. Fitness Planner Agent (stubbed rule-based)
    # -------------------------------
    fitness_plan = {
        "week1": ["3x cardio (30–40 min)", "2x strength training"],
        "week2": ["Cardio 45 min", "2x strength training"]
    }
    state["fitness_plan"] = fitness_plan
    state["messages"].append({
        "role": "assistant",
        "name": "Fitness Planner",
        "content": f"Generated fitness plan: {fitness_plan}"
    })

    # -------------------------------
    # 3. Nutritionist Agent (stubbed rule-based)
    # -------------------------------
    nutrition_plan = {
        "calories_per_day": 1500,
        "macros": {"protein": "35%", "carbs": "40%", "fats": "25%"},
        "meals": [
            "Breakfast: Oats with berries",
            "Lunch: Grilled chicken salad",
            "Dinner: Steamed fish with veggies"
        ]
    }
    state["nutrition_plan"] = nutrition_plan
    state["messages"].append({
        "role": "assistant",
        "name": "Nutritionist",
        "content": f"Generated nutrition plan: {nutrition_plan}"
    })

    # -------------------------------
    # 4. Hydration & Supplement Agent
    # -------------------------------
    user = UserProfile(
        name="Client",
        body_mass_kg=70,
        vitamin_d_deficient_or_low_sun=True
    )
    climate = Climate(avg_temp_c=30, avg_humidity_pct=70)

    # Workouts aligned with fitness plan
    week_pattern = [
        Workout(day_of_week="Mon", minutes=45, intensity="moderate"),
        Workout(day_of_week="Wed", minutes=30, intensity="vigorous"),
        Workout(day_of_week="Sat", minutes=60, intensity="moderate")
    ]
    workouts_by_week = [week_pattern[:] for _ in range(2)]  # 2 weeks

    hydration_agent = HydrationSupplementAgent(user, climate, workouts_by_week)
    supplements = hydration_agent.generate()

    state["supplements"] = supplements
    state["messages"].append({
        "role": "assistant",
        "name": "Hydration Coach",
        "content": f"Generated hydration & supplements: {json.dumps(supplements, indent=2)}"
    })

    # -------------------------------
    # 5. Final Summarization (LLM)
    # -------------------------------
    action_plan = summarizer(state, detailed=True)
    print(action_plan)


if __name__ == "__main__":
    # Example user prompt
    run_consultation("I want to reduce 5kg in 2 weeks")
