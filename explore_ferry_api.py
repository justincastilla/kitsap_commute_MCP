#!/usr/bin/env python3
"""
Ferry API Explorer

This script tests all available WSDOT Ferry API endpoints to see which ones
are accessible and what data they return.
"""

import os
import json
import requests
from datetime import datetime
from ferry_api import FerryAPIClient


def test_endpoint(name: str, url: str, api_key: str, params: dict = None) -> dict:
    """Test a single API endpoint"""
    if params is None:
        params = {}
    params['apiaccesscode'] = api_key

    try:
        resp = requests.get(url, params=params, timeout=15)

        if resp.status_code == 200:
            try:
                data = resp.json()
                return {
                    'name': name,
                    'status': 'success',
                    'code': 200,
                    'data_type': type(data).__name__,
                    'data_count': len(data) if isinstance(data, (list, dict)) else 1,
                    'sample': data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else str(data)[:100])
                }
            except json.JSONDecodeError:
                return {
                    'name': name,
                    'status': 'success_non_json',
                    'code': 200,
                    'content': resp.text[:200]
                }
        else:
            return {
                'name': name,
                'status': 'failed',
                'code': resp.status_code,
                'message': resp.text[:200]
            }
    except Exception as e:
        return {
            'name': name,
            'status': 'error',
            'message': str(e)
        }


def explore_api():
    """Explore all WSDOT Ferry API endpoints"""

    print("=" * 70)
    print("WSDOT Ferry API Explorer")
    print("=" * 70)

    api_key = os.getenv('WSDOT_API_KEY')
    if not api_key:
        print("\n✗ WSDOT_API_KEY environment variable not set")
        print("  Set it with: export WSDOT_API_KEY='your-api-key'")
        return False

    print(f"\nUsing API Key: {api_key[:10]}...{api_key[-10:]}")
    print()

    # Define all known endpoints
    endpoints = {
        'Schedule API': [
            ('Active Seasons', 'https://wsdot.wa.gov/Ferries/API/Schedule/rest/activeseasons'),
            ('Caches Date', 'https://wsdot.wa.gov/Ferries/API/Schedule/rest/cachedate'),
            ('Routes', 'https://wsdot.wa.gov/Ferries/API/Schedule/rest/routes'),
            ('Route Details', 'https://wsdot.wa.gov/Ferries/API/Schedule/rest/routedetails', {'routeid': 1}),
            ('Schedule Today', 'https://wsdot.wa.gov/Ferries/API/Schedule/rest/schedule/today'),
           ('Available Dates', 'https://wsdot.wa.gov/Ferries/API/Schedule/rest/availabledates'),
        ],
        'Terminals API': [
            ('Terminal Basics', 'https://wsdot.wa.gov/Ferries/API/Terminals/rest/terminalbasics'),
            ('Terminal Locations', 'https://wsdot.wa.gov/Ferries/API/Terminals/rest/terminallocations'),
            ('Terminal Verbose', 'https://wsdot.wa.gov/Ferries/API/Terminals/rest/terminalverbose'),
            ('Waiting Times', 'https://wsdot.wa.gov/Ferries/API/Terminals/rest/waitingtimes'),
            ('Cache Date', 'https://wsdot.wa.gov/Ferries/API/Terminals/rest/cachedate'),
        ],
        'Vessels API': [
            ('Vessel Basics', 'https://wsdot.wa.gov/Ferries/API/Vessels/rest/vesselbasics'),
            ('Vessel Locations', 'https://wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations'),
            ('Vessel Verbose', 'https://wsdot.wa.gov/Ferries/API/Vessels/rest/vesselverbose'),
            ('Cache Date', 'https://wsdot.wa.gov/Ferries/API/Vessels/rest/cachedate'),
        ],
    }

    results = {}

    for api_name, api_endpoints in endpoints.items():
        print(f"\n{api_name}")
        print("-" * 70)

        results[api_name] = []

        for endpoint_data in api_endpoints:
            if len(endpoint_data) == 2:
                name, url = endpoint_data
                params = {}
            else:
                name, url, params = endpoint_data

            print(f"\n  Testing: {name}")
            print(f"  URL: {url}")

            result = test_endpoint(name, url, api_key, params)
            results[api_name].append(result)

            if result['status'] == 'success':
                print(f"  ✓ SUCCESS (HTTP {result['code']})")
                print(f"    Data type: {result['data_type']}")
                print(f"    Count: {result['data_count']}")
                if result.get('sample'):
                    sample_str = json.dumps(result['sample'], indent=4)[:200]
                    print(f"    Sample: {sample_str}...")
            elif result['status'] == 'success_non_json':
                print(f"  ✓ SUCCESS but non-JSON response")
                print(f"    Content: {result.get('content', '')}")
            elif result['status'] == 'failed':
                print(f"  ✗ FAILED (HTTP {result['code']})")
                print(f"    Message: {result.get('message', 'No message')}")
            else:
                print(f"  ✗ ERROR")
                print(f"    Message: {result.get('message', 'Unknown error')}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_tested = 0
    total_success = 0

    for api_name, api_results in results.items():
        success = sum(1 for r in api_results if r['status'] in ['success', 'success_non_json'])
        total = len(api_results)
        total_tested += total
        total_success += success

        print(f"\n{api_name}: {success}/{total} endpoints accessible")

        # List successful endpoints
        for result in api_results:
            if result['status'] in ['success', 'success_non_json']:
                print(f"  ✓ {result['name']}")

    print(f"\nOverall: {total_success}/{total_tested} endpoints accessible")

    # Save results
    output_file = 'ferry_api_exploration_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'api_key_used': f"{api_key[:10]}...{api_key[-10:]}",
            'results': results
        }, f, indent=2)

    print(f"\n✓ Detailed results saved to: {output_file}")

    print("\n" + "=" * 70)

    return total_success > 0


def test_with_client():
    """Test using the FerryAPIClient"""
    print("\n" + "=" * 70)
    print("Testing with FerryAPIClient")
    print("=" * 70)

    try:
        client = FerryAPIClient()

        print("\nTesting client methods:")

        # Test active seasons (we know this works)
        try:
            print("\n  get_active_seasons()...")
            seasons = client.get_active_seasons(cache=False)
            print(f"    ✓ Got {len(seasons)} seasons")
            if seasons:
                print(f"    Sample: {json.dumps(seasons[0], indent=6)[:200]}...")
        except Exception as e:
            print(f"    ✗ Error: {e}")

        # Test other methods
        test_methods = [
            ('get_routes', []),
            ('get_terminal_basics', []),
            ('get_vessel_basics', []),
        ]

        for method_name, args in test_methods:
            try:
                print(f"\n  {method_name}()...")
                method = getattr(client, method_name)
                data = method(*args, cache=False)
                count = len(data) if isinstance(data, (list, dict)) else 1
                print(f"    ✓ Got {count} items")
            except Exception as e:
                print(f"    ✗ Error: {e}")

    except Exception as e:
        print(f"\n✗ Could not initialize client: {e}")


def main():
    """Main entry point"""
    import sys

    success = explore_api()

    if success:
        test_with_client()

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
