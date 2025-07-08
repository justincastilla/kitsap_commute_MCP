import os
import requests

def get_ferry_times(origin, destination, event_time):
    """
    Minimal MCP server function to fetch WSDOT ferry schedules.
    Args:
        origin (str): Ferry terminal origin (e.g., 'Bainbridge Island')
        destination (str): Ferry terminal destination (e.g., 'Seattle')
        event_time (str): ISO8601 datetime string (not used in minimal version)
    Returns:
        list: List of ferry departure times as strings
    """
    api_key = os.getenv('WSDOT_API_KEY')
    if not api_key:
        raise Exception("WSDOT_API_KEY environment variable not set")

    # Hardcoded terminal IDs (from WSDOT docs)
    TERMINAL_IDS = {
        'anacortes': 1,
        'bainbridge island': 3,
        'bremerton': 4,
        'clinton': 5,
        'coupeville': 11,
        'edmonds': 8,
        'fauntleroy': 9,
        'friday harbor': 10,
        'kingston': 12,
        'lopez island': 13,
        'mukilteo': 14,
        'orcas island': 15,
        'point defiance': 16,
        'port townsend': 17,
        'seattle': 7,
        'shaw island': 18,
        'sidney b.c.': 19,
        'southworth': 20,
        'tahlequah': 21,
        'vashon island': 22,
    }
    dep_id = TERMINAL_IDS.get(origin.lower())
    arr_id = TERMINAL_IDS.get(destination.lower())
    if not dep_id or not arr_id:
        raise ValueError(f"Unknown terminal: {origin} or {destination}")

    # /scheduletoday/{DepartingTerminalID}/{ArrivingTerminalID}/0 (all times)
    url = f'https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/scheduletoday/{dep_id}/{arr_id}/false'
    params = {'apiaccesscode': api_key}
    resp = requests.get(url, params=params)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error response for {origin} → {destination}: {resp.text}")
        raise
    data = resp.json()
    # Each sailing is an object with 'DepartingTime' and 'ArrivingTime'
    sailings = []
    # /scheduletoday: not used, fallback to /schedule below
    # Try /schedule/{TripDate}/{DepartingTerminalID}/{ArrivingTerminalID}
    from datetime import datetime, timezone, timedelta
    import re
    today = datetime.now().strftime('%Y-%m-%d')
    url2 = f'https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/schedule/{today}/{dep_id}/{arr_id}'
    resp2 = requests.get(url2, params=params)
    try:
        resp2.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error response for {origin} → {destination} (schedule endpoint): {resp2.text}")
        raise
    data2 = resp2.json()
    combos = data2.get('TerminalCombos', [])
    dotnet_re = re.compile(r"/Date\((\d+)([-+]\d{4})?\)/")
    if combos and 'Times' in combos[0]:
        annotations = combos[0].get('Annotations', [])
        from zoneinfo import ZoneInfo
        pacific = ZoneInfo("America/Los_Angeles")
        for t in combos[0]['Times']:
            # Parse time
            match = dotnet_re.match(t['DepartingTime'])
            if match:
                millis = int(match.group(1))
                dt_utc = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=millis)
                dt_pacific = dt_utc.astimezone(pacific)
                time_str = dt_pacific.strftime('%Y-%m-%d %I:%M %p')
            else:
                time_str = t['DepartingTime']
                dt_pacific = None
            # Vessel
            vessel = t.get('VesselName', '')
            # Annotations and crossing time
            annots = []
            crossing_time = None
            if 'AnnotationIndexes' in t:
                for i in t['AnnotationIndexes']:
                    annot = annotations[i]
                    # Look for 'crossing time XX minutes.'
                    import re
                    match = re.search(r'crossing time (\d+) minutes?\.', annot)
                    if match:
                        crossing_time = int(match.group(1))
                        # Remove crossing time from annotation text
                        annot = re.sub(r' ?-? ?crossing time \d+ minutes?\.', '', annot).strip()
                        if annot.endswith('-'):
                            annot = annot[:-1].strip()
                    if annot:
                        annots.append(annot)
            # Estimated arrival time
            estimated_arrival_time = None
            try:
                if dt_pacific:
                    dep_dt = dt_pacific
                else:
                    dep_dt = datetime.strptime(time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=pacific)
                if crossing_time:
                    arr_dt = dep_dt + timedelta(minutes=crossing_time)
                    estimated_arrival_time = arr_dt.strftime('%Y-%m-%d %I:%M %p')
            except Exception:
                pass
            # Set default crossing time for Southworth <-> Fauntleroy non-direct sailings
            is_sf = (
                (origin.lower() == 'southworth' and destination.lower() == 'fauntleroy') or
                (origin.lower() == 'fauntleroy' and destination.lower() == 'southworth')
            )
            if is_sf and crossing_time is None and not any('Direct route' in a for a in annots):
                crossing_time = 40
                # Update estimated arrival time
                try:
                    if dt_pacific:
                        dep_dt = dt_pacific
                    else:
                        dep_dt = datetime.strptime(time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=pacific)
                    estimated_arrival_time = (dep_dt + timedelta(minutes=crossing_time)).strftime('%Y-%m-%d %I:%M %p')
                except Exception:
                    estimated_arrival_time = None
            # Fallback crossing time table for major routes
            fallback_crossings = {
                ("kingston", "edmonds"): 30,
                ("edmonds", "kingston"): 30,
                ("bainbridge island", "seattle"): 35,
                ("seattle", "bainbridge island"): 35,
                ("bremerton", "seattle"): 50,
                ("seattle", "bremerton"): 50,
            }
            # Always apply fallback if crossing_time is still None
            key = (origin.lower(), destination.lower())
            if crossing_time is None and key in fallback_crossings:
                crossing_time = fallback_crossings[key]
            # Always recalculate ETA if crossing_time is set (not None)
            if crossing_time is not None:
                try:
                    if dt_pacific:
                        dep_dt = dt_pacific
                    else:
                        dep_dt = datetime.strptime(time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=pacific)
                    estimated_arrival_time = (dep_dt + timedelta(minutes=crossing_time)).strftime('%Y-%m-%d %I:%M %p')
                except Exception:
                    estimated_arrival_time = None
            sailings.append({
                'time': time_str,
                'vessel': vessel,
                'annotations': annots,
                'crossing_time': crossing_time,
                'estimated_arrival_time': estimated_arrival_time
            })
    if sailings:
        return sailings
    print(f"No sailings found for {origin} → {destination} using /schedule. Full response:")
    print(data2)
    return []
