#!/usr/bin/env python3
"""
Test script for the Ferry API Client

This script demonstrates how to use the FerryAPIClient to fetch and cache
ferry data from the WSDOT APIs.
"""

import os
from ferry_api import FerryAPIClient


def test_basic_functionality():
    """Test basic API functionality"""
    print("Testing Ferry API Client...")
    print("=" * 60)

    # Check if API key is available
    api_key = os.getenv('WSDOT_API_KEY')
    if not api_key:
        print("\nWARNING: WSDOT_API_KEY environment variable not set.")
        print("Set it to test the API client:")
        print("  export WSDOT_API_KEY='your-api-key'")
        return False

    try:
        # Initialize client
        client = FerryAPIClient()
        print(f"✓ Client initialized")
        print(f"✓ Cache directory: {client.cache_dir}")

        # Test terminal basics (small endpoint)
        print("\nFetching terminal basics...")
        terminals = client.get_terminal_basics()
        print(f"✓ Retrieved {len(terminals)} terminals")

        # Show sample terminal
        if terminals:
            sample = terminals[0]
            print(f"\nSample terminal:")
            for key, value in sample.items():
                print(f"  {key}: {value}")

        # Test vessel basics
        print("\nFetching vessel basics...")
        vessels = client.get_vessel_basics()
        print(f"✓ Retrieved {len(vessels)} vessels")

        # Show sample vessel
        if vessels:
            sample = vessels[0]
            print(f"\nSample vessel:")
            for key, value in sample.items():
                print(f"  {key}: {value}")

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_usage_examples():
    """Show usage examples"""
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES")
    print("=" * 60)

    examples = """
# Basic usage - fetch and cache terminal data
from ferry_api import FerryAPIClient

client = FerryAPIClient()

# Get terminal information
terminals = client.get_terminal_basics()        # Basic info
locations = client.get_terminal_locations()      # Detailed locations
bulletins = client.get_terminal_bulletins()      # Current bulletins
conditions = client.get_terminal_conditions()    # Real-time conditions

# Get vessel information
vessels = client.get_vessel_basics()            # Basic info
vessel_locs = client.get_vessel_locations()     # Current locations
vessel_stats = client.get_vessel_stats()        # Specifications
accommodations = client.get_vessel_accommodations()  # Amenities

# Get schedule information
date_range = client.get_schedule_date_range()   # Valid date range
routes = client.get_routes()                    # All routes
schedule = client.get_route_schedules(route_id=1, date='2024-12-01')

# Get fare information
fares = client.get_fares()

# Fetch all static data at once
all_data = client.fetch_all_static_data()

# Fetch current real-time data
current = client.fetch_current_conditions()

# Clear cache
client.clear_cache('vessel_*.json')  # Clear vessel cache
client.clear_cache()                 # Clear all cache

# Disable caching for specific calls
real_time_locs = client.get_vessel_locations(cache=False)
"""

    print(examples)


if __name__ == '__main__':
    success = test_basic_functionality()

    if success:
        show_usage_examples()
    else:
        print("\nTo run tests, set your WSDOT API key:")
        print("  export WSDOT_API_KEY='your-api-key'")
        show_usage_examples()
