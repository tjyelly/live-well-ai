# fitness_planner.py (patch)

import os
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_SYSTEM = (
    "You are a certified fitness coach. Create safe, practical 2-week plans. "
    "Balance cardio & strength; include warm-up/cool-down; respect constraints."
)

# If you’re doing “LLM suggests tool, another node executes it”, you only need the schema here.
_WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_singapore_weather",
        "description": "Return a simple 14-day SG forecast as 'YYYY-MM-DD: Condition' lines.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Forecast days", "default": 14}
            },
            "required": [],
            "additionalProperties": False
        },
    },
}

def _safe_str(x) -> str:
    return "" if x is None else str(x)

def fitness_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ask LLM to request weather tool (no execution here)."""
    goal = _safe_str(state.get("user_goal")).strip()
    if not goal:
        return {"planner_tool_request": None, "fitness_plan": "Please set 'user_goal' first."}

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content":
            "User goal & constraints:\n"
            f"{goal}\n\n"
            "Request the Singapore weather tool if needed. Do not give the final plan yet."
         },
    ]

    # ✅ Chat Completions supports tools + messages
    chat = _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        tools=[_WEATHER_TOOL],
        tool_choice="required",  # force a tool use
        temperature=0.6,
    )

    # Extract the tool call (first one)
    tool_req = None
    choice = chat.choices[0]
    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        tc = choice.message.tool_calls[0]
        tool_req = {"name": tc.function.name, "arguments": tc.function.arguments}

    return {"planner_tool_request": tool_req}

def fitness_planner_finalize_node(state: Dict[str, Any]) -> Dict[str, str]:
    """After another node executed the tool and stored weather_info, produce the final 2-week plan."""
    goal = _safe_str(state.get("user_goal")).strip()
    forecast = _safe_str(state.get("weather_info")).strip() or "(no weather available)"

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content":
            "User goal & constraints:\n"
            f"{goal}\n\n"
            "Weather context (Singapore):\n"
            f"{forecast}\n\n"
            "Now produce the final **2-week fitness plan** with weather-adapted sessions "
            "(indoor swaps on Rain/Thunder/Haze; hydration/shortened intensity on Hot/Humid). "
            "Sections: Overview; Week 1; Week 2; Progression & Safety; Weather & Equipment Adjustments; Optional Tips."
         },
    ]

    chat = _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        temperature=0.6,
    )
    plan_text = chat.choices[0].message.content.strip()
    return {"fitness_plan": plan_text}

def execute_tool(tool_name: str) -> str:
    """If you still keep this convenience wrapper, guard against None before strip()."""
    from tools.singapore_time import singapore_time
    from tools.singapore_weather import singapore_weather

    tool = _safe_str(tool_name).strip().lower()
    if tool == "time":
        return singapore_time()
    if tool == "weather":
        return singapore_weather()
    return f"Unknown tool: {tool}"
