from datetime import datetime
import pytz

def singapore_time() -> str:
    """
    Returns the current local time in Singapore as a formatted string.
    """
    singapore_tz = pytz.timezone("Asia/Singapore")
    singapore_time = datetime.now(singapore_tz)
    print("\n=== Singapore time tool called ===\n")
    return f"Time in Singapore now: {singapore_time.strftime('%Y-%m-%d %H:%M:%S')}"
