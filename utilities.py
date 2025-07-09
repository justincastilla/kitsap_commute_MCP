import os
import json
from datetime import datetime



def get_day_type(event_time):
    """
    Parse event_time and return 'weekday' or 'weekend'.
    If event_time is invalid or None, use today.
    """
    if event_time:
        try:
            dt = datetime.fromisoformat(event_time)
        except Exception:
            try:
                dt = datetime.strptime(event_time, '%Y-%m-%d %H:%M')
            except Exception:
                dt = datetime.now()
    else:
        dt = datetime.now()
    return 'weekend' if dt.weekday() >= 5 else 'weekday'


def parse_datetime(dt: str | None) -> datetime | None:
    if dt is None:
        return None
    try:
        return datetime.fromisoformat(dt)
    except Exception:
        return None

def get_schedule(): 
    path = os.path.join(os.path.dirname(__file__), 'static_ferry_schedules.json')
    with open(path, 'r') as f:
        content = f.read()
        content = '\n'.join([line for line in content.splitlines() if not line.strip().startswith('//')])
    return json.loads(content)

def to_epoch_seconds(dt):
    if hasattr(dt, 'timestamp'):
        return int(dt.timestamp())
    return int(dt)