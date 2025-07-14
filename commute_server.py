import os
import json
import requests
import fastmcp
from utilities import get_schedule, get_day_type, to_epoch_seconds, parse_datetime
from datetime import datetime
from typing import Optional

wdot_api_key = os.getenv('WSDOT_API_KEY')
if not wdot_api_key:
    raise Exception("WSDOT_API_KEY environment variable not set")

google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
if not google_api_key:
    raise Exception("GOOGLE_MAPS_API_KEY environment variable not set")

mcp = fastmcp.FastMCP("commute-server")

schedule = get_schedule()

@mcp.resource(
    uri="transit://ferries/schedules/{direction}",
    name="Ferry Schedules",
    description="Full or filtered ferry schedules from static_ferry_schedules.json. Optionally filter by direction"
)
def fetch_ferry_schedules(direction: str | None = None) -> dict:
    """
    Returns the full ferry schedule, or only routes matching the given direction (east, west, kitsap, king).
    """
    if direction is None:
        return {"schedules": schedule}
    direction = direction.lower()
    filtered = {route: info for route, info in schedule.items()
                if direction in [d.lower() for d in info.get("direction", [])]}
    return {"schedules": filtered}

@mcp.resource(
    uri="transit://ferries/terminals",
    name="Ferry Terminals",
    description="List of ferry terminals")
def fetch_terminals():
    url = 'https://wsdot.wa.gov/Ferries/API/Terminals/rest/terminalbasics'
    params = {'apiaccesscode': wdot_api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data

@mcp.tool(
    name="find_nearby_ferry_terminals",
    description="Finds the nearest ferry terminals to a given address using a static terminal list and Google Maps Geocoding API."
)
def find_nearby_ferry_terminals(address: str, max_results: int = 3) -> dict:
    """
    Finds the nearest ferry terminals to a given address using a static terminal list and Google Maps Geocoding API.
    Returns a sorted list of the closest terminals with name, address, lat, lng, place_id, and distance_km.
    """
    import json
    import os
    # Load terminals from JSON file
    terminals_path = os.path.join(os.path.dirname(__file__), 'data', 'ferry_terminals.json')
    with open(terminals_path, 'r') as f:
        terminals = json.load(f)
    # Geocode address
    geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
    geo_params = {"address": address, "key": google_api_key}
    geo_resp = requests.get(geo_url, params=geo_params)
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()
    try:
        loc = geo_data['results'][0]['geometry']['location']
        addr_lat, addr_lng = loc['lat'], loc['lng']
    except (KeyError, IndexError):
        return {"terminals": [], "error": f"Could not geocode address: {address}"}

    # Compute distances
    from utilities import haversine
    results = []
    for t in terminals:
        try:
            t_lat = float(t['lat'])
            t_lng = float(t['lng'])
            dist = haversine(addr_lat, addr_lng, t_lat, t_lng)
            results.append({
                "name": t.get('display_name'),
                "address": t.get('address'),
                "lat": t_lat,
                "lng": t_lng,
                "place_id": t.get('place_id'),
                "distance_km": round(dist, 2),
                "city": t.get('city'),
                "neighborhood": t.get('neighborhood'),
                "county": t.get('county')
            })
        except Exception as e:
            print({"error": str(e), "terminal": t})
            continue
    # Sort and limit
    results.sort(key=lambda x: x['distance_km'])
    return {"terminals": results[:max_results]}


@mcp.tool(
    name='drive_time',
    description="Returns drive time between origin and destination")
def drive_time_tool(
    origin: str, 
    destination: str, 
    departure_time: Optional[str] = None, 
    arrival_time: Optional[str] = None) -> dict:
    """
    Returns drive time in minutes between origin and destination, 
    optionally factoring in departure or arrival time (ISO 8601 string, local time).
    """
    dep = parse_datetime(departure_time)
    arr = parse_datetime(arrival_time)
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": origin, "destination": destination, "key": google_api_key}

    if arr is not None:
        params['arrival_time'] = to_epoch_seconds(arr)
    elif dep is not None:
        params['departure_time'] = to_epoch_seconds(dep)

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    try:
        leg = data['routes'][0]['legs'][0]
        minutes = int(leg['duration']['value'] // 60)
        traffic = False
        minutes_in_traffic = None
        if 'duration_in_traffic' in leg:
            minutes_in_traffic = int(leg['duration_in_traffic']['value'] // 60)
            traffic = minutes_in_traffic > minutes
        result = {"drive_minutes": minutes, "traffic": traffic}
        if minutes_in_traffic is not None:
            result["drive_minutes_in_traffic"] = minutes_in_traffic
        return result
    except (KeyError, IndexError):
        raise Exception(f"Could not extract drive time from response: {data}")

@mcp.tool(
    name='get_ferry_times',
    description="Returns ferry sailings for the specified origin, destination, and event date (YYYY-MM-DD)")
def get_ferry_times(origin: str, destination: str, event_time: str, ) -> dict:
    """
    Returns ferry sailings for the specified origin, destination, and event date (YYYY-MM-DD).
    Args:
        origin (str): Ferry terminal origin (e.g., 'Bainbridge Island')
        destination (str): Ferry terminal destination (e.g., 'Seattle')
        event_time (str): ISO8601 datetime string
    Returns:
        list: List of ferry departure dicts (same format as before)
    When to use:
        When you need to find ferry sailings for a specific route and event date.
    """
    route_key = f"{origin.strip().lower()}-{destination.strip().lower()}"
    
    if route_key not in schedule:
        print(f"No static schedule found for route: {route_key}")
        return {"ferry_times": [], "error": f"No static schedule found for route: {route_key}"}

    # Determine weekday/weekend
    day_type = get_day_type(event_time)

    return {"ferry_times": schedule[route_key].get(day_type, [])}


@mcp.tool(
    name='get_ferry_times_by_direction',
    description="Returns ferry sailings for a specific direction and event date")
def get_ferry_times_by_direction(event_time: str, direction: str) -> dict:
    """
    Returns ferry sailings for a specific direction and event date.
    Args:
        event_time (str): ISO8601 datetime string or 'YYYY-MM-DD'
        direction (str): Direction of travel (e.g., 'kitsap', 'king', 'east', 'west', etc.)
    Returns:
        dict: Mapping of route keys to list of sailings matching the direction
    """
    day_type = get_day_type(event_time)
    matches = {}
    for route_key, route_info in schedule.items():
        directions = route_info.get("direction", [])
        if direction in directions:
            sailings = route_info.get(day_type, [])
            if sailings:
                matches[route_key] = sailings

    return {"ferry_times_by_direction": matches}


@mcp.tool(
    name='geocode_county',
    description="Returns the county for a given address using the Google Maps Geocoding API.")
def geocode_county(address: str) -> dict:
    """
    Returns the county for a given address using the Google Maps Geocoding API.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": google_api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    try:
        components = data['results'][0]['address_components']
        county = None
        for comp in components:
            if 'administrative_area_level_2' in comp.get('types', []):
                county = comp.get('long_name')
                break
        if county:
            return {"county": county}
        else:
            return {"county": None, "error": "County not found in geocoding result."}
    except (KeyError, IndexError):
        return {"county": None, "error": f"Could not geocode county for: {address}"}

@mcp.prompt(
    name='get_to_seattle',
    description="Returns the best and second-best commute options (drive or ferry) to Seattle, minimizing wait at your destination and total driving time.")
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
    """

@mcp.prompt(
    name='get_to_kitsap',
    description="Returns the best and second-best commute options (drive or ferry) to Kitsap County, minimizing wait at your destination and total driving time.")
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
    """

@mcp.prompt(            
    name='get_there_by',
    description="Returns the best and second-best commute options (drive or ferry) to a location, minimizing wait at your destination and total driving time.")
def get_there_by(origin, location, event_time, buffer_minutes=10):
    """
    Returns the best and second-best commute options (drive or ferry) to a location, minimizing wait at your destination and total driving time.
    location: destination address
    event_time: 'YYYY-MM-DD HH:MM' (local time)
    buffer_minutes: extra time to allow for parking/walking at terminal (default 10)
    """
    return f"""
    1. The origin location will be in {origin}
    2. The event time will be {event_time} in local time
    3. The event address will be {location}
    4. The buffer minutes will be {buffer_minutes}
    5. Always find 2 options that get you there at least 15 minutes before the event time
    """


@mcp.prompt("how_to_plan_a_trip1")
def plan_a_trip2(origin, destination, event_time):
    
    return f"""
        Find multiple route options from {origin} to {destination}. 
        This may include ferry and car options.
        Always return a driving only option. 
        Using the origin's address {origin}, find the two nearest ferry terminals.
        Calculate the drive time from the origin address {origin} to each terminal.
        Find the sailing schedule for each terminal. 
        Determine the drive time from the destination terminal to the destination address {destination}.
        Calculate the total time for each option. 
        This total time should be the time it takes to get to the event location at least 15 minutes before the event time {event_time}.
        You may give up to two ferry options.
        All options must never get the user there later than 15 minutes before the event time of  {event_time}.
        Display the information in a table with columns for: 
            - Route	
            - Leave Origin
            - Drive to Terminal
            - Ferry Departure
            - Ferry Crossing
            - Arrive at Terminal time
            - Drive to Event
            - Approx. Arrival at Event
            - Total Travel Time
    """    

@mcp.prompt("how_to_plan_a_trip")
def plan_a_trip2(origin, destination, event_time, event_location):
    """
    Guides the user through planning a trip by collecting their origin, destination, and event time, 
    and evaluates both ferry and car commute options. 

    The function should:
    - Prompt for the user's origin, destination, and event time.
    - Explore possible routes using both ferry and driving options.
    - For ferry options:
        - Identify the three closest ferry terminals to the origin.
        - Find ferry schedules for each terminal.
        - Calculate driving time from the origin to each terminal.
        - Determine the best ferry and driving combinations to arrive at least 15 minutes before the event.
    - For car options:
        - Calculate total drive time directly from the origin to the destination.
    - Present the best alternatives for the user's commute, considering total travel time and minimizing wait.
    """
    return """
    1. You should ask for where their origin is
    2. You should ask for where their destination is
    3. You should ask for when the event is
    4. You should explore options for getting there by ferry and by car
    5. For Ferry: 
        1. You should determine the distances between the origin and the 3 nearest ferry terminals
        2. Then find the ferry times for each terminal
        3. Determine how long it would take to drive to each origin terminal from the origin location. Factor that into the total time for each option.
        4. Also determine how long it would take to drive from each destination ferry terminal to the event location. Factor that into the total time for each option as well.
        5. Only recommend ferry options that have a combined drive time with the ferry time that will get the user to the destination at least 15 minutes before the event time.
        6. For ferries heading to Seattle, always consider the Southworth Ferry as an option, as Fauntleroy is in Seattle and a valid commuting option to drive to downtown Seattle.
        7. The Southworth ferry goes to Fauntleroy (West Seattle), not downtown Seattle. If your destination is downtown, you will need to drive from Fauntleroy.
    6. For Car: 
        1. You should find the drive time between the origin and destination
        2. Only recommend car options that will get the user to the destination at least 15 minutes before the event time.
    7. Return both the option for car and ferry options with the least amount of drive time.
    """    

if __name__ == "__main__":
    mcp.run()