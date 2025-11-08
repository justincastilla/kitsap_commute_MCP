# Washington State Ferries API Client

A comprehensive Python interface for gathering ferry information from the Washington State Department of Transportation (WSDOT) Ferry APIs.

## Features

- **Complete API Coverage**: Interfaces with all WSDOT Ferry APIs
  - Vessels API (locations, stats, accommodations)
  - Terminals API (info, conditions, bulletins)
  - Schedule API (routes, schedules, date ranges)
  - Fares API (fare information)

- **Intelligent Caching**: Automatically caches API responses to local files
  - Reduces API calls
  - Improves performance
  - Configurable cache behavior per endpoint

- **Easy to Use**: Simple, intuitive Python interface
- **Type-Safe**: Fully type-annotated for better IDE support

## Installation

No additional dependencies beyond the main project requirements. The client uses:
- `requests` - for HTTP requests
- `json` - for data serialization
- Standard library modules

## Setup

1. Set your WSDOT API key as an environment variable:
```bash
export WSDOT_API_KEY='your-api-key-here'
```

To get an API key, register at: https://wsdot.wa.gov/traffic/api/

2. Import the client in your code:
```python
from ferry_api import FerryAPIClient

client = FerryAPIClient()
```

## Usage

### Basic Terminal Information

```python
# Get all terminals
terminals = client.get_terminal_basics()

# Get detailed terminal locations
locations = client.get_terminal_locations()

# Get current bulletins and alerts
bulletins = client.get_terminal_bulletins()

# Get real-time terminal conditions (spaces available, etc.)
conditions = client.get_terminal_conditions()

# Get comprehensive terminal data
verbose = client.get_terminal_verbose()
```

### Vessel Information

```python
# Get basic vessel info
vessels = client.get_vessel_basics()

# Get current vessel locations and ETAs
locations = client.get_vessel_locations()

# Get vessel specifications (length, capacity, etc.)
stats = client.get_vessel_stats()

# Get vessel amenities (bathrooms, galley, etc.)
accommodations = client.get_vessel_accommodations()

# Get all vessel data
verbose = client.get_vessel_verbose()
```

### Schedule Information

```python
# Get valid date range for schedules
date_range = client.get_schedule_date_range()

# Get all routes
routes = client.get_routes()

# Get terminals for a specific date
terminals = client.get_schedule_terminals(date='2024-12-01')

# Get schedule for a specific route
schedule = client.get_route_schedules(route_id=1, date='2024-12-01')
```

### Fare Information

```python
# Get fare data
fares = client.get_fares()
```

### Batch Operations

```python
# Fetch and cache all static data at once
all_data = client.fetch_all_static_data()

# Fetch all current real-time data
current = client.fetch_current_conditions()
```

### Cache Management

```python
# Disable caching for real-time data
locations = client.get_vessel_locations(cache=False)

# Clear specific cached files
client.clear_cache('vessel_*.json')

# Clear all cache
client.clear_cache()

# Specify custom cache directory
client = FerryAPIClient(cache_dir='/path/to/cache')
```

## Data Storage

By default, all cached data is stored in `./data/ferry_cache/` as JSON files.

Each cached file contains:
- `cached_at`: ISO timestamp of when data was cached
- `data`: The actual API response data

### Cache Files

**Static data** (cached by default):
- `vessel_basics.json` - Basic vessel information
- `vessel_stats.json` - Vessel specifications
- `vessel_accommodations.json` - Vessel amenities
- `vessel_verbose.json` - Complete vessel data
- `terminal_basics.json` - Basic terminal information
- `terminal_locations.json` - Terminal location details
- `terminal_verbose.json` - Complete terminal data
- `routes.json` - All ferry routes
- `fares.json` - Fare information
- `schedule_date_range.json` - Valid schedule date range
- `all_static_data.json` - Combined static data

**Dynamic data** (timestamped):
- `vessel_locations_YYYYMMDD_HHMM.json` - Vessel positions
- `terminal_conditions_YYYYMMDD_HHMM.json` - Terminal space availability
- `terminal_bulletins_YYYYMMDD_HHMM.json` - Current alerts
- `current_conditions_YYYYMMDD_HHMM.json` - Combined real-time data

## API Endpoints Reference

### Vessels API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_vessel_basics()` | `/vesselbasics` | Basic vessel info |
| `get_vessel_locations()` | `/vessellocations` | Current positions & ETAs |
| `get_vessel_stats()` | `/vesselstats` | Vessel specifications |
| `get_vessel_accommodations()` | `/vesselaccommodations` | Amenities & facilities |
| `get_vessel_verbose()` | `/vesselverbose` | Complete vessel data |

### Terminals API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_terminal_basics()` | `/terminalbasics` | Basic terminal info |
| `get_terminal_locations()` | `/terminallocations` | Location details |
| `get_terminal_bulletins()` | `/terminalbulletins` | Alerts & bulletins |
| `get_terminal_conditions()` | `/terminalconditions` | Real-time conditions |
| `get_terminal_verbose()` | `/terminalverbose` | Complete terminal data |

### Schedule API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_schedule_date_range()` | `/validdaterange` | Valid schedule dates |
| `get_schedule_terminals()` | `/terminals` | Terminals for date |
| `get_routes()` | `/routebasics` | All ferry routes |
| `get_route_schedules()` | `/schedule` | Route schedule |

### Fares API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_fares()` | `/fares` | Fare information |

## Example: Full Data Fetch

```python
from ferry_api import FerryAPIClient

# Initialize client
client = FerryAPIClient()

# Fetch all static data (vessels, terminals, routes, fares)
print("Fetching static data...")
static = client.fetch_all_static_data()

print(f"Vessels: {len(static['vessels']['basics'])}")
print(f"Terminals: {len(static['terminals']['basics'])}")
print(f"Routes: {len(static['schedule']['routes'])}")

# Fetch current conditions
print("\nFetching real-time data...")
current = client.fetch_current_conditions()

print(f"Active vessels: {len(current['vessel_locations'])}")
print(f"Terminal conditions: {len(current['terminal_conditions'])}")
print(f"Current bulletins: {len(current['terminal_bulletins'])}")

print(f"\nAll data cached in: {client.cache_dir}")
```

## Integration with MCP Server

The ferry API client can be easily integrated with the existing MCP server:

```python
from ferry_api import FerryAPIClient

# In commute_server.py
ferry_client = FerryAPIClient()

@mcp.tool(
    name="get_real_time_ferry_locations",
    description="Get current locations of all ferries"
)
def get_ferry_locations():
    """Get real-time ferry vessel locations"""
    return ferry_client.get_vessel_locations(cache=False)

@mcp.tool(
    name="get_terminal_status",
    description="Get current terminal conditions and space availability"
)
def get_terminal_status():
    """Get real-time terminal conditions"""
    return ferry_client.get_terminal_conditions(cache=False)
```

## Testing

Run the test script to verify the API client:

```bash
# Make sure WSDOT_API_KEY is set
export WSDOT_API_KEY='your-api-key'

# Run tests
python test_ferry_api.py
```

Or test the main module directly:

```bash
python ferry_api.py
```

## Error Handling

The client raises exceptions for various error conditions:

```python
try:
    client = FerryAPIClient()
    terminals = client.get_terminal_basics()
except ValueError as e:
    print(f"Configuration error: {e}")
except requests.HTTPError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## API Rate Limits

Be mindful of WSDOT API rate limits. The caching system helps minimize API calls:
- Use `cache=True` (default) for static data
- Use `cache=False` only for real-time data that changes frequently
- Call `fetch_all_static_data()` once at startup
- Call `fetch_current_conditions()` periodically for updates

## Contributing

When adding new endpoints:

1. Add the method to the appropriate API section in `ferry_api.py`
2. Follow the existing naming convention: `get_<resource>_<detail_level>()`
3. Include proper type hints and docstrings
4. Add caching support with sensible defaults
5. Update this README with the new method

## Resources

- [WSDOT Ferry API Documentation](https://wsdot.wa.gov/ferries/api/)
- [Vessels API Docs](https://wsdot.wa.gov/ferries/api/vessels/documentation/rest.html)
- [Terminals API Docs](https://wsdot.wa.gov/ferries/api/terminals/documentation/rest.html)
- [Schedule API Docs](https://wsdot.wa.gov/ferries/api/schedule/documentation/rest.html)
- [Fares API Docs](https://wsdot.wa.gov/ferries/api/fares/documentation/rest.html)

## License

This module is part of the Kitsap Commute MCP Server project.
