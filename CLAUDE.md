# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kitsap Commute Helper is a **dual MCP server application** that helps Kitsap County residents plan ferry/car commutes and manage events. It consists of two FastMCP servers that integrate with Claude Desktop:

1. **`commute_server.py`** - Ferry schedules, driving times, route planning using WSDOT and Google Maps APIs
2. **`elasticsearch_server.py`** - Event storage and semantic search using Elasticsearch with ML embeddings

Both servers are designed to run as **stdio-based MCP servers** for Claude Desktop, not HTTP servers.

## Core Architecture

### Configuration System

All environment variables and settings flow through **`config.py`** (centralized configuration):
- API keys: `WSDOT_API_KEY`, `GOOGLE_MAPS_API_KEY`
- Elasticsearch: `ELASTIC_ENDPOINT`, `ELASTIC_API_KEY`, `EVENT_INDEX`
- ML model settings: `EMBEDDING_MODEL_ID`, `INFERENCE_ENDPOINT_ID`, `PIPELINE_ID`
- Paths: `DATA_DIR`, `PROJECT_ROOT`

**Important:** Never load `.env` directly in other files - always import from `config.py`.

### Data Architecture

Three categories of data files in `data/`:

1. **Ferry Reference Data** (static, rarely changes):
   - `ferry_terminals.json` - 7 terminals with geocoded locations
   - `ferry_schedules.json` - Static schedules by route (weekday/weekend)

2. **Sample Events** (test data):
   - `sample_events.json` - Tech events for demo/testing (currently Dec 2025 - Feb 2026)

3. **Deprecated** (backward compatibility):
   - `elasticsearch_initialization.py` - Deprecated shim, use `setup/elasticsearch_setup.py`

### MCP Server Structure

Each server uses **FastMCP** decorators:

**commute_server.py** exposes:
- **2 Resources**: `fetch_ferry_schedules()`, `fetch_terminals()`
- **4 Tools**: `find_nearby_ferry_terminals()`, `drive_time_tool()`, `get_ferry_times()`, `ferry_cost()`
- **2 Prompts**: `user_preferences()`, `plan_trip()`

**elasticsearch_server.py** exposes:
- **2 Tools**: `search_events()`, `create_event()`

### Elasticsearch + ML Pipeline

The event search uses **hybrid retrieval** with Reciprocal Rank Fusion (RRF):
1. **Text search** - Multi-match across title/description/topic
2. **Semantic search** - E5 multilingual embeddings via Elasticsearch ML inference
3. **RRF fusion** - Combines both results with configurable rank constant

Events are indexed through an **ingest pipeline** that auto-generates `description_vector` embeddings.

## Development Commands

### Running Locally (Without Docker)

```bash
# Install dependencies
pip install elasticsearch fastmcp pydantic python-dotenv requests

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Initialize Elasticsearch (first time only)
python setup/elasticsearch_setup.py --all

# Run servers (in separate terminals)
python commute_server.py
python elasticsearch_server.py
```

### Running with Docker

```bash
# Build and start both MCP servers (Elasticsearch runs separately)
docker-compose up --build

# View logs
docker-compose logs -f commute-server
docker-compose logs -f elasticsearch-server

# Stop services
docker-compose down
```

**Note:** Docker setup runs the MCP servers in containers, but Elasticsearch must run separately (locally or cloud).

### Elasticsearch Setup

```bash
# Run all setup steps at once
python setup/elasticsearch_setup.py --all

# Or run individually
python setup/elasticsearch_setup.py --create-index
python setup/elasticsearch_setup.py --create-endpoint
python setup/elasticsearch_setup.py --create-pipeline
python setup/elasticsearch_setup.py --load-sample-data
```

### Claude Desktop Integration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kitsap-commute": {
      "command": "/Users/username/.pyenv/shims/python3",
      "args": ["/path/to/kitsap-commute-helper/commute_server.py"]
    },
    "kitsap-events": {
      "command": "/Users/username/.pyenv/shims/python3",
      "args": ["/path/to/kitsap-commute-helper/elasticsearch_server.py"]
    }
  }
}
```

**Important:** Use full paths for both `command` (Python binary) and `args` (script path).

## Key Implementation Details

### User Preferences (Commute Planning)

The `user_preferences` prompt defines default behavior:
- Always provide **exactly 3 route options**
- One option **must be driving-only** (no ferry)
- Other 2 options are ferry + driving combinations
- Arrival: 15 minutes before event time
- Display in table format

Reference this prompt when modifying route planning logic.

### Ferry Route Keys

Routes are keyed as `"{origin}-{destination}"` (lowercase) in `ferry_schedules.json`:
- Example: `"bremerton-seattle"`
- Each route has `direction`, `weekday`, `weekend` arrays

### Cost Calculations

**Mileage Cost** (`drive_time_tool`):
- **Rate**: $0.77 per mile (hardcoded constant)
- Automatically calculated for all driving routes
- Returns `mileage_cost`, `distance_miles`, and `cost_summary` fields
- Uses Google Maps distance in meters, converted to miles: `distance_meters * 0.000621371`

**Ferry Fares** (`ferry_cost`):
- **WSDOT Fares API**: Calls official WSDOT API for real-time ferry pricing
- **Terminal mapping**: Translates terminal names to IDs (e.g., "Southworth" → 20)
- **Travel modes**: "walk" (passenger only) or "drive" (vehicle + driver)
- **Vehicle sizes**: "standard" (under 22'), "small" (under 14'), "motorcycle"
- **WA Ferry Pricing Rule**:
  - Eastbound (to mainland) = PAID
  - Westbound (to islands) = FREE
  - Examples: Seattle→Bainbridge is FREE, Bainbridge→Seattle is PAID
- **Fallback logic**: If exact fare not found, searches for reasonable default
- Returns `fare_amount`, `fare_name`, `cost_summary` fields

**Terminal ID Mapping** (hardcoded in `ferry_cost`):
```python
terminal_mapping = {
    "seattle": 7, "bainbridge island": 3, "southworth": 20,
    "fauntleroy": 9, "edmonds": 8, "kingston": 12,
    "bremerton": 4, "point defiance": 16, "tahlequah": 21,
    # ... plus San Juan Islands terminals
}
```

### Southworth Ferry Special Case

When planning routes to Seattle:
- Southworth ferry goes to **Fauntleroy (West Seattle)**, NOT downtown
- If destination is downtown Seattle, must add drive time from Fauntleroy
- This is documented in the `how_to_plan_a_trip` prompt

### Haversine Distance Calculation

`utilities.haversine()` calculates great-circle distance in kilometers. Used for:
- Finding nearest ferry terminals
- Sorting terminals by distance from origin

### Date/Time Handling

- All event times use **ISO 8601 format** with timezone (e.g., `2025-12-03T18:00:00-08:00`)
- Winter months (Dec-Feb) use PST (`-08:00`), summer uses PDT (`-07:00`)
- `utilities.get_day_type()` returns `'weekday'` or `'weekend'` for ferry schedule lookups

### Elasticsearch Embedding Dimension

The E5-small model generates **384-dimensional vectors**. This is hardcoded in `config.py`:
```python
EMBEDDING_DIM = 384  # E5-small default
```

If changing the embedding model, update this constant AND the index mapping.

## Common Pitfalls

1. **Duplicate function names**: The branch had two functions named `plan_a_trip2()`. These are now `plan_trip_basic()` and `plan_trip_detailed()`.

2. **Import order**: Always import from `config.py` before using environment variables. Never use `os.getenv()` directly in server files.

3. **Ferry schedules are static**: The current implementation uses static JSON schedules. For real-time data, integrate with WSDOT's live API.

4. **Elasticsearch must be running**: Both the setup scripts and the elasticsearch_server.py require a running Elasticsearch instance. The servers will fail silently if ES is unreachable.

5. **Sample events are in the future**: When testing, remember that `sample_events.json` contains events in Dec 2025 - Feb 2026.

## File Migration Notes

The codebase recently underwent reorganization:

- **Old**: `data/elasticsearch_initialization.py` (299 lines, mixed setup + operations)
- **New**: `setup/elasticsearch_setup.py` (clean setup functions only)
- **Compatibility**: The old file is now a deprecation shim

When adding Elasticsearch setup functionality, modify `setup/elasticsearch_setup.py`, not the deprecated file.

## API Keys Required

- **WSDOT_API_KEY** - Washington State DOT ferry API access
- **GOOGLE_MAPS_API_KEY** - Geocoding and directions API
- **ELASTIC_API_KEY** - Optional for local Elasticsearch, required for Elastic Cloud
- **ELASTIC_ENDPOINT** - Defaults to `http://localhost:9200`

All keys go in `.env` file (never commit this file).
