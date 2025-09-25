import json
from agents import hydration_supplement
from tools.weather import singapore_weather
from tools.singapore_time import singapore_time


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


if __name__ == "__main__":
    test_hydration()
