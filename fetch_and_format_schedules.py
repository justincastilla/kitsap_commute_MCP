#!/usr/bin/env python3
"""
Fetch and format ferry schedules from WSDOT API

This script fetches schedule data and outputs it in the MCP server format.
Run this script locally where you have direct API access.
"""

import requests
import json
from datetime import datetime, timedelta


# API configuration
API_KEY = '57b61dc1-0a98-4fe8-8b51-aab842744898'
BASE_URL = 'https://wsdot.wa.gov/Ferries/API/Schedule/rest'

# Route configurations with crossing times and directions
ROUTE_CONFIG = {
    'bainbridge island-seattle': {
        'direction': ['east', 'king', 'seattle'],
        'crossing_time': 35,
        'terminal_ids': (3, 7)  # Bainbridge, Seattle
    },
    'seattle-bainbridge island': {
        'direction': ['west', 'kitsap', 'peninsula'],
        'crossing_time': 35,
        'terminal_ids': (7, 3)  # Seattle, Bainbridge
    },
    'bremerton-seattle': {
        'direction': ['east', 'king', 'seattle'],
        'crossing_time': 60,
        'terminal_ids': (4, 7)  # Bremerton, Seattle
    },
    'seattle-bremerton': {
        'direction': ['west', 'peninsula', 'bremerton'],
        'crossing_time': 60,
        'terminal_ids': (7, 4)  # Seattle, Bremerton
    },
    'kingston-edmonds': {
        'direction': ['east', 'snohomish', 'seattle'],
        'crossing_time': 30,
        'terminal_ids': (14, 8)  # Kingston, Edmonds
    },
    'edmonds-kingston': {
        'direction': ['west', 'kitsap', 'peninsula'],
        'crossing_time': 30,
        'terminal_ids': (8, 14)  # Edmonds, Kingston
    },
    'fauntleroy-southworth': {
        'direction': ['west', 'kitsap', 'peninsula'],
        'crossing_time': 35,
        'terminal_ids': (9, 11)  # Fauntleroy, Southworth
    },
    'southworth-fauntleroy': {
        'direction': ['east', 'king', 'seattle'],
        'crossing_time': 35,
        'terminal_ids': (11, 9)  # Southworth, Fauntleroy
    },
}


def fetch_active_seasons():
    """Fetch active schedule seasons"""
    url = f'{BASE_URL}/activeseasons'
    params = {'apiaccesscode': API_KEY}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching active seasons: {e}")
        return None


def fetch_schedule_for_date(date_str):
    """Fetch schedule for a specific date"""
    url = f'{BASE_URL}/schedule/today'  # Try this endpoint first
    params = {'apiaccesscode': API_KEY}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching schedule: {e}")
        return None


def convert_time_to_12hr(time_24hr):
    """Convert 24-hour time to 12-hour AM/PM format"""
    try:
        if 'T' in time_24hr:
            # ISO datetime format
            dt = datetime.fromisoformat(time_24hr.replace('Z', '+00:00'))
            return dt.strftime('%I:%M %p').lstrip('0')
        else:
            # HH:MM format
            hour, minute = map(int, time_24hr.split(':'))
            dt = datetime(2000, 1, 1, hour, minute)
            return dt.strftime('%I:%M %p').lstrip('0')
    except:
        return time_24hr


def format_sailing(sailing_data, route_config):
    """Format a single sailing entry"""
    formatted = {
        'time': convert_time_to_12hr(sailing_data.get('DepartingTime', '')),
        'annotations': sailing_data.get('Annotations', []) or [],
        'crossing_time': route_config['crossing_time']
    }

    # Add direction for eastbound routes
    if 'east' in route_config['direction']:
        formatted['direction'] = 'east'

    return formatted


def main():
    """Main function to fetch and format ferry schedules"""

    print("=" * 70)
    print("Ferry Schedule Fetcher")
    print("=" * 70)

    # Step 1: Fetch active seasons
    print("\nStep 1: Fetching active seasons...")
    seasons = fetch_active_seasons()

    if seasons:
        print(f"✓ Found {len(seasons)} active seasons")
        for season in seasons:
            print(f"  - Season ID: {season.get('SeasonID')}")
            print(f"    Date: {season.get('SeasonStart')} to {season.get('SeasonEnd')}")
    else:
        print("✗ Could not fetch seasons")
        print("\nPlease run this script from a location with API access.")
        print("You mentioned the API works in your browser, so run it there.")
        return

    # Step 2: Try different endpoints to fetch schedule data
    print("\nStep 2: Fetching schedule data...")
    print("(This is where we need to find the right endpoint)")

    # Try various endpoints
    test_endpoints = [
        f'{BASE_URL}/schedule/today',
        f'{BASE_URL}/routes',
        f'{BASE_URL}/availabledates',
    ]

    for endpoint in test_endpoints:
        print(f"\nTrying: {endpoint}")
        try:
            resp = requests.get(endpoint, params={'apiaccesscode': API_KEY}, timeout=15)
            print(f"  Status: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"  ✓ SUCCESS! Got data")
                print(f"  Type: {type(data)}")
                if isinstance(data, list):
                    print(f"  Count: {len(data)}")
                    if data:
                        print(f"  Sample keys: {list(data[0].keys())[:5]}")
                elif isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())[:5]}")
            else:
                print(f"  ✗ Failed: {resp.text[:100]}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("""
Since the API has access restrictions from this environment, please:

1. Run this script on your local machine where the API works:
   python fetch_and_format_schedules.py

2. Or manually fetch the data and I'll help format it:
   - Visit: https://wsdot.wa.gov/Ferries/API/Schedule/rest/routes?apiaccesscode=57b61dc1-0a98-4fe8-8b51-aab842744898
   - Copy the JSON response
   - Paste it here and I'll format it

3. Alternative: Use the web schedule scraper approach:
   - Scrape https://wsdot.wa.gov/ferries/schedule/
   - Convert to JSON format

The current static_ferry_schedules.json is already in the correct format.
If you get API data, I can help convert it to match that format.
    """)


if __name__ == '__main__':
    main()
