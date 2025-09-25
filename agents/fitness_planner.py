from typing import Dict, Any
from openai import OpenAI
from ..prompts import SYSTEM_PROMPT
from ..schemas import Plan, Inputs
from ..tools.weather import weather_today, weather_heat_adjustment
from ..tools.progress import progress_last_week
import json

def _json_schema() -> Dict[str, Any]:
    return {
        "name":"FitnessPlan",
        "schema":{
            "type":"object",
            "properties":{
                "meta":{"type":"object","properties":{
                    "plan_id":{"type":"string"},"duration_weeks":{"type":"integer"},
                    "sessions_per_week":{"type":"integer"},"session_length_min":{"type":"integer"},
                    "goal":{"type":"string"},"experience":{"type":"string"},
                    "environment":{"type":"string"},"generated_at":{"type":"string"}
                },"required":["plan_id","duration_weeks","sessions_per_week","session_length_min","goal","experience","environment","generated_at"]},
                "global_rules":{"type":"object","properties":{
                    "progression":{"type":"string"},
                    "rest_days":{"type":"array","items":{"type":"string"}},
                    "safety_flags":{"type":"array","items":{"type":"string"}}
                },"required":["progression","rest_days","safety_flags"]},
                "weeks":{"type":"array","items":{"type":"object","properties":{
                    "week":{"type":"integer"},
                    "sessions":{"type":"array","items":{"type":"object","properties":{
                        "day":{"type":"string"},"theme":{"type":"string"},
                        "blocks":{"type":"array","items":{"type":"object","properties":{
                            "type":{"type":"string"},
                            "items":{"type":"array","items":{"type":"object","properties":{
                                "name":{"type":"string"},"sets":{"type":["integer","null"]},
                                "reps":{"type":["string","null"]},"rpe":{"type":["string","integer","null"]},
                                "duration_min":{"type":["integer","null"]},"pattern":{"type":["string","null"]},
                                "rest_sec":{"type":["integer","null"]}
                            },"required":["name"]}}
                        },"required":["type","items"]}},
                        "substitutions":{"type":"object"},
                        "tags":{"type":"array","items":{"type":"string"}}
                    },"required":["day","theme","blocks","substitutions","tags"]}}
                },"required":["week","sessions"]}},
                "adjustment_hooks":{"type":"object","properties":{
                    "on_low_compliance":{"type":"string"},
                    "on_high_RPE":{"type":"string"},
                    "on_hot_weather":{"type":"string"}
                },"required":["on_low_compliance","on_high_RPE","on_hot_weather"]}
            },
            "required":["meta","global_rules","weeks","adjustment_hooks"]
        }
    }

def render_user_prompt(inputs: Inputs) -> str:
    w = weather_today(inputs.city)
    heat = weather_heat_adjustment(w.get("heatIndexC", 24))
    last = progress_last_week(inputs.user_id)
    details = {
        "goal": inputs.goal,
        "frequency": inputs.freq,
        "experience": inputs.experience,
        "session_length_min": inputs.session_len,
        "environment": inputs.environment,
        "equipment": inputs.equipment,
        "constraints": inputs.constraints,
        "preferences": inputs.preferences,
        "city": inputs.city,
        "weather": w,
        "weather_adjustment": heat,
        "last_week_progress": last
    }
    return json.dumps(details, ensure_ascii=False, indent=2)

def generate_plan(inputs: Inputs, model: str = "gpt-5") -> Plan:
    client = OpenAI()
    schema = _json_schema()
    user_prompt = render_user_prompt(inputs)
    resp = client.responses.create(
        model=model,
        messages=[
            {"role":"system","content": SYSTEM_PROMPT},
            {"role":"user","content": "Here are the inputs and tool signals. Create the 4-week plan as JSON only:\n"+user_prompt},
        ],
        response_format={"type":"json_schema","json_schema": schema},
        temperature=0.4,
    )
    try:
        content = resp.output_text
    except Exception:
        content = None
        for out in getattr(resp, "output", []):
            if getattr(out, "type", "") == "message":
                for c in getattr(out.message, "content", []):
                    if getattr(c, "type", "") == "output_text":
                        content = c.text
                        break
    if not content:
        raise RuntimeError("No content returned by model")
    data = json.loads(content)
    return Plan.model_validate(data)
