import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class CommuteRequest(BaseModel):
    origin: str
    destination: str
    event_time: str  # ISO8601

@app.post("/recommend")
def recommend_route(request: CommuteRequest or None):
    # Placeholder for logic to call ferry, traffic, and maps APIs
    return {"recommendation": "ferry", "details": "Sample output"}

from fastapi import Query

@app.get("/ferry-times")
def get_ferry_times_api(origin: str, destination: str, event_time: str, after_time: str = Query(None, description="HH:MM 24-hour Pacific Time")):
    from mcp.wsdot_ferry_server import get_ferry_times
    try:
        sailings = get_ferry_times(origin, destination, event_time)
        def parse_eta(s):
            try:
                from datetime import datetime
                return datetime.strptime(s['estimated_arrival_time'], '%Y-%m-%d %I:%M %p') if s['estimated_arrival_time'] else None
            except Exception:
                return None
        from zoneinfo import ZoneInfo
        pacific = ZoneInfo("America/Los_Angeles")
        from datetime import datetime
        # Determine cutoff time for filtering
        if after_time:
            today = datetime.now(pacific).strftime('%Y-%m-%d')
            cutoff = datetime.strptime(f"{today} {after_time}", "%Y-%m-%d %H:%M").replace(tzinfo=pacific)
        else:
            cutoff = datetime.now(pacific)
        def parse_departure(s):
            try:
                return datetime.strptime(s['time'], '%Y-%m-%d %I:%M %p').replace(tzinfo=pacific) if s['time'] else None
            except Exception:
                return None
        sailings_sorted = sorted(
            sailings,
            key=lambda s: (parse_eta(s) is None, parse_eta(s))
        )
        future_sailings = [s for s in sailings_sorted if parse_departure(s) and parse_departure(s) > cutoff]
        return {"ferry_times": future_sailings}
    except Exception as e:
        return {"error": str(e)}

@app.get("/next-kitsap-ferries")
def next_kitsap_ferries(event_time: str, after_time: str = Query(None, description="HH:MM 24-hour Pacific Time")):
    from mcp.wsdot_ferry_server import get_ferry_times
    from zoneinfo import ZoneInfo
    from datetime import datetime
    pacific = ZoneInfo("America/Los_Angeles")
    routes = [
        ("Edmonds", "Kingston"),
        ("Seattle", "Bainbridge Island"),
        ("Seattle", "Bremerton"),
        ("Fauntleroy", "Southworth"),
    ]
    results = {}
    for origin, destination in routes:
        try:
            sailings = get_ferry_times(origin, destination, event_time)
            if after_time:
                today = datetime.now(pacific).strftime('%Y-%m-%d')
                cutoff = datetime.strptime(f"{today} {after_time}", "%Y-%m-%d %H:%M").replace(tzinfo=pacific)
            else:
                cutoff = datetime.now(pacific)
            def parse_departure(s):
                try:
                    return datetime.strptime(s['time'], '%Y-%m-%d %I:%M %p').replace(tzinfo=pacific) if s['time'] else None
                except Exception:
                    return None
            future_sailings = [s for s in sailings if parse_departure(s) and parse_departure(s) > cutoff]
            results[f"{origin}_to_{destination}"] = future_sailings[0] if future_sailings else None
        except Exception as e:
            results[f"{origin}_to_{destination}"] = {"error": str(e)}
    return results

@app.get("/next-seattle-ferries")
def next_seattle_ferries(event_time: str, after_time: str = Query(None, description="HH:MM 24-hour Pacific Time")):
    from mcp.wsdot_ferry_server import get_ferry_times
    from zoneinfo import ZoneInfo
    from datetime import datetime
    pacific = ZoneInfo("America/Los_Angeles")
    routes = [
        ("Kingston", "Edmonds"),
        ("Bainbridge Island", "Seattle"),
        ("Bremerton", "Seattle"),
        ("Southworth", "Fauntleroy"),
    ]
    results = {}
    for origin, destination in routes:
        try:
            sailings = get_ferry_times(origin, destination, event_time)
            if after_time:
                today = datetime.now(pacific).strftime('%Y-%m-%d')
                cutoff = datetime.strptime(f"{today} {after_time}", "%Y-%m-%d %H:%M").replace(tzinfo=pacific)
            else:
                cutoff = datetime.now(pacific)
            def parse_departure(s):
                try:
                    return datetime.strptime(s['time'], '%Y-%m-%d %I:%M %p').replace(tzinfo=pacific) if s['time'] else None
                except Exception:
                    return None
            future_sailings = [s for s in sailings if parse_departure(s) and parse_departure(s) > cutoff]
            results[f"{origin}_to_{destination}"] = future_sailings[0] if future_sailings else None
        except Exception as e:
            results[f"{origin}_to_{destination}"] = {"error": str(e)}
    return results

@app.get("/traffic")
def get_traffic(origin: str, destination: str, event_time: str):
    # Placeholder for MCP call to WSDOT Traffic API
    return {"traffic": "Light"}

@app.get("/drive-times")
def get_drive_times(origin: str, destination: str, event_time: str):
    # Placeholder for MCP call to Google Maps Directions API
    return {"drive_time": "1h 20m"}
