#!/usr/bin/env python3
"""
Update Ferry Schedules from WSDOT API

This script fetches current ferry schedule data from the WSDOT API
and converts it to the format used by the MCP server.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from ferry_api import FerryAPIClient


# Direction mappings for routes
ROUTE_DIRECTIONS = {
    'bainbridge island-seattle': ['east', 'king', 'seattle'],
    'seattle-bainbridge island': ['west', 'kitsap', 'peninsula'],
    'bremerton-seattle': ['east', 'king', 'seattle'],
    'seattle-bremerton': ['west', 'peninsula', 'bremerton'],
    'kingston-edmonds': ['east', 'snohomish', 'seattle'],
    'edmonds-kingston': ['west', 'kitsap', 'peninsula'],
    'fauntleroy-southworth': ['west', 'kitsap', 'peninsula'],
    'southworth-fauntleroy': ['east', 'king', 'seattle'],
    'fauntleroy-vashon': ['south', 'vashon'],
    'vashon-fauntleroy': ['north', 'seattle'],
    'southworth-vashon': ['south', 'vashon'],
    'vashon-southworth': ['north', 'kitsap'],
    'mukilteo-clinton': ['west', 'whidbey'],
    'clinton-mukilteo': ['east', 'snohomish', 'everett'],
    'port townsend-coupeville': ['west', 'peninsula'],
    'coupeville-port townsend': ['east', 'whidbey'],
    'anacortes-san juan islands': ['west', 'islands'],
    'san juan islands-anacortes': ['east', 'anacortes'],
}

# Estimated crossing times (in minutes) for each route
CROSSING_TIMES = {
    'bainbridge island-seattle': 35,
    'seattle-bainbridge island': 35,
    'bremerton-seattle': 60,
    'seattle-bremerton': 60,
    'kingston-edmonds': 30,
    'edmonds-kingston': 30,
    'fauntleroy-southworth': 35,
    'southworth-fauntleroy': 35,
    'fauntleroy-vashon': 15,
    'vashon-fauntleroy': 15,
    'southworth-vashon': 10,
    'vashon-southworth': 10,
    'mukilteo-clinton': 20,
    'clinton-mukilteo': 20,
    'port townsend-coupeville': 35,
    'coupeville-port townsend': 35,
}


def normalize_terminal_name(name: str) -> str:
    """Normalize terminal names to lowercase for consistency"""
    return name.strip().lower()


def create_route_key(departing: str, arriving: str) -> str:
    """Create a route key from terminal names"""
    dep = normalize_terminal_name(departing)
    arr = normalize_terminal_name(arriving)
    return f"{dep}-{arr}"


def convert_time_format(time_str: str) -> str:
    """
    Convert time from API format to display format (12-hour with AM/PM)

    Args:
        time_str: Time string from API (e.g., "04:45" or "16:45")

    Returns:
        Formatted time string (e.g., "04:45 AM" or "04:45 PM")
    """
    try:
        # Parse 24-hour time
        if 'T' in time_str:
            # Handle ISO datetime format
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            time_obj = dt.time()
        else:
            # Handle HH:MM format
            hour, minute = map(int, time_str.split(':'))
            time_obj = datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time()

        # Format as 12-hour time with AM/PM
        return time_obj.strftime("%I:%M %p").lstrip('0')
    except Exception as e:
        print(f"Warning: Could not parse time '{time_str}': {e}")
        return time_str


def extract_sailing_times(schedule_data: dict, route_key: str) -> dict:
    """
    Extract sailing times from API schedule data

    Args:
        schedule_data: Raw schedule data from API
        route_key: Route identifier key

    Returns:
        Dictionary with weekday and weekend sailing times
    """
    result = {
        'weekday': [],
        'weekend': []
    }

    # Get crossing time for this route
    crossing_time = CROSSING_TIMES.get(route_key, 30)

    # Get direction info
    directions = ROUTE_DIRECTIONS.get(route_key, [])
    primary_direction = directions[0] if directions else None

    try:
        # Parse the schedule data structure
        # The API returns different formats, so we need to handle various cases

        if isinstance(schedule_data, list):
            # List of schedules
            for schedule in schedule_data:
                process_schedule_item(schedule, result, crossing_time, primary_direction)
        elif isinstance(schedule_data, dict):
            # Single schedule or nested structure
            if 'Times' in schedule_data:
                times_data = schedule_data['Times']
                if isinstance(times_data, list):
                    for time_item in times_data:
                        process_time_item(time_item, result, crossing_time, primary_direction)
            elif 'Date' in schedule_data and 'Sailings' in schedule_data:
                # Schedule with date and sailings
                sailings = schedule_data['Sailings']
                for sailing in sailings:
                    process_sailing(sailing, result, crossing_time, primary_direction, schedule_data.get('Date'))

    except Exception as e:
        print(f"Warning: Error extracting times for {route_key}: {e}")

    return result


def process_schedule_item(item: dict, result: dict, crossing_time: int, direction: str):
    """Process a single schedule item"""
    if 'DepartingTime' in item:
        time_str = convert_time_format(item['DepartingTime'])
        annotations = item.get('Annotations', []) or []

        # Determine if weekday or weekend based on date or flags
        schedule_type = 'weekday'  # Default to weekday
        if 'IsWeekend' in item and item['IsWeekend']:
            schedule_type = 'weekend'

        sailing_info = {
            'time': time_str,
            'annotations': annotations if isinstance(annotations, list) else [],
            'crossing_time': crossing_time
        }

        if direction:
            sailing_info['direction'] = direction

        result[schedule_type].append(sailing_info)


def process_time_item(item: dict, result: dict, crossing_time: int, direction: str):
    """Process a time item from schedule"""
    if 'DepartingTime' in item or 'Time' in item:
        time_str = item.get('DepartingTime') or item.get('Time')
        time_str = convert_time_format(time_str)

        annotations = item.get('Annotations', []) or []

        sailing_info = {
            'time': time_str,
            'annotations': annotations if isinstance(annotations, list) else [],
            'crossing_time': crossing_time
        }

        if direction:
            sailing_info['direction'] = direction

        # Default to weekday
        result['weekday'].append(sailing_info)


def process_sailing(sailing: dict, result: dict, crossing_time: int, direction: str, date: str):
    """Process a sailing entry"""
    if 'DepartingTime' in sailing:
        time_str = convert_time_format(sailing['DepartingTime'])
        annotations = sailing.get('Annotations', []) or []

        # Determine weekday/weekend from date
        schedule_type = 'weekday'
        if date:
            try:
                dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    schedule_type = 'weekend'
            except:
                pass

        sailing_info = {
            'time': time_str,
            'annotations': annotations if isinstance(annotations, list) else [],
            'crossing_time': crossing_time
        }

        if direction:
            sailing_info['direction'] = direction

        result[schedule_type].append(sailing_info)


def fetch_and_update_schedules():
    """Fetch current schedules from API and update the static file"""

    print("=" * 70)
    print("Ferry Schedule Updater")
    print("=" * 70)

    # Initialize API client
    try:
        client = FerryAPIClient()
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nPlease set your WSDOT_API_KEY environment variable:")
        print("  export WSDOT_API_KEY='your-api-key'")
        return False

    print("\nStep 1: Fetching routes from API...")
    try:
        routes_data = client.get_routes()
        print(f"✓ Found {len(routes_data)} routes")
    except Exception as e:
        print(f"✗ Error fetching routes: {e}")
        return False

    print("\nStep 2: Fetching schedule date range...")
    try:
        date_range = client.get_schedule_date_range()
        print(f"✓ Schedule valid from {date_range.get('StartDate')} to {date_range.get('EndDate')}")
    except Exception as e:
        print(f"⚠ Warning: Could not fetch date range: {e}")

    # Build schedule dictionary
    schedules = {}

    print("\nStep 3: Processing routes and fetching schedules...")
    for route in routes_data:
        try:
            route_id = route.get('RouteID')
            route_abbrev = route.get('RouteAbbrev', '')
            departing = route.get('DepartingTerminalName', '')
            arriving = route.get('ArrivingTerminalName', '')

            if not route_id or not departing or not arriving:
                continue

            route_key = create_route_key(departing, arriving)

            print(f"\n  Processing: {route_key} (Route {route_id})")

            # Fetch schedule for this route
            try:
                schedule_data = client.get_route_schedules(route_id)

                # Extract sailing times
                sailing_times = extract_sailing_times(schedule_data, route_key)

                # Get direction info
                directions = ROUTE_DIRECTIONS.get(route_key, [])

                # Create schedule entry
                schedules[route_key] = {
                    'direction': directions,
                    'weekday': sailing_times.get('weekday', []),
                    'weekend': sailing_times.get('weekend', [])
                }

                weekday_count = len(sailing_times.get('weekday', []))
                weekend_count = len(sailing_times.get('weekend', []))
                print(f"    ✓ Weekday sailings: {weekday_count}")
                print(f"    ✓ Weekend sailings: {weekend_count}")

            except Exception as e:
                print(f"    ✗ Error fetching schedule: {e}")
                continue

        except Exception as e:
            print(f"  ✗ Error processing route: {e}")
            continue

    # If we got no schedules from API, return the existing static data
    if not schedules:
        print("\n⚠ Warning: No schedules fetched from API")
        print("This could be due to API access issues or data format changes")
        print("Keeping existing static schedule file")
        return False

    # Save to file
    output_file = Path(__file__).parent / 'data' / 'static_ferry_schedules.json'
    backup_file = Path(__file__).parent / 'data' / f'static_ferry_schedules_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    print(f"\nStep 4: Saving schedules...")

    # Create backup of existing file
    if output_file.exists():
        import shutil
        shutil.copy(output_file, backup_file)
        print(f"  ✓ Backup created: {backup_file.name}")

    # Save new schedules
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schedules, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Updated schedules saved to: {output_file.name}")
    print(f"  ✓ Total routes: {len(schedules)}")

    print("\n" + "=" * 70)
    print("Schedule update complete!")
    print("=" * 70)

    return True


def main():
    """Main entry point"""
    import sys

    success = fetch_and_update_schedules()
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
