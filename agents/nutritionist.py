# agents/nutritionist.py
"""
Nutritionist Agent
------------------
Calculates daily calorie & macronutrient targets and produces an easy, prep-friendly
7-day rotating meal plan plus a compact grocery list. Designed to integrate with a
multi-agent system (e.g., your coordinator and summarizer).

Public entrypoints:
- plan_for_4_weeks(user: UserProfile, prefs: NutritionPrefs | None) -> NutritionPlan
- quick_plan_for_prompt(...) -> NutritionPlan  # convenience for free-text prompts

Notes
-----
- Uses simple, transparent calculations with reasonable defaults when stats are missing.
- Exposes both rest-day and workout-day calorie bands.
- Macro policy: Protein 1.6–2.2 g/kg (default 1.8), Fat ≥ 0.6 g/kg (default 0.8), carbs fill remainder.
- Deficit: ~500 kcal/day by default; can be tuned via prefs.

Safety
------
This is not medical advice. Users with medical conditions, pregnancy, or on medication
should consult a qualified clinician before changing diet or supplements.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple
import math
import json

# -----------------------------
# Data Models
# -----------------------------

@dataclass
class UserProfile:
    # Minimal shared contract across agents.
    # Provide as many as available; sensible defaults are applied if missing.
    name: Optional[str] = None
    sex: Optional[str] = None            # "male" | "female" | None (affects BMR choice)
    age: Optional[int] = None            # years
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None # "sedentary"|"light"|"moderate"|"active"|"very_active"
    workouts_per_week: int = 3
    goal: str = "lose weight"
    diet_prefs: Optional[str] = None     # e.g., "omnivore", "vegetarian", "vegan", "halal"
    allergies: Optional[List[str]] = None
    equipment: Optional[str] = None      # not used here but part of global contract

@dataclass
class NutritionPrefs:
    target_daily_deficit_kcal: int = 500
    protein_g_per_kg: float = 1.8
    fat_g_per_kg: float = 0.8
    # Carb grams filled after protein/fat
    workout_day_bonus_kcal: int = 200    # additional fuel on training days
    min_fiber_g: int = 25
    max_fiber_g: int = 35
    # Safety rails
    min_kcal_floor: int = 1200           # do not plan below this
    explain_calculations: bool = True

@dataclass
class MacroTargets:
    kcal_rest: int
    kcal_workout: int
    protein_g: int
    fat_g: int
    carbs_rest_g: int
    carbs_workout_g: int
    fiber_g_range: Tuple[int, int]

@dataclass
class Recipe:
    title: str
    ingredients: List[str]
    steps: List[str]
    est_kcal: Optional[int] = None
    macros_g: Optional[Dict[str, int]] = None  # {"protein":..., "carbs":..., "fat":...}

@dataclass
class Meal:
    name: str            # "breakfast" | "lunch" | "dinner" | "snack"
    option: str          # short label
    ingredients: List[str]
    est_kcal: Optional[int] = None
    notes: Optional[str] = None

@dataclass
class DayPlan:
    day_index: int                 # 1..7
    is_workout_day: bool
    kcal_target: int
    meals: List[Meal] = field(default_factory=list)

@dataclass
class GroceryItem:
    name: str
    qty: str

@dataclass
class NutritionPlan:
    summary: str
    targets: MacroTargets
    rotation_days: List[DayPlan]     # 7-day rotating plan
    grocery_list: List[GroceryItem]
    quick_recipes: List[Recipe]
    calculations: Optional[Dict[str, Any]] = None   # if explain_calculations


# -----------------------------
# Core Calculations
# -----------------------------

_ACTIVITY_FACTORS = {
    # Coarse-grained Mifflin-St Jeor activity multipliers
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

def _clamp_int(x: float, lo: int, hi: int) -> int:
    return int(max(lo, min(hi, round(x))))

def _default_weight(height_cm: Optional[float]) -> float:
    # If no weight provided, infer a neutral placeholder from height using BMI ~24.
    if height_cm and 140 <= height_cm <= 210:
        return (24.0 * (height_cm/100.0)**2)
    return 75.0  # robust default

def _mifflin_st_jeor_bmr(sex: Optional[str], weight_kg: float, height_cm: float, age: int) -> float:
    # Mifflin St Jeor (kcal/day)
    # male:   BMR = 10*W + 6.25*H - 5*A + 5
    # female: BMR = 10*W + 6.25*H - 5*A - 161
    base = 10*weight_kg + 6.25*height_cm - 5*age
    if sex and sex.lower().startswith("f"):
        return base - 161
    return base + 5

def _tdee(bmr: float, activity_level: Optional[str]) -> float:
    factor = _ACTIVITY_FACTORS.get((activity_level or "light").lower(), 1.375)
    return bmr * factor

def _macro_targets(weight_kg: float, kcal_rest: int, kcal_workout: int,
                   protein_g_per_kg: float, fat_g_per_kg: float) -> Tuple[int, int, int, int]:
    protein_g = int(round(weight_kg * protein_g_per_kg))
    fat_g = int(round(weight_kg * fat_g_per_kg))

    # kcal from protein & fat
    kcal_pf = protein_g * 4 + fat_g * 9
    carbs_rest_g = max(0, int(round((kcal_rest - kcal_pf) / 4)))
    carbs_workout_g = max(0, int(round((kcal_workout - kcal_pf) / 4)))
    return protein_g, fat_g, carbs_rest_g, carbs_workout_g


# -----------------------------
# Meal Templates (simple, swappable)
# -----------------------------

_BREAKFASTS = [
    Meal("breakfast", "Greek yogurt bowl",
         ["Greek yogurt 250 g", "mixed berries 150 g", "granola 30 g"]),
    Meal("breakfast", "Protein oats",
         ["Rolled oats 60 g", "milk 250 ml", "whey protein 1 scoop", "banana 1"]),
    Meal("breakfast", "Eggs & toast",
         ["Eggs 3", "whole-grain toast 1 slice", "tomato/cucumber"]),
]

_LUNCHES = [
    Meal("lunch", "Chicken quinoa salad",
         ["Chicken breast 150 g", "quinoa 100 g cooked", "mixed greens", "olive oil 1 tsp"]),
    Meal("lunch", "Tuna wrap",
         ["Tuna 150 g", "whole-wheat wrap 1", "mixed greens", "light yogurt sauce"]),
    Meal("lunch", "Tofu stir-fry",
         ["Tofu 200 g", "mixed veg 200 g", "brown rice 120 g cooked", "soy/garlic/ginger"]),
]

_DINNERS = [
    Meal("dinner", "Salmon plate",
         ["Salmon 150 g", "sweet potato 200 g", "broccoli 200 g"]),
    Meal("dinner", "Lean beef pasta",
         ["Lean beef 120 g", "whole-grain pasta 80 g dry", "marinara", "spinach"]),
    Meal("dinner", "Lentil curry set",
         ["Lentil curry 250 g", "basmati rice 120 g cooked", "side salad"]),
]

_SNACKS = [
    Meal("snack", "Apple + peanut butter", ["Apple 1", "peanut butter 2 tbsp"]),
    Meal("snack", "Cottage cheese", ["Cottage cheese 150 g"]),
    Meal("snack", "Whey shake", ["Whey protein 1 scoop", "water or milk"]),
    Meal("snack", "Hummus & carrots", ["Carrot sticks 150 g", "hummus 50 g"]),
]

def _rotate(seq: List[Meal], idx: int) -> Meal:
    return seq[idx % len(seq)]

def _weekly_grocery() -> List[GroceryItem]:
    items = [
        ("Chicken breast", "1.2 kg"),
        ("Salmon", "600 g"),
        ("Tuna (cans)", "3"),
        ("Lean beef", "500 g"),
        ("Eggs", "12"),
        ("Tofu", "2 blocks"),
        ("Greek yogurt", "1.5 kg"),
        ("Whey protein", "1 tub"),
        ("Quinoa", "1 pack"),
        ("Brown rice", "1 pack"),
        ("Whole-grain pasta", "1 pack"),
        ("Whole-wheat wraps", "1 pack"),
        ("Rolled oats", "1 pack"),
        ("Granola", "1 small pack"),
        ("Berries (frozen ok)", "1 kg"),
        ("Bananas", "7–10"),
        ("Apples", "6"),
        ("Leafy greens / mixed salad", "2 large bags"),
        ("Sweet potatoes", "1.5 kg"),
        ("Broccoli", "1 kg"),
        ("Mixed veg (frozen ok)", "1 kg"),
        ("Olive oil", "1 bottle"),
        ("Hummus", "1 tub"),
        ("Cottage cheese", "1 tub"),
        ("Basic spices & sauces", "as needed"),
    ]
    return [GroceryItem(name=n, qty=q) for n, q in items]

def _quick_recipes() -> List[Recipe]:
    return [
        Recipe(
            title="5-min Protein Yogurt Bowl",
            ingredients=["Greek yogurt 250 g", "berries 150 g", "granola 30 g", "honey (optional)"],
            steps=["Combine all ingredients in a bowl. Mix and enjoy."],
        ),
        Recipe(
            title="One-Pan Tofu Stir-Fry",
            ingredients=["Tofu 200 g (pressed, cubed)", "mixed veg 200 g", "soy sauce", "garlic", "ginger", "1 tsp oil"],
            steps=[
                "Heat pan, add oil and aromatics 30s.",
                "Add tofu cubes 3–4 min; add veg 3–4 min.",
                "Finish with soy/ginger/garlic to taste. Serve with rice."
            ],
        ),
        Recipe(
            title="Sheet-Pan Salmon",
            ingredients=["Salmon 150–200 g", "sweet potato 200 g (wedges)", "broccoli 200 g", "1 tsp oil", "salt/pepper"],
            steps=[
                "Oven 200°C. Toss veg with oil/salt.",
                "Roast veg 15 min, add salmon on tray; roast 10–12 min more."
            ],
        ),
    ]


# -----------------------------
# Public API
# -----------------------------

def plan_for_4_weeks(
    user: UserProfile,
    prefs: Optional[NutritionPrefs] = None
) -> NutritionPlan:
    """
    Main entrypoint used by the orchestrator.
    Returns a 7-day rotating plan + targets.
    """
    prefs = prefs or NutritionPrefs()

    # Defaults & fallbacks
    weight_kg = user.weight_kg or _default_weight(user.height_cm)
    height_cm = user.height_cm or 175.0
    age = user.age or 30
    sex = (user.sex or "male").lower()
    activity = user.activity_level or _infer_activity_from_workouts(user.workouts_per_week)

    # Baseline & targets
    bmr = _mifflin_st_jeor_bmr(sex, weight_kg, height_cm, age)
    tdee_est = _tdee(bmr, activity)
    kcal_rest = max(prefs.min_kcal_floor, int(round(tdee_est - prefs.target_daily_deficit_kcal)))
    kcal_workout = kcal_rest + prefs.workout_day_bonus_kcal

    protein_g, fat_g, carbs_rest_g, carbs_workout_g = _macro_targets(
        weight_kg, kcal_rest, kcal_workout, prefs.protein_g_per_kg, prefs.fat_g_per_kg
    )

    targets = MacroTargets(
        kcal_rest=kcal_rest,
        kcal_workout=kcal_workout,
        protein_g=protein_g,
        fat_g=fat_g,
        carbs_rest_g=carbs_rest_g,
        carbs_workout_g=carbs_workout_g,
        fiber_g_range=(prefs.min_fiber_g, prefs.max_fiber_g),
    )

    # Build 7-day rotation (assume 3 workouts/wk by default: days 2,4,6)
    workout_days = _pick_workout_days(user.workouts_per_week)
    rotation = []
    for i in range(1, 8):
        is_w = i in workout_days
        day_kcals = targets.kcal_workout if is_w else targets.kcal_rest
        day_meals = [
            _rotate(_BREAKFASTS, i-1),
            _rotate(_LUNCHES, i-1),
            _rotate(_DINNERS, i-1),
        ]
        # 1–2 snacks based on kcal band
        if day_kcals >= 2000:
            day_meals += [_rotate(_SNACKS, i-1), _rotate(_SNACKS, i)]
        else:
            day_meals += [_rotate(_SNACKS, i-1)]

        rotation.append(DayPlan(day_index=i, is_workout_day=is_w, kcal_target=day_kcals, meals=day_meals))

    summary = _summarize(user, targets)

    calculations = None
    if prefs.explain_calculations:
        calculations = {
            "inputs": asdict(user),
            "bmr_mifflin_st_jeor": round(bmr, 1),
            "tdee_est": round(tdee_est, 1),
            "policy": asdict(prefs),
        }

    plan = NutritionPlan(
        summary=summary,
        targets=targets,
        rotation_days=rotation,
        grocery_list=_weekly_grocery(),
        quick_recipes=_quick_recipes(),
        calculations=calculations,
    )
    return plan

def quick_plan_for_prompt(
    weight_kg: Optional[float] = None,
    height_cm: Optional[float] = None,
    age: Optional[int] = None,
    sex: Optional[str] = None,
    workouts_per_week: int = 3,
    activity_level: Optional[str] = None,
    diet_prefs: Optional[str] = None,
    allergies: Optional[List[str]] = None,
    daily_deficit_kcal: int = 500,
) -> NutritionPlan:
    """
    Convenience for simple, prompt-like usage without constructing dataclasses upstream.
    """
    user = UserProfile(
        weight_kg=weight_kg, height_cm=height_cm, age=age, sex=sex,
        workouts_per_week=workouts_per_week, activity_level=activity_level,
        diet_prefs=diet_prefs, allergies=allergies
    )
    prefs = NutritionPrefs(target_daily_deficit_kcal=daily_deficit_kcal)
    return plan_for_4_weeks(user, prefs)


# -----------------------------
# Helpers
# -----------------------------

def _infer_activity_from_workouts(workouts_per_week: int) -> str:
    if workouts_per_week <= 1:
        return "sedentary"
    if workouts_per_week == 2:
        return "light"
    if workouts_per_week == 3:
        return "moderate"
    if workouts_per_week == 4:
        return "active"
    return "very_active"

def _pick_workout_days(workouts_per_week: int) -> List[int]:
    # Spread across 7-day week; default [2,4,6] for 3x
    if workouts_per_week <= 0:
        return []
    if workouts_per_week == 1:
        return [3]
    if workouts_per_week == 2:
        return [2,5]
    if workouts_per_week == 3:
        return [2,4,6]
    if workouts_per_week == 4:
        return [1,3,5,7]
    # For 5–6, pack more days
    if workouts_per_week == 5:
        return [1,2,4,5,7]
    return [1,2,3,5,6,7]  # 6x

def _summarize(user: UserProfile, t: MacroTargets) -> str:
    who = user.name or "User"
    rate_hint = "Expect ~0.4–0.6 kg/week with good adherence (typical ~500 kcal/day deficit)."
    fiber = f"Fiber target: {t.fiber_g_range[0]}–{t.fiber_g_range[1]} g/day."
    return (
        f"{who}: Phase-1 weight-loss nutrition for 4 weeks.\n"
        f"Calories: {t.kcal_rest} kcal (rest) / {t.kcal_workout} kcal (workout).\n"
        f"Macros: protein {t.protein_g} g, fat {t.fat_g} g, carbs {t.carbs_rest_g} g (rest) / {t.carbs_workout_g} g (workout).\n"
        f"{fiber} {rate_hint}"
    )


# -----------------------------
# Serialization utilities (optional)
# -----------------------------

def to_dict(plan: NutritionPlan) -> Dict[str, Any]:
    """Serialize plan to a primitive dict (JSON-friendly)."""
    d = asdict(plan)
    # dataclasses already produce JSONish dicts; return as-is
    return d

def to_json(plan: NutritionPlan, indent: int = 2) -> str:
    return json.dumps(to_dict(plan), indent=indent)


# -----------------------------
# Demo / Self-test
# -----------------------------

if __name__ == "__main__":
    demo_user = UserProfile(
        name="Demo User",
        sex="male",
        age=28,
        height_cm=175,
        weight_kg=75,
        activity_level=None,
        workouts_per_week=3,
        goal="lose 10 lb",
        diet_prefs="omnivore",
        allergies=None,
    )
    plan = plan_for_4_weeks(demo_user)
    print(plan.summary)
    print()
    print("Targets:")
    print(plan.targets)
    print()
    print("Day 1 sample:")
    for m in plan.rotation_days[0].meals:
        print(f" - {m.name}: {m.option}")
    print()
    print("Grocery (first 5):")
    for g in plan.grocery_list[:5]:
        print(f" - {g.name}: {g.qty}")
    print()
    print("JSON preview:")
    print(to_json(plan)[:500], "...")
