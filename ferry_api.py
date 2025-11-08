"""
Comprehensive Washington State Ferries API Client

This module provides a complete interface to the WSDOT Ferry APIs:
- Vessels API: vessel information, locations, stats, accommodations
- Terminals API: terminal information, locations, bulletins, conditions
- Schedule API: routes, schedules, and date ranges
- Fares API: fare information

All data can be cached locally to minimize API calls and improve performance.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any


class FerryAPIClient:
    """Client for interacting with Washington State Ferries APIs"""

    BASE_URLS = {
        'vessels': 'https://wsdot.wa.gov/Ferries/API/Vessels/rest',
        'terminals': 'https://wsdot.wa.gov/Ferries/API/Terminals/rest',
        'schedule': 'https://wsdot.wa.gov/Ferries/API/Schedule/rest',
        'fares': 'https://wsdot.wa.gov/Ferries/API/Fares/rest',
    }

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the Ferry API Client

        Args:
            api_key: WSDOT API access code (defaults to WSDOT_API_KEY env var)
            cache_dir: Directory to store cached API responses (defaults to ./data/ferry_cache)
        """
        self.api_key = api_key or os.getenv('WSDOT_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set WSDOT_API_KEY environment variable or pass api_key parameter.")

        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent / 'data' / 'ferry_cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _make_request(self, api_type: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the WSDOT Ferry API

        Args:
            api_type: Type of API ('vessels', 'terminals', 'schedule', 'fares')
            endpoint: API endpoint to call
            params: Additional query parameters

        Returns:
            JSON response from the API
        """
        if api_type not in self.BASE_URLS:
            raise ValueError(f"Invalid API type: {api_type}")

        url = f"{self.BASE_URLS[api_type]}/{endpoint}"

        # Add API key to params
        if params is None:
            params = {}
        params['apiaccesscode'] = self.api_key

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def _save_to_cache(self, filename: str, data: Any) -> Path:
        """
        Save data to cache file

        Args:
            filename: Name of the cache file
            data: Data to save (will be JSON serialized)

        Returns:
            Path to the saved file
        """
        filepath = self.cache_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'cached_at': datetime.now().isoformat(),
                'data': data
            }, f, indent=2)
        print(f"Saved to cache: {filepath}")
        return filepath

    def _load_from_cache(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load data from cache file

        Args:
            filename: Name of the cache file

        Returns:
            Cached data or None if file doesn't exist
        """
        filepath = self.cache_dir / filename
        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            cached = json.load(f)

        print(f"Loaded from cache: {filepath} (cached at {cached.get('cached_at')})")
        return cached.get('data')

    # ==================== VESSELS API ====================

    def get_vessel_basics(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get basic information about all vessels

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of vessels with basic information
        """
        cache_file = 'vessel_basics.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('vessels', 'vesselbasics')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_vessel_locations(self, cache: bool = False) -> List[Dict[str, Any]]:
        """
        Get current vessel locations and ETAs

        Args:
            cache: Whether to save to cache (default False as this changes frequently)

        Returns:
            List of vessels with location and ETA data
        """
        cache_file = f'vessel_locations_{datetime.now().strftime("%Y%m%d_%H%M")}.json'

        data = self._make_request('vessels', 'vessellocations')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_vessel_stats(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get vessel statistics (specifications, engine count, length, year built, etc.)

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of vessels with detailed statistics
        """
        cache_file = 'vessel_stats.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('vessels', 'vesselstats')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_vessel_accommodations(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get vessel accommodations (bathrooms, galley, elevator, etc.)

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of vessels with accommodation details
        """
        cache_file = 'vessel_accommodations.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('vessels', 'vesselaccommodations')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_vessel_verbose(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get highly detailed information for all vessels

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of vessels with comprehensive details
        """
        cache_file = 'vessel_verbose.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('vessels', 'vesselverbose')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    # ==================== TERMINALS API ====================

    def get_terminal_basics(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get basic information about all terminals

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of terminals with basic information
        """
        cache_file = 'terminal_basics.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('terminals', 'terminalbasics')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_terminal_locations(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get detailed location information for all terminals

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of terminals with location details
        """
        cache_file = 'terminal_locations.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('terminals', 'terminallocations')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_terminal_bulletins(self, cache: bool = False) -> List[Dict[str, Any]]:
        """
        Get alerts and bulletins for all terminals

        Args:
            cache: Whether to save to cache (default False as bulletins change frequently)

        Returns:
            List of terminal bulletins and alerts
        """
        cache_file = f'terminal_bulletins_{datetime.now().strftime("%Y%m%d_%H%M")}.json'

        data = self._make_request('terminals', 'terminalbulletins')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_terminal_conditions(self, cache: bool = False) -> List[Dict[str, Any]]:
        """
        Get current terminal conditions (drive-up and reservation spaces available)

        Args:
            cache: Whether to save to cache (default False as conditions change frequently)

        Returns:
            List of terminals with current condition data
        """
        cache_file = f'terminal_conditions_{datetime.now().strftime("%Y%m%d_%H%M")}.json'

        data = self._make_request('terminals', 'terminalconditions')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_terminal_verbose(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get comprehensive terminal information

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of terminals with detailed information
        """
        cache_file = 'terminal_verbose.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('terminals', 'terminalverbose')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    # ==================== SCHEDULE API ====================

    def get_active_seasons(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get active ferry schedule seasons

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of active seasons with date ranges
        """
        cache_file = 'active_seasons.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('schedule', 'activeseasons')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_schedule_date_range(self, cache: bool = True) -> Dict[str, Any]:
        """
        Get the valid date range for which schedule data is available

        Args:
            cache: Whether to save/load from cache

        Returns:
            Dictionary with date range information
        """
        cache_file = 'schedule_date_range.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('schedule', 'validdaterange')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_schedule_terminals(self, date: Optional[str] = None, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get valid departing terminals for a given date

        Args:
            date: Trip date in format 'YYYY-MM-DD' (defaults to today)
            cache: Whether to save/load from cache

        Returns:
            List of valid terminals for the date
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        cache_file = f'schedule_terminals_{date}.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('schedule', 'terminals', {'date': date})

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_routes(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get information about all ferry routes

        Args:
            cache: Whether to save/load from cache

        Returns:
            List of routes with basic information
        """
        cache_file = 'routes.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('schedule', 'routebasics')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    def get_route_schedules(self, route_id: int, date: Optional[str] = None, cache: bool = True) -> Dict[str, Any]:
        """
        Get schedule for a specific route

        Args:
            route_id: Route ID
            date: Schedule date in format 'YYYY-MM-DD' (defaults to today)
            cache: Whether to save/load from cache

        Returns:
            Schedule data for the route
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        cache_file = f'route_schedule_{route_id}_{date}.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('schedule', 'schedule', {'routeid': route_id, 'date': date})

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    # ==================== FARES API ====================

    def get_fares(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get fare information

        Args:
            cache: Whether to save/load from cache

        Returns:
            Fare information
        """
        cache_file = 'fares.json'

        if cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        data = self._make_request('fares', 'fares')

        if cache:
            self._save_to_cache(cache_file, data)

        return data

    # ==================== UTILITY METHODS ====================

    def fetch_all_static_data(self) -> Dict[str, Any]:
        """
        Fetch and cache all static data (data that doesn't change frequently)

        Returns:
            Dictionary containing all fetched data
        """
        print("Fetching all static ferry data...")

        data = {
            'vessels': {
                'basics': self.get_vessel_basics(),
                'stats': self.get_vessel_stats(),
                'accommodations': self.get_vessel_accommodations(),
                'verbose': self.get_vessel_verbose(),
            },
            'terminals': {
                'basics': self.get_terminal_basics(),
                'locations': self.get_terminal_locations(),
                'verbose': self.get_terminal_verbose(),
            },
            'schedule': {
                'date_range': self.get_schedule_date_range(),
                'routes': self.get_routes(),
            },
            'fares': self.get_fares(),
        }

        # Save combined data
        self._save_to_cache('all_static_data.json', data)

        print(f"\nAll static data fetched and cached to {self.cache_dir}")
        return data

    def fetch_current_conditions(self) -> Dict[str, Any]:
        """
        Fetch current real-time data (vessel locations, terminal conditions, bulletins)

        Returns:
            Dictionary containing current conditions
        """
        print("Fetching current ferry conditions...")

        data = {
            'vessel_locations': self.get_vessel_locations(cache=True),
            'terminal_conditions': self.get_terminal_conditions(cache=True),
            'terminal_bulletins': self.get_terminal_bulletins(cache=True),
        }

        # Save combined current data
        cache_file = f'current_conditions_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        self._save_to_cache(cache_file, data)

        print(f"\nCurrent conditions fetched and cached to {self.cache_dir}")
        return data

    def clear_cache(self, pattern: str = '*') -> int:
        """
        Clear cached files

        Args:
            pattern: Glob pattern for files to delete (default: all files)

        Returns:
            Number of files deleted
        """
        deleted = 0
        for filepath in self.cache_dir.glob(pattern):
            if filepath.is_file():
                filepath.unlink()
                deleted += 1

        print(f"Deleted {deleted} cached file(s)")
        return deleted


def main():
    """Example usage of the FerryAPIClient"""
    import sys

    try:
        client = FerryAPIClient()

        print("=" * 60)
        print("Washington State Ferries API Client")
        print("=" * 60)

        # Fetch all static data
        print("\n1. Fetching all static data...")
        static_data = client.fetch_all_static_data()

        print(f"\n   Vessels: {len(static_data['vessels']['basics'])}")
        print(f"   Terminals: {len(static_data['terminals']['basics'])}")
        print(f"   Routes: {len(static_data['schedule']['routes'])}")

        # Fetch current conditions
        print("\n2. Fetching current conditions...")
        current_data = client.fetch_current_conditions()

        print(f"\n   Active Vessels: {len(current_data['vessel_locations'])}")
        print(f"   Terminal Conditions: {len(current_data['terminal_conditions'])}")
        print(f"   Bulletins: {len(current_data['terminal_bulletins'])}")

        print("\n" + "=" * 60)
        print(f"All data cached in: {client.cache_dir}")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    exit(main())
