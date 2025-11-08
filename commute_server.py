import json
import logging
import requests
import fastmcp
from config import WSDOT_API_KEY, GOOGLE_MAPS_API_KEY, DATA_DIR
from utilities import (
    get_schedule,
    get_day_type,
    to_epoch_seconds,
    parse_datetime,
    haversine,
)
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = fastmcp.FastMCP("commute-server")

# Load static data once at module level
schedule = get_schedule()

# Load ferry terminals once
terminals_path = DATA_DIR / "ferry_terminals.json"
with open(terminals_path, "r") as f:
    FERRY_TERMINALS = json.load(f)


@mcp.resource(
    uri="transit://ferries/schedules/{direction}",
    name="Ferry Schedules",
    description="Full or filtered ferry schedules from static_ferry_schedules.json. Optionally filter by direction",
)
def fetch_ferry_schedules(direction: str | None = None) -> dict:
    """
    Returns the full ferry schedule, or only routes matching the given direction (east, west, kitsap, king).
    """
    if direction is None:
        return {"schedules": schedule}
    direction = direction.lower()
    filtered = {
        route: info
        for route, info in schedule.items()
        if direction in [d.lower() for d in info.get("direction", [])]
    }
    return {"schedules": filtered}


@mcp.resource(
    uri="transit://ferries/terminals",
    name="Ferry Terminals",
    description="List of ferry terminals",
)
def fetch_terminals():
    """
    Fetches the list of ferry terminals from the WSDOT API.
    """
    url = "https://wsdot.wa.gov/Ferries/API/Terminals/rest/terminalbasics"
    params = {"apiaccesscode": WSDOT_API_KEY}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data


@mcp.tool(
    name="find_nearby_ferry_terminals",
    description="Finds the nearest ferry terminals to a given address using a static terminal list and Google Maps Geocoding API.",
)
def find_nearby_ferry_terminals(address: str, max_results: int = 3) -> dict:
    """
    Finds the nearest ferry terminals to a given address using a static terminal list and Google Maps Geocoding API.
    Returns a sorted list of the closest terminals with name, address, lat, lng, place_id, and distance_km.
    """
    # Geocode address
    geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
    geo_params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
    geo_resp = requests.get(geo_url, params=geo_params, timeout=10)
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()
    try:
        loc = geo_data["results"][0]["geometry"]["location"]
        addr_lat, addr_lng = loc["lat"], loc["lng"]
    except (KeyError, IndexError):
        return {"terminals": [], "error": f"Could not geocode address: {address}"}

    # Compute distances using module-level FERRY_TERMINALS
    results = []
    for t in FERRY_TERMINALS:
        try:
            t_lat = float(t["lat"])
            t_lng = float(t["lng"])
            dist = haversine(addr_lat, addr_lng, t_lat, t_lng)
            results.append(
                {
                    "name": t.get("display_name"),
                    "address": t.get("address"),
                    "lat": t_lat,
                    "lng": t_lng,
                    "place_id": t.get("place_id"),
                    "distance_km": round(dist, 2),
                    "city": t.get("city"),
                    "neighborhood": t.get("neighborhood"),
                    "county": t.get("county"),
                }
            )
        except Exception as e:
            logger.error(f"Error processing terminal: {e}", extra={"terminal": t})
            continue
    # Sort and limit
    results.sort(key=lambda x: x["distance_km"])
    return {"terminals": results[:max_results]}


@mcp.tool(
    name="drive_time",
    description="Returns drive time between origin and destination with mileage cost",
)
def drive_time_tool(
    origin: str,
    destination: str,
    departure_time: Optional[str] = None,
    arrival_time: Optional[str] = None,
) -> dict:
    """
    Returns drive time in minutes between origin and destination,
    optionally factoring in departure or arrival time (ISO 8601 string, local time).
    Also calculates mileage cost at $0.77 per mile.
    """
    dep = parse_datetime(departure_time)
    arr = parse_datetime(arrival_time)
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": origin, "destination": destination, "key": GOOGLE_MAPS_API_KEY}

    if arr is not None:
        params["arrival_time"] = to_epoch_seconds(arr)
    elif dep is not None:
        params["departure_time"] = to_epoch_seconds(dep)

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    try:
        leg = data["routes"][0]["legs"][0]

        # Extract time information
        minutes = int(leg["duration"]["value"] // 60)
        traffic = False
        minutes_in_traffic = None
        if "duration_in_traffic" in leg:
            minutes_in_traffic = int(leg["duration_in_traffic"]["value"] // 60)
            traffic = minutes_in_traffic > minutes

        # Extract distance information and calculate mileage cost
        distance_meters = leg["distance"]["value"]
        distance_miles = distance_meters * 0.000621371  # Convert meters to miles
        mileage_rate = 0.77  # $0.77 per mile
        mileage_cost = distance_miles * mileage_rate

        result = {
            "drive_minutes": minutes,
            "traffic": traffic,
            "distance_miles": round(distance_miles, 2),
            "distance_text": leg["distance"]["text"],
            "mileage_cost": round(mileage_cost, 2),
            "mileage_rate": mileage_rate,
            "cost_summary": f"${round(mileage_cost, 2)} ({round(distance_miles, 1)} miles @ ${mileage_rate}/mile)",
        }

        if minutes_in_traffic is not None:
            result["drive_minutes_in_traffic"] = minutes_in_traffic

        return result
    except (KeyError, IndexError):
        raise Exception(f"Could not extract drive time from response: {data}")


@mcp.tool(
    name="get_ferry_times",
    description="Returns ferry sailings for the specified origin, destination, and event date (YYYY-MM-DD)",
)
def get_ferry_times(
    origin: str,
    destination: str,
    event_time: str,
) -> dict:
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
        logger.warning(f"No static schedule found for route: {route_key}")
        return {
            "ferry_times": [],
            "error": f"No static schedule found for route: {route_key}",
        }

    # Determine weekday/weekend
    day_type = get_day_type(event_time)

    return {"ferry_times": schedule[route_key].get(day_type, [])}


@mcp.tool(
    name="ferry_cost",
    description="Returns ferry fare information for a specific route and travel date from WSDOT API, defaulting to driver mode.",
)
def ferry_cost(
    trip_date: str,
    departing_terminal: str,
    arriving_terminal: str,
    travel_mode: str = "drive",
    vehicle_size: str = "standard",
) -> dict:
    """
    Returns succinct ferry fare information for a specific route and travel date using WSDOT's official API.
    Defaults to driver mode with standard vehicle size for realistic commuter scenarios and one-way.

    Args:
        trip_date (str): Travel date in YYYY-MM-DD format (e.g., '2025-07-31')
        departing_terminal (str): Ferry terminal name for departure (e.g., "Southworth", "Bainbridge Island", "Seattle")
        arriving_terminal (str): Ferry terminal name for arrival (e.g., "Fauntleroy", "Seattle", "Kingston")
        travel_mode (str): Travel mode - "walk" for passenger only, "drive" for vehicle (default: "drive")
        vehicle_size (str): Vehicle size - "standard", "small", "motorcycle" (default: "standard")

    Returns:
        dict: Succinct ferry fare with route, cost, and description
        Example: {
            "trip_date": "2025-07-31",
            "route": "Southworth → Fauntleroy",
            "travel_mode": "drive",
            "fare_amount": 23.2,
            "fare_description": "Standard vehicle fare",
            "fare_name": "Vehicle Under 22' (standard veh) & Driver",
            "cost_summary": "$23.2 - Vehicle Under 22' (standard veh) & Driver"
        }

    Valid ferry terminals:
    - Seattle (downtown ferry terminal)
    - Bainbridge Island
    - Southworth (Kitsap Peninsula)
    - Fauntleroy (West Seattle)
    - Edmonds (Snohomish County)
    - Kingston (Kitsap Peninsula)
    - Bremerton (Kitsap Peninsula)
    - Point Defiance (Tacoma)
    - Tahlequah (Vashon Island)

    Common ferry routes:
    - Seattle ↔ Bainbridge Island
    - Southworth ↔ Fauntleroy
    - Edmonds ↔ Kingston
    - Point Defiance ↔ Tahlequah
    - Bremerton ↔ Seattle

    NOTE: Washington State Ferries pricing:
    - Eastbound (to mainland) = PAID
    - Westbound (to islands) = FREE
    Examples: Seattle→Bainbridge is FREE, Bainbridge→Seattle is PAID
    """
    # Terminal name to ID mapping
    terminal_mapping = {
        "seattle": 7,
        "bainbridge island": 3,
        "southworth": 20,
        "fauntleroy": 9,
        "edmonds": 8,
        "kingston": 12,
        "bremerton": 4,
        "point defiance": 16,
        "tahlequah": 21,
        "anacortes": 1,
        "friday harbor": 2,
        "orcas": 5,
        "shaw": 6,
        "lopez": 11,
        "sidney bc": 13,
    }

    # Convert terminal names to IDs
    departing_terminal_clean = departing_terminal.lower().strip()
    arriving_terminal_clean = arriving_terminal.lower().strip()

    departing_terminal_id = terminal_mapping.get(departing_terminal_clean)
    arriving_terminal_id = terminal_mapping.get(arriving_terminal_clean)

    # Validate terminal names
    if departing_terminal_id is None:
        available_terminals = ", ".join(terminal_mapping.keys())
        return {
            "error": f"Unknown departing terminal: '{departing_terminal}'. Available terminals: {available_terminals}",
            "trip_date": trip_date,
            "route": f"{departing_terminal} → {arriving_terminal}",
        }

    if arriving_terminal_id is None:
        available_terminals = ", ".join(terminal_mapping.keys())
        return {
            "error": f"Unknown arriving terminal: '{arriving_terminal}'. Available terminals: {available_terminals}",
            "trip_date": trip_date,
            "route": f"{departing_terminal} → {arriving_terminal}",
        }

    # Date should be in YYYY-MM-DD format
    api_date = trip_date

    # Use the farelineitems API endpoint for detailed fare information
    url = f"https://www.wsdot.wa.gov/ferries/api/fares/rest/farelineitems/{api_date}/{departing_terminal_id}/{arriving_terminal_id}/false"
    params = {"apiaccesscode": WSDOT_API_KEY}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        fare_data = resp.json()

        # Also get basic terminal combination info
        terminal_combo_url = f"https://www.wsdot.wa.gov/ferries/api/fares/rest/terminalcombo/{api_date}/{departing_terminal_id}/{arriving_terminal_id}"
        terminal_resp = requests.get(terminal_combo_url, params=params, timeout=10)
        terminal_data = None
        if terminal_resp.status_code == 200:
            terminal_data = terminal_resp.json()

        # Find recommended fare based on travel mode and vehicle size
        recommended_fare = None
        fare_description = ""

        if isinstance(fare_data, list):
            for fare_item in fare_data:
                fare_desc = fare_item.get("FareLineItem", "").lower()

                if travel_mode == "walk":
                    # Look for passenger fare
                    if "passenger" in fare_desc or (
                        "adult" in fare_desc and "vehicle" not in fare_desc
                    ):
                        recommended_fare = fare_item
                        fare_description = "Walk-on passenger fare"
                        break

                elif travel_mode == "drive":
                    # Look for vehicle fare based on size
                    if vehicle_size == "motorcycle" and "motorcycle" in fare_desc:
                        recommended_fare = fare_item
                        fare_description = "Motorcycle fare"
                        break
                    elif vehicle_size == "small" and (
                        "under 14" in fare_desc or "less than 168" in fare_desc
                    ):
                        recommended_fare = fare_item
                        fare_description = "Small vehicle fare"
                        break
                    elif vehicle_size == "standard" and (
                        "under 22" in fare_desc or "standard veh" in fare_desc
                    ):
                        recommended_fare = fare_item
                        fare_description = "Standard vehicle fare"
                        break

            # If no exact match found, fall back to reasonable defaults
            if not recommended_fare and fare_data:
                if travel_mode == "walk":
                    # Find any passenger fare (adult)
                    for fare_item in fare_data:
                        fare_desc = fare_item.get("FareLineItem", "").lower()
                        if "adult" in fare_desc and "vehicle" not in fare_desc:
                            recommended_fare = fare_item
                            fare_description = "Default passenger fare"
                            break
                elif travel_mode == "drive":
                    # Find any standard vehicle fare
                    for fare_item in fare_data:
                        fare_desc = fare_item.get("FareLineItem", "").lower()
                        if (
                            "under 22" in fare_desc or "standard veh" in fare_desc
                        ) and "driver" in fare_desc:
                            recommended_fare = fare_item
                            fare_description = "Default vehicle fare"
                            break

        # Extract essential fare information for succinct response
        if recommended_fare:
            fare_amount = recommended_fare.get("Amount", 0)
            fare_name = recommended_fare.get("FareLineItem", "")
        else:
            fare_amount = 0
            fare_name = "No fare found"

        # Get terminal names from terminal combo data if available
        departing_terminal_name = departing_terminal
        arriving_terminal_name = arriving_terminal
        if terminal_data:
            departing_terminal_name = terminal_data.get(
                "DepartingTerminalName", departing_terminal_name
            )
            arriving_terminal_name = terminal_data.get(
                "ArrivingTerminalName", arriving_terminal_name
            )

        # Enhanced cost summary with better free route explanation
        if fare_amount > 0:
            cost_summary = f"${fare_amount} - {fare_name}"
        else:
            # Explain why it's free (common WA ferry pattern)
            if any(
                keyword in departing_terminal.lower()
                for keyword in ["seattle", "edmonds", "mukilteo", "anacortes"]
            ):
                cost_summary = "FREE (mainland to island direction)"
                fare_description = fare_description or "Free westbound travel"
            else:
                cost_summary = "FREE"
                fare_description = fare_description or "No charge for this direction"

        # Create succinct result focusing on essential information
        result = {
            "trip_date": trip_date,
            "route": f"{departing_terminal_name} → {arriving_terminal_name}",
            "travel_mode": travel_mode,
            "fare_amount": fare_amount,
            "fare_description": fare_description,
            "fare_name": fare_name,
            "cost_summary": cost_summary,
        }

        return result

    except requests.RequestException as e:
        # Handle specific 400 errors for invalid routes
        error_msg = str(e)
        if "400 Client Error" in error_msg:
            return {
                "error": f"No direct ferry route available from {departing_terminal} to {arriving_terminal}",
                "trip_date": trip_date,
                "route": f"{departing_terminal} → {arriving_terminal}",
                "suggestion": "Common ferry routes: Seattle↔Bainbridge Island, Southworth↔Fauntleroy, Edmonds↔Kingston",
                "valid_terminals": "Seattle, Bainbridge Island, Southworth, Fauntleroy, Edmonds, Kingston, Bremerton, Point Defiance, Tahlequah",
            }
        else:
            return {
                "error": f"Failed to fetch ferry fare data: {str(e)}",
                "trip_date": trip_date,
                "route": f"{departing_terminal} → {arriving_terminal}",
            }
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse API response: {str(e)}",
            "trip_date": trip_date,
            "route": f"{departing_terminal} → {arriving_terminal}",
        }


@mcp.prompt("user_preferences")
def user_preferences():
    """
    User's commute planning preferences.
    Always reference these preferences when planning trips.
    """
    return """
    User Preferences for Trip Planning:
    - Always provide exactly 3 route options
    - One option MUST be driving-only (no ferry)
    - The other 2 options can be ferry + driving combinations
    - Arrival time: At least 15 minutes before the event
    - Display results in a table format with all timing details
    """


@mcp.prompt("how_to_plan_a_trip")
def plan_trip(origin: str = None, destination: str = None, event_time: str = None):
    """
    Guides the user through planning a trip by collecting their origin, destination, and event time,
    and evaluates both ferry and car commute options.

    The function should:
    - Prompt for the user's origin, destination, and event time (if not provided).
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
    # Build dynamic instructions based on provided parameters
    instructions = """
    IMPORTANT: First review the user_preferences prompt to understand user's route planning preferences.
    """

    if not origin:
        instructions += "\n    1. You should ask for where their origin is"
    else:
        instructions += f"\n    1. Origin is {origin}"

    if not destination:
        instructions += "\n    2. You should ask for where their destination is"
    else:
        instructions += f"\n    2. Destination is {destination}"

    if not event_time:
        instructions += "\n    3. You should ask for when the event is"
    else:
        instructions += f"\n    3. Event time is {event_time}"

    instructions += """
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
    7. Follow the user_preferences to determine how many route options to return and ensure one is driving-only.
    8. Display results in a table format with columns for:
        - Route
        - Leave Origin
        - Drive to Terminal (if applicable)
        - Ferry Departure (if applicable)
        - Ferry Crossing (if applicable)
        - Arrive at Terminal (if applicable)
        - Drive to Event
        - Approx. Arrival at Event
        - Total Travel Time
    """

    return instructions


if __name__ == "__main__":
    mcp.run()
