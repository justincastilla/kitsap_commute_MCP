# Ferry Schedule Updater

Tools for fetching and updating ferry schedule data from the WSDOT Ferry APIs.

## Files

- **update_ferry_schedules.py** - Fetches current schedules from WSDOT API and updates the static schedule file
- **verify_schedule_data.py** - Analyzes and validates the current schedule data
- **ferry_api.py** - Comprehensive API client for all WSDOT Ferry APIs

## Current Status

⚠️ **API Access Issue**: The WSDOT Ferry APIs are currently returning `403 Forbidden` errors with the provided API key. This could be due to:

1. **API Key Registration**: The API key may need to be registered or activated at https://wsdot.wa.gov/traffic/api/
2. **IP Restrictions**: Some APIs require whitelisting of IP addresses
3. **API Changes**: The API endpoints or authentication method may have changed
4. **Rate Limiting**: There might be rate limits or usage restrictions

## Getting API Access

To use the WSDOT Ferry APIs, you need to:

1. **Register for an API key** at: https://wsdot.wa.gov/traffic/api/
   - Sign up for a WSDOT Traveler Information API account
   - Request access to the Ferry APIs specifically

2. **Set your API key** as an environment variable:
   ```bash
   export WSDOT_API_KEY='your-api-key-here'
   ```

3. **Verify access** by running:
   ```bash
   python -c "from ferry_api import FerryAPIClient; client = FerryAPIClient(); print(client.get_terminal_basics())"
   ```

## Usage

### Verify Current Schedule Data

Check your current static schedule file:

```bash
python verify_schedule_data.py
```

This will show:
- Total routes and sailings
- Route details (first/last sailing times, crossing durations)
- Data validation (missing fields, inconsistencies)

**Example output:**
```
======================================================================
Ferry Schedule Analysis
======================================================================

Schedule file: static_ferry_schedules.json
Total routes: 8

Route Details:
BAINBRIDGE ISLAND-SEATTLE
  Directions: east, king, seattle
  Weekday sailings: 23
  Weekend sailings: 22
  Weekday: 04:45 AM - 12:55 AM (crossing: 35 min)
  ...

Total weekday sailings: 174
Total weekend sailings: 165
✓ No issues found - schedule data looks good!
```

### Update Schedules from API

Once you have valid API access:

```bash
export WSDOT_API_KEY='your-api-key'
python update_ferry_schedules.py
```

This will:
1. Fetch all ferry routes from the API
2. Get current schedule data for each route
3. Convert API format to MCP server format
4. Create a backup of the existing schedule file
5. Save the updated schedules to `data/static_ferry_schedules.json`

**Features:**
- Automatic backup creation before updating
- Comprehensive error handling
- Progress reporting for each route
- Data validation

### Manual Schedule Updates

If the API is not accessible, you can manually update the schedule file:

1. **Visit WSDOT Ferry Schedules**: https://wsdot.wa.gov/ferries/schedule/
2. **Download schedule PDFs** or check the online schedules
3. **Manually edit** `data/static_ferry_schedules.json`
4. **Verify your changes**:
   ```bash
   python verify_schedule_data.py
   ```

## Schedule Data Format

The static schedule file uses this format:

```json
{
  "route-key": {
    "direction": ["east", "king", "seattle"],
    "weekday": [
      {
        "time": "04:45 AM",
        "annotations": ["Direct route"],
        "direction": "east",
        "crossing_time": 35
      }
    ],
    "weekend": [
      {
        "time": "05:20 AM",
        "annotations": [],
        "direction": "east",
        "crossing_time": 35
      }
    ]
  }
}
```

**Fields:**
- `direction`: Array of direction tags (east/west, county names, etc.)
- `weekday`: Array of Monday-Friday sailing times
- `weekend`: Array of Saturday-Sunday sailing times
- `time`: Departure time in 12-hour format (e.g., "04:45 AM")
- `annotations`: Optional notes (e.g., "Direct route", "Summer only")
- `crossing_time`: Duration of crossing in minutes

**Route Keys:**
- Format: `{origin}-{destination}` (lowercase, normalized)
- Examples: `bainbridge island-seattle`, `edmonds-kingston`

**Direction Tags:**
Used for filtering routes by travel direction:
- **Geographic**: `east`, `west`, `north`, `south`
- **Counties**: `king`, `kitsap`, `snohomish`, `island`
- **Regions**: `seattle`, `peninsula`, `islands`

## Troubleshooting

### 403 Forbidden Errors

If you get 403 errors when accessing the API:

1. **Verify API key registration**:
   - Check that your key is active at https://wsdot.wa.gov/traffic/api/
   - Ensure you have access to Ferry APIs (not just traffic APIs)

2. **Check API documentation**:
   - Visit: https://wsdot.wa.gov/ferries/api/
   - Review authentication requirements
   - Check for any recent API changes

3. **Test with different endpoints**:
   ```python
   from ferry_api import FerryAPIClient
   client = FerryAPIClient()

   # Try different endpoints
   print(client.get_terminal_basics())  # Simplest endpoint
   print(client.get_routes())           # Schedule API
   print(client.get_vessel_basics())    # Vessel API
   ```

4. **Contact WSDOT**:
   - If issues persist, contact WSDOT API support
   - Email: They may have a support contact on their API registration page

### Empty or Missing Schedule Data

If the API returns empty data:

1. Check the **valid date range**:
   ```python
   from ferry_api import FerryAPIClient
   client = FerryAPIClient()
   print(client.get_schedule_date_range())
   ```

2. Verify the **route ID** is correct
3. Try fetching for a **specific date** within the valid range

### Data Format Issues

If converted data doesn't match expected format:

1. Run the verification tool to identify issues:
   ```bash
   python verify_schedule_data.py
   ```

2. Check the API response format:
   - API formats may change over time
   - Update `update_ferry_schedules.py` parsing logic if needed

3. Review the WSDOT API documentation for format changes

## Development

### Adding New Routes

To add support for a new ferry route:

1. **Update route directions** in `update_ferry_schedules.py`:
   ```python
   ROUTE_DIRECTIONS = {
       'new-route-origin-destination': ['direction', 'tags'],
       ...
   }
   ```

2. **Add crossing time** estimate:
   ```python
   CROSSING_TIMES = {
       'new-route-origin-destination': 25,  # minutes
       ...
   }
   ```

3. **Run the updater** to fetch the new route's schedule

### Modifying Data Conversion

The `update_ferry_schedules.py` script converts API data to the MCP format. Key functions:

- `extract_sailing_times()` - Extracts times from API response
- `convert_time_format()` - Converts 24-hour to 12-hour format
- `process_schedule_item()` - Processes individual sailing entries

If the API format changes, update these functions accordingly.

## Resources

- [WSDOT Ferry API Registration](https://wsdot.wa.gov/traffic/api/)
- [Ferry Vessels API Docs](https://wsdot.wa.gov/ferries/api/vessels/documentation/rest.html)
- [Ferry Terminals API Docs](https://wsdot.wa.gov/ferries/api/terminals/documentation/rest.html)
- [Ferry Schedule API Docs](https://wsdot.wa.gov/ferries/api/schedule/documentation/rest.html)
- [Ferry Fares API Docs](https://wsdot.wa.gov/ferries/api/fares/documentation/rest.html)
- [Online Ferry Schedules](https://wsdot.wa.gov/ferries/schedule/)

## Next Steps

1. **Resolve API access** - Register/activate your API key
2. **Test the updater** - Run `update_ferry_schedules.py` once access works
3. **Schedule regular updates** - Set up a cron job or scheduled task:
   ```bash
   # Run weekly on Sunday at 2 AM
   0 2 * * 0 cd /path/to/kitsap_commute_MCP && python update_ferry_schedules.py
   ```
4. **Monitor for changes** - WSDOT updates schedules seasonally
