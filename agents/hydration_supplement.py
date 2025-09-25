from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Literal, Tuple

Intensity = Literal["light", "moderate", "vigorous"]

# -----------------------------
# Data Models
# -----------------------------

@dataclass
class UserProfile:
    name: str
    body_mass_kg: float
    height_cm: Optional[float] = None
    sex: Optional[Literal["male", "female"]] = None
    age: Optional[int] = None

    # Flags / conditions
    caffeine_sensitive: bool = False
    vegetarian_or_vegan: bool = False
    kidney_issue: bool = False
    pregnant_or_breastfeeding: bool = False
    fish_allergy: bool = False
    on_anticoagulants: bool = False
    vitamin_d_deficient_or_low_sun: bool = False
    sodium_restricted: bool = False

@dataclass
class Climate:
    avg_temp_c: float
    avg_humidity_pct: float
    altitude_m: Optional[int] = None

@dataclass
class Workout:
    day_of_week: Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    minutes: int
    intensity: Intensity
    is_outdoor: bool = True

@dataclass
class PlanConfig:
    weeks: int = 4
    baseline_ml_per_kg: int = 35
    prehydrate_ml_per_kg: Tuple[int, int] = (5, 7)
    topup_ml_per_kg_2h: Tuple[int, int] = (3, 5)
    during_lph_range: Tuple[float, float] = (0.4, 0.8)
    sodium_mg_per_hour_range: Tuple[int, int] = (300, 600)
    post_replace_factor_range: Tuple[float, float] = (1.25, 1.50)

# -----------------------------
# Hydration & Supplement Agent
# -----------------------------

class HydrationSupplementAgent:
    def __init__(self, user: UserProfile, climate: Climate, workouts_by_week: List[List[Workout]], cfg: PlanConfig = PlanConfig()):
        if len(workouts_by_week) != cfg.weeks:
            raise ValueError(f"Expected {cfg.weeks} weeks of workouts, got {len(workouts_by_week)}")
        self.user = user
        self.climate = climate
        self.weeks = workouts_by_week
        self.cfg = cfg

    # --- Helper functions (shortened here for readability) ---
    def _heat_humidity_multiplier(self) -> float:
        t, h = self.climate.avg_temp_c, self.climate.avg_humidity_pct
        mult = 1.0
        if t >= 27: mult += 0.10
        if t >= 32: mult += 0.10
        if h >= 60: mult += 0.05
        if h >= 75: mult += 0.05
        if self.climate.altitude_m and self.climate.altitude_m >= 1500:
            mult += 0.05
        return min(mult, 1.35)

    def _daily_baseline_ml(self) -> int:
        return int(round(self.user.body_mass_kg * self.cfg.baseline_ml_per_kg))

    def _hydration_for_workout(self, w: Workout) -> Dict:
        return {
            "workout": asdict(w),
            "pre": "Drink 5–7 ml/kg at T–4h; optional top-up 3–5 ml/kg at T–2h",
            "during": "0.4–0.8 L per hour; add sodium if >60min or very sweaty",
            "post": "Replace 125–150% of weight lost; or ~0.6 L/hour if no scale"
        }

    # --- Public API ---
    def generate_hydration_plan(self) -> Dict:
        weeks_out = []
        for i, week in enumerate(self.weeks, start=1):
            day_map = {d: [] for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]}
            for w in week:
                day_map[w.day_of_week].append(self._hydration_for_workout(w))
            weeks_out.append({
                "week": i,
                "daily_baseline_target_ml": self._daily_baseline_ml(),
                "days": day_map
            })
        return {"user": asdict(self.user), "plan": weeks_out}

    def generate_supplement_cheatsheet(self) -> Dict:
        u = self.user
        items = [
            {
                "what": "Protein powder",
                "why": "Helps meet daily protein needs.",
                "dose": "20–30 g per serving.",
                "skip_if": None
            },
            {
                "what": "Creatine monohydrate",
                "why": "Supports strength and recovery.",
                "dose": "3–5 g/day.",
                "skip_if": "Avoid if kidney issues or pregnancy/breastfeeding" if (u.kidney_issue or u.pregnant_or_breastfeeding) else None
            }
        ]
        return {"cheatsheet": items}

    def generate(self) -> Dict:
        return {
            "hydration_plan": self.generate_hydration_plan(),
            "supplement_cheatsheet": self.generate_supplement_cheatsheet()
        }
