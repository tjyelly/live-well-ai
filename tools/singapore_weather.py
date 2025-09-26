# singapore_weather_update.py  (forecast: one-word per day)
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Dict, Optional

import httpx

# ---------- Logging ----------
LOG_PATH = os.getenv("WEATHER_LOG_PATH", "weather.log")
LOG_LEVEL = os.getenv("WEATHER_LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("sg_forecast")
if not logger.handlers:
    logger.setLevel(LOG_LEVEL)
    fh = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)

# ---------- Constants ----------
# Singapore coords
LAT = 1.3521
LON = 103.8198
TIMEZONE = "Asia/Singapore"

# Open-Meteo daily fields (no API key required)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
# Provider limit: typically up to 16 days
PROVIDER_MAX_DAYS = 14

# Classification thresholds (tweak if you like)
RAINY_DAY_MM = 1.0             # >=1.0 mm in a day => Rainy
RAINY_PROB_PCT = 60            # or precip prob >=60% => Rainy
SUNNY_TEMP_MAX_C = 31.0        # hot enough to call "Sunny"
SUNNY_MAX_PROB_PCT = 20        # low rain chance to call "Sunny"
SUNNY_MAX_MM = 0.5             # very little rain

def _classify_day(temp_max_c: Optional[float],
                  precip_mm: Optional[float],
                  precip_prob_max: Optional[float]) -> str:
    """Return 'Rainy' | 'Sunny' | 'Normal' based on simple daily rules."""
    try:
        if (precip_mm is not None and float(precip_mm) >= RAINY_DAY_MM) or \
                (precip_prob_max is not None and float(precip_prob_max) >= RAINY_PROB_PCT):
            return "Rainy"
    except (TypeError, ValueError):
        pass
    try:
        if (temp_max_c is not None and float(temp_max_c) >= SUNNY_TEMP_MAX_C) and \
                (precip_prob_max is not None and float(precip_prob_max) <= SUNNY_MAX_PROB_PCT) and \
                (precip_mm is not None and float(precip_mm) <= SUNNY_MAX_MM):
            return "Sunny"
    except (TypeError, ValueError):
        pass
    return "Normal"

def forecast_sg_weather(days: int = 20) -> List[Dict[str, str]]:
    """
    Returns a list like: [{ "date": "2025-09-25", "condition": "Rainy" }, ...]
    Caps to provider max days (usually 16) and logs all calls.
    """
    n_days = min(days, PROVIDER_MAX_DAYS)
    if days > n_days:
        logger.info("Requested days=%d capped to provider_max=%d", days, n_days)

    params = {
        "latitude": LAT,
        "longitude": LON,
        "timezone": TIMEZONE,
        "daily": ",".join([
            "temperature_2m_max",
            "precipitation_sum",
            "precipitation_probability_max"
        ]),
        "forecast_days": n_days
    }

    start = time.perf_counter()
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(OPEN_METEO_URL, params=params)
            dur = time.perf_counter() - start
            logger.info("GET %s status=%s duration=%.3fs params=%s",
                        OPEN_METEO_URL, r.status_code, dur, {k: params[k] for k in ("latitude","longitude","forecast_days")})
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error("Forecast fetch failed: %r", e)
        # Return 'Normal' for requested days to keep output shape simple
        return [{"date": f"day+{i+1}", "condition": "Normal"} for i in range(days)]

    daily = data.get("daily") or {}
    dates = daily.get("time") or []
    tmaxs = daily.get("temperature_2m_max") or []
    psums = daily.get("precipitation_sum") or []
    pprob = daily.get("precipitation_probability_max") or []

    out: List[Dict[str, str]] = []
    for i in range(min(len(dates), n_days)):
        label = _classify_day(
            tmaxs[i] if i < len(tmaxs) else None,
            psums[i] if i < len(psums) else None,
            pprob[i] if i < len(pprob) else None,
        )
        out.append({"date": dates[i], "condition": label})
    logger.info("Classified %d days: %s", len(out),
                ", ".join([f"{d['date']}={d['condition']}" for d in out]))
    return out

if __name__ == "__main__":
    # Print one word per day, datewise
    for row in forecast_sg_weather(20):
        print(f"{row['date']}: {row['condition']}")

def singapore_weather(days: int = 14) -> str:
    """
    Returns a simple multi-line string forecast for Singapore.
    Example:
        2025-09-25: Rainy
        2025-09-26: Sunny
    """
    rows = forecast_sg_weather(days)
    print("\n=== Singapore weather tool called ===\n")
    return "\n".join([f"{r['date']}: {r['condition']}" for r in rows])

