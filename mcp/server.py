from mcp.server.fastmcp import FastMCP
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from google_maps_server import get_drive_time
from wsdot_ferry_server import get_ferry_times
from commute_planner import next_seattle_ferries_with_drive, best_route_to_event

mcp = FastMCP("commute-server")
PACIFIC = ZoneInfo("America/Los_Angeles")

def parse_datetime(dt: Optional[str]) -> Optional[datetime]:
    if dt is None:
        return None
    try:
        return datetime.fromisoformat(dt)
    except Exception:
        return None

@mcp.resource("transit://ferries/terminals")
def fetch_terminals():
    api_key = os.getenv('WSDOT_API_KEY')
    if not api_key:
        raise Exception("WSDOT_API_KEY environment variable not set")
    url = 'https://wsdot.wa.gov/Ferries/API/Terminals/rest/terminalbasics'
    params = {'apiaccesscode': api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    for terminal in data:
        print(f"{terminal['TerminalName']}: {terminal['TerminalID']}") 

@mcp.tool('drive_time')
def drive_time_tool(origin: str, destination: str, departure_time: Optional[str] = None, arrival_time: Optional[str] = None) -> dict:
    """
    Returns drive time in minutes between origin and destination, optionally factoring in departure or arrival time (ISO 8601 string, local time).
    """
    dep = parse_datetime(departure_time)
    arr = parse_datetime(arrival_time)
    minutes = get_drive_time(origin, destination, departure_time=dep, arrival_time=arr)
    return {"drive_minutes": minutes}

@mcp.tool('ferry_times')
def ferry_times_tool(origin: str, destination: str, event_time: str) -> dict:
    """
    Returns all ferry sailings for the specified origin, destination, and event date (YYYY-MM-DD).
    """
    times = get_ferry_times(origin, destination, event_time)
    return {"ferry_times": times}

@mcp.tool('next_seattle_ferries_with_drive')
def next_seattle_ferries_with_drive_tool(origin: Optional[str] = None, event_time: Optional[str] = None, buffer_minutes: int = 10) -> dict:
    """
    Returns the next ferry you can catch from Kitsap to Seattle, factoring in drive time from your origin and a buffer.
    """
    results = next_seattle_ferries_with_drive(
        origin=origin,
        event_time=event_time,
        buffer_minutes=buffer_minutes
    )
    return {"results": results}

@mcp.tool('best_route_to_event')
def best_route_to_event_tool(event_time: str, event_address: str, origin: Optional[str] = None, buffer_minutes: int = 10) -> dict:
    """
    Returns the best and second-best commute options (drive or ferry) to an event, minimizing wait at your destination and total driving time.
    event_time: 'YYYY-MM-DD HH:MM' (local time)
    event_address: destination address
    origin: starting address (optional)
    buffer_minutes: extra time to allow for parking/walking at terminal (default 10)
    """
    result = best_route_to_event(
        event_time_str=event_time,
        event_address=event_address,
        origin=origin,
        buffer_minutes=buffer_minutes
    )
    return result

@mcp.prompt("get_to_seattle")
def get_to_seattle():
    """
    Returns the best and second-best commute options (drive or ferry) to Seattle, minimizing wait at your destination and total driving time.
    """
    return """
    1. The origin location will be in Kitsap County, WA
    2. The event time will be in local time
    3. The event address will be in Seattle, WA
    4. The buffer minutes will be 10
    5. Find out two options: drive or ferry
    6. Always find options that get you there at least 15 minutes before the event time
    7. Return the best 2 options
    """

@mcp.prompt("get_to_kitsap")
def get_to_kitsap():
    """
    Returns the best and second-best commute options (drive or ferry) to Kitsap County, minimizing wait at your destination and total driving time.
    """
    return """
    1. The origin location will be in Seattle, WA
    2. The event time will be in local time
    3. The event address will be in Kitsap County, WA
    4. The buffer minutes will be 10
    5. Find out two options: drive or ferry
    6. Always find options that get you there at least 15 minutes before the event time
    7. Return the best 2 options
    """

@mcp.prompt("get_there_by")
def get_there_by(location, event_time, buffer_minutes=10):
    """
    Returns the best and second-best commute options (drive or ferry) to a location, minimizing wait at your destination and total driving time.
    location: destination address
    event_time: 'YYYY-MM-DD HH:MM' (local time)
    buffer_minutes: extra time to allow for parking/walking at terminal (default 10)
    """
    return f"""
    1. The origin location will be in Kitsap County, WA
    2. The event time will be {event_time} in local time
    3. The event address will be {location}
    4. The buffer minutes will be {buffer_minutes}
    5. Always find options that get you there at least 15 minutes before the event time
    6. Return two options to get there
    """
    
if __name__ == "__main__":
    mcp.run()