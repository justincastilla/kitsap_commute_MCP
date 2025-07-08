# MCP server for Google Maps Directions API
import os
import requests

# Table of ferry terminal addresses (never change)
FERRY_TERMINAL_ADDRESSES = {
    "kingston": "11264 State Route 104, Kingston, WA 98346",
    "bainbridge island": "270 Olympic Dr SE, Bainbridge Island, WA 98110",
    "bremerton": "211 1st St, Bremerton, WA 98337",
    "southworth": "11864 SE Sedgwick Rd, Port Orchard, WA 98367",
    "edmonds": "199 Sunset Ave S, Edmonds, WA 98020",
    "fauntleroy": "4829 SW Barton St, Seattle, WA 98136",
    "seattle": "801 Alaskan Way, Seattle, WA 98104",
}

DEFAULT_ORIGIN = "102 Shamrock Lane, Port Orchard, WA 98366"

def get_drive_time(origin, destination, departure_time=None, arrival_time=None):
    """
    Returns the drive time in minutes between origin and destination using Google Maps Directions API.
    Optionally specify departure_time or arrival_time (Python datetime, in local time). If neither is given, uses now.
    """
    import time
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        raise Exception("GOOGLE_MAPS_API_KEY environment variable not set")
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": origin, "destination": destination, "key": api_key}
    if arrival_time:
        if hasattr(arrival_time, 'timestamp'):
            params['arrival_time'] = int(arrival_time.timestamp())
        else:
            params['arrival_time'] = int(arrival_time)
    elif departure_time:
        if hasattr(departure_time, 'timestamp'):
            params['departure_time'] = int(departure_time.timestamp())
        else:
            params['departure_time'] = int(departure_time)
    else:
        params['departure_time'] = int(time.time())
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        raise Exception(f"Google Maps API error: {resp.status_code} {resp.text}")
    data = resp.json()
    if data.get("status") != "OK" or not data.get("routes"):
        raise Exception(f"Google Maps API error: {data.get('status')} {data.get('error_message', '')}")
    try:
        duration_sec = data["routes"][0]["legs"][0]["duration"]["value"]
        return int(round(duration_sec / 60))  # minutes
    except Exception:
        raise Exception("Could not parse drive time from Google Maps API response")
