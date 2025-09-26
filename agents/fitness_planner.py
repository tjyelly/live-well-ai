# fitness_planner.py

from typing import Dict, Any
import os   
from dotenv import load_dotenv
from openai import OpenAI

from tools.singapore_time import singapore_time
from tools.singapore_weather import singapore_weather

load_dotenv()  # reads .env at project root
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Put it in a .env or export it in your shell.")

_client = OpenAI(api_key=_api_key)
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_SYSTEM = (
    "You are a certified fitness coach. Create safe, practical workout plans for adults. "
    "Balance cardio and strength, include warm-up and cool-down, and respect user constraints. "
    "When planning, you should request up-to-date Singapore weather via the provided tool before finalizing."
)

# Tools the model can request by name; they map to execute_tool() below.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "Get a simple Singapore 14-day forecast as lines 'YYYY-MM-DD: Condition'.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "time",
            "description": "Get the current local time in Singapore.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]

def _safe_str(x) -> str:
    """Coerce possibly-None values to a safe string (prevents None.strip())."""
    return "" if x is None else str(x)

def _build_user_prompt(user_goal: str) -> str:
    """Single, clear set of instructions for the final plan format."""
    return (
        "User goal & constraints:\n"
        f"{user_goal.strip()}\n\n"
        "First, request any tools you need (e.g., weather, time). "
        "Only after tool results are returned, produce the final **2-week fitness plan** following these rules:\n"
        "1) 3–5 sessions/week as appropriate for the goal and fitness level.\n"
        "2) Include warm-up and cool-down for each session.\n"
        "3) Mix cardio and strength; suggest sets×reps or time.\n"
        "4) Adapt to weather: Rain/Thunder/Haze -> prefer indoor/covered that day; Hot/Humid -> reduce outdoor HIIT and add hydration notes.\n"
        "5) Output sections:\n"
        "   - Overview (2–3 lines)\n"
        "   - Week 1 (Day-by-day bullets)\n"
        "   - Week 2 (Day-by-day bullets)\n"
        "   - Progression & Safety (bullets)\n"
        "   - Weather & Equipment Adjustments (bullets)\n"
        "   - Optional Tips (bullets)\n"
    )

def fitness_planner(state: Dict[str, Any]) -> Dict[str, str]:
    """
    Reads state['user_goal'] (string), lets the LLM REQUEST tools, executes them locally via execute_tool(),
    feeds tool results back to the model, then returns a plain-text 2-week plan.
    """
    goal = _safe_str(state.get("user_goal")).strip()
    if not goal:
        return {"fitness_plan": "Please provide your goal and constraints in 'user_goal'."}

    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": _build_user_prompt(goal)},
    ]

    chat = _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="required",    # force the model to suggest at least one tool call here
        temperature=0.3,
    )
    choice = chat.choices[0]

    max_tool_hops = 3
    hops = 0

    while choice.finish_reason == "tool_calls" and choice.message.tool_calls and hops < max_tool_hops:
        hops += 1

        # Add assistant's tool_calls turn
        messages.append({
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": choice.message.tool_calls
        })

        # Execute each requested tool and add tool results
        for tc in choice.message.tool_calls:
            tool_name = tc.function.name  # must match TOOLS 'name': 'weather' / 'time'
            try:
                result_text = execute_tool(tool_name)
            except Exception as e:
                result_text = f"(tool '{tool_name}' failed: {e})"

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": _safe_str(result_text)
            })

        # Ask the model again, now with tool outputs
        chat = _client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
        )
        choice = chat.choices[0]

    # Final answer
    if choice.message and choice.message.content:
        return {"fitness_plan": choice.message.content.strip()}

    # Fallback: ask once more without tools
    chat = _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        temperature=0.6,
    )
    return {"fitness_plan": chat.choices[0].message.content.strip()}

def execute_tool(tool_name: str) -> str:
    tool = (tool_name or "").strip().lower()
    try:
        if tool == "time":
            return singapore_time()
        elif tool == "weather":
            return singapore_weather()  # default 14 days inside your function
        else:
            return f"Unknown tool: {tool}"
    except Exception as e:
        msg = f"(tool '{tool}' failed: {type(e).__name__}: {e})"
        print("DEBUG execute_tool error:", msg)
        return msg
