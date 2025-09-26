import json
from agents import hydration_supplement
from tools.singapore_weather import singapore_weather
from tools.singapore_time import singapore_time
from agents import nutritionist as nutrition_agent

def test_hydration():
    print("=== Current Time ===")
    print(singapore_time())

    print("\n=== Weather Forecast (5 days) ===")
    print(singapore_weather(5))

    user = hydration_supplement.UserProfile(
        name="Test User",
        body_mass_kg=70,
        vitamin_d_deficient_or_low_sun=True
    )
    climate = hydration_supplement.Climate(avg_temp_c=30, avg_humidity_pct=70)

    week_pattern = [
        hydration_supplement.Workout(day_of_week="Mon", minutes=45, intensity="moderate"),
        hydration_supplement.Workout(day_of_week="Wed", minutes=30, intensity="vigorous"),
        hydration_supplement.Workout(day_of_week="Sat", minutes=60, intensity="moderate", is_outdoor=False),
    ]
    workouts_by_week = [week_pattern[:] for _ in range(4)]

    agent = hydration_supplement.HydrationSupplementAgent(user, climate, workouts_by_week)
    result = agent.generate()

    print("\n=== Hydration & Supplement Agent Output ===")
    print(json.dumps(result, indent=2))
def test_nutritionist():
    """
    Minimal smoke test for Agent 2 (Nutritionist).
    Builds a simple user profile, generates a plan, and prints a concise preview.
    """
    user = nutrition_agent.UserProfile(
        name="Test User",
        sex="male",
        age=28,
        height_cm=175,
        weight_kg=75,
        workouts_per_week=3,
        activity_level=None,
        diet_prefs="omnivore",
        allergies=None,
        goal="lose 10 lb",
    )

    plan = nutrition_agent.plan_for_4_weeks(user)

    print("\n=== Nutritionist Agent Output (preview) ===")
    print(plan.summary)

    t = plan.targets
    print("\n[Targets]")
    print(f" - Calories: {t.kcal_rest} (rest) / {t.kcal_workout} (workout)")
    print(f" - Macros: protein {t.protein_g} g, fat {t.fat_g} g, "
          f"carbs {t.carbs_rest_g}/{t.carbs_workout_g} g (rest/workout)")
    print(f" - Fiber: {t.fiber_g_range[0]}–{t.fiber_g_range[1]} g/day")

    d1 = plan.rotation_days[0]
    print("\n[Day 1]")
    print(f" - Workout day: {'Yes' if d1.is_workout_day else 'No'}")
    print(f" - Kcal target: {d1.kcal_target}")
    for m in d1.meals:
        print(f"   • {m.name.capitalize()}: {m.option}")

    print("\n[Grocery list — first 8]")
    for g in plan.grocery_list[:8]:
        print(f" - {g.name}: {g.qty}")


if __name__ == "__main__":
    test_hydration()
    test_nutritionist()
