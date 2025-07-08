import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from google_maps_server import get_drive_time, FERRY_TERMINAL_ADDRESSES
from wsdot_ferry_server import get_ferry_times

DEFAULT_ORIGIN = "102 Shamrock Lane, Port Orchard, WA 98366"
BUFFER_MINUTES = 10
PACIFIC = ZoneInfo("America/Los_Angeles")

# Kitsap to Seattle routes: (origin terminal, destination terminal)
KITSAP_TO_SEATTLE_ROUTES = [
    ("kingston", "edmonds"),
    ("bainbridge island", "seattle"),
    ("bremerton", "seattle"),
    ("southworth", "fauntleroy"),
]

def next_seattle_ferries_with_drive(origin=DEFAULT_ORIGIN, event_time=None, buffer_minutes=BUFFER_MINUTES):
    """
    For each Kitsap->Seattle route, returns the soonest ferry you can catch factoring in drive time + buffer.
    Returns dict: route -> ferry dict or None
    """
    if event_time is None:
        now = datetime.now(PACIFIC)
        event_time = now.strftime("%Y-%m-%d")
    else:
        now = datetime.now(PACIFIC)
    results = {}
    for kit_term, sea_term in KITSAP_TO_SEATTLE_ROUTES:
        terminal_addr = FERRY_TERMINAL_ADDRESSES[kit_term]
        try:
            drive_min = get_drive_time(origin, terminal_addr)
            sailings = get_ferry_times(kit_term.title(), sea_term.title(), event_time)
            # Find soonest sailing you can make
            for sailing in sailings:
                dep_time = datetime.strptime(sailing['time'], '%Y-%m-%d %I:%M %p').replace(tzinfo=PACIFIC)
                min_depart = now + timedelta(minutes=drive_min + buffer_minutes)
                if dep_time > min_depart:
                    results[f"{kit_term}_to_{sea_term}"] = {
                        **sailing,
                        "drive_minutes": drive_min,
                        "buffer_minutes": buffer_minutes,
                        "must_leave_by": (dep_time - timedelta(minutes=drive_min + buffer_minutes)).strftime('%Y-%m-%d %I:%M %p'),
                    }
                    break
            else:
                results[f"{kit_term}_to_{sea_term}"] = None
        except Exception as e:
            results[f"{kit_term}_to_{sea_term}"] = {"error": str(e)}
    return results

def best_route_to_event(event_time_str, event_address, origin=DEFAULT_ORIGIN, buffer_minutes=BUFFER_MINUTES):
    """
    Returns the best route (direct drive or ferry) to reach event_address by event_time_str (format 'YYYY-MM-DD HH:MM'),
    prioritizing least waiting at the destination, then shortest total driving.
    """
    from datetime import datetime
    event_time = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=PACIFIC)
    candidates = []
    # Option 1: Direct drive (use arrival_time for traffic-aware estimate)
    drive_direct = get_drive_time(origin, event_address, arrival_time=event_time)
    leave_by_drive = event_time - timedelta(minutes=drive_direct)
    arrive_drive = leave_by_drive + timedelta(minutes=drive_direct)
    wait_drive = (event_time - arrive_drive).total_seconds() / 60
    if wait_drive >= 0:
        candidates.append({
            "mode": "drive",
            "arrive": arrive_drive.strftime('%Y-%m-%d %I:%M %p'),
            "leave_by": leave_by_drive.strftime('%Y-%m-%d %I:%M %p'),
            "total_drive_minutes": drive_direct,
            "wait_minutes": int(wait_drive),
            "details": f"Drive directly from {origin} to {event_address}",
        })
    # Option 2: Ferry routes
    for kit_term, sea_term in KITSAP_TO_SEATTLE_ROUTES:
        kit_addr = FERRY_TERMINAL_ADDRESSES[kit_term]
        sea_addr = FERRY_TERMINAL_ADDRESSES[sea_term]
        try:
            # For each sailing, compute when you'd need to leave to catch it
            sailings = get_ferry_times(kit_term.title(), sea_term.title(), event_time_str.split()[0])
            for sailing in sailings:
                dep_time = datetime.strptime(sailing['time'], '%Y-%m-%d %I:%M %p').replace(tzinfo=PACIFIC)
                eta_time = sailing.get('estimated_arrival_time')
                if not eta_time:
                    continue
                arr_time = datetime.strptime(eta_time, '%Y-%m-%d %I:%M %p').replace(tzinfo=PACIFIC)
                # Only consider ferries that arrive before event_time
                if arr_time > event_time:
                    continue
                # Calculate when you must leave your house to make the ferry
                must_leave_by = dep_time - timedelta(minutes=buffer_minutes)
                drive_to_terminal = get_drive_time(origin, kit_addr, arrival_time=dep_time - timedelta(minutes=buffer_minutes))
                # If you can't make it, skip
                if dep_time < (datetime.now(PACIFIC) + timedelta(minutes=drive_to_terminal + buffer_minutes)):
                    continue
                # Drive from Seattle-side terminal to event, aiming to arrive at event_time
                drive_from_terminal = get_drive_time(sea_addr, event_address, arrival_time=event_time)
                total_drive = drive_to_terminal + drive_from_terminal
                # Arrival at event is ferry arrival + drive from terminal
                final_arrive = arr_time + timedelta(minutes=drive_from_terminal)
                wait_minutes = (event_time - final_arrive).total_seconds() / 60
                if wait_minutes < 0:
                    continue
                candidates.append({
                    "mode": "ferry",
                    "route": f"{kit_term}_to_{sea_term}",
                    "ferry_depart": sailing['time'],
                    "ferry_arrive": eta_time,
                    "arrive": final_arrive.strftime('%Y-%m-%d %I:%M %p'),
                    "leave_by": (dep_time - timedelta(minutes=drive_to_terminal + buffer_minutes)).strftime('%Y-%m-%d %I:%M %p'),
                    "drive_to_terminal": drive_to_terminal,
                    "drive_from_terminal": drive_from_terminal,
                    "buffer": buffer_minutes,
                    "total_drive_minutes": total_drive,
                    "wait_minutes": int(wait_minutes),
                    "details": f"Drive to {kit_term.title()} ({kit_addr}), take {kit_term.title()}->{sea_term.title()} ferry, then drive to event."
                })
        except Exception:
            continue
    # Pick top two candidates
    if not candidates:
        return {"error": "No valid route found"}
    candidates.sort(key=lambda x: (x['wait_minutes'], x['total_drive_minutes']))
    best = candidates[0]
    second_best = candidates[1] if len(candidates) > 1 else None
    return {"best": best, "second_best": second_best}

if __name__ == "__main__":
    # Example: event at 6pm at 3rd and Pine, Seattle
    event_time_str = "2025-07-07 18:00"
    event_address = "3rd and Pine, Seattle, WA"
    result = best_route_to_event(event_time_str, event_address)
    print("Best route to event:")
    for k, v in result['best'].items():
        print(f"  {k}: {v}")
    if result['second_best']:
        print("\nSecond best option:")
        for k, v in result['second_best'].items():
            print(f"  {k}: {v}")
