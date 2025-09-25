# tools/singapore_time.py
from datetime import datetime
import pytz

def singapore_time() -> str:
    """
    Returns the current time in Singapore formatted nicely.
    """
    tz = pytz.timezone("Asia/Singapore")
    now = datetime.now(tz)
    return f"Time in Singapore now: {now.strftime('%Y-%m-%d %H:%M:%S')}"
