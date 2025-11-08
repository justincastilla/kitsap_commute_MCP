# Kitsap Commute & Event Minder

A Python-based app to help Kitsap County residents plan commutes and manage events, using real-time WSDOT and Google Maps data. The application provides ferry, drive, and event creation and search. These are MCP servers that can be used with Claude Desktop or any other client that uses MCP.

## Main Components

### MCP Servers
- **`commute_server.py`**: Ferry schedules, route planning, driving times, and cost calculations
  - 2 Resources: Ferry schedules and terminals
  - 4 Tools: Find nearby terminals, calculate drive times with mileage cost, get ferry schedules, get ferry fares
  - 2 Prompts: User preferences and comprehensive trip planning

- **`elasticsearch_server.py`**: Event storage and semantic search
  - 2 Tools: Search events (hybrid semantic + keyword), create events

### Supporting Files
- `config.py`: Centralized configuration management
- `utilities.py`: Shared utility functions (haversine distance, date parsing, schedule loading)
- `setup/`: One-time Elasticsearch setup scripts
- `data/`: Reference data (ferry terminals, schedules) and sample events

## Project Structure

```
kitsap_commute_MCP/
├── Dockerfile                 # Docker container configuration
├── docker-compose.yml         # Multi-container orchestration
├── commute_server.py          # MCP server for ferry & commute planning
├── elasticsearch_server.py    # MCP server for event search
├── utilities.py               # Shared utility functions
├── config.py                  # Centralized configuration
│
├── data/                      # Reference and sample data
│   ├── README.md              # Documentation for data files
│   ├── ferry_terminals.json   # Ferry terminal locations
│   ├── ferry_schedules.json   # Static ferry schedules
│   └── sample_events.json     # Sample events for testing
│
└── setup/                     # One-time setup scripts
    └── elasticsearch_setup.py # Elasticsearch initialization
```

## Getting Started with Docker

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed
- **Elasticsearch running separately** (locally or in the cloud)

### 1. Start Elasticsearch

You need Elasticsearch running before starting the MCP servers. Options:

**Option A: Run Elasticsearch locally** (not in Docker):
```bash
# Download and run Elasticsearch 8.11.0+
# See: https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html
```

**Option B: Use Elastic Cloud**:
- Sign up at https://cloud.elastic.co
- Create a deployment
- Note your endpoint URL and API key

### 2. Set up environment variables

Copy `.env.example` to `.env` and fill in all required API keys:

```bash
cp .env.example .env
# Edit .env and add your actual keys:
# - GOOGLE_MAPS_API_KEY
# - WSDOT_API_KEY
# - ELASTIC_ENDPOINT (e.g., http://localhost:9200 or your Elastic Cloud URL)
# - ELASTIC_API_KEY (optional for local ES, required for Elastic Cloud)
```

### 3. Set up Elasticsearch (First Time Only)

Initialize the index and load sample data:

```bash
# If running Elasticsearch locally, run setup directly:
python setup/elasticsearch_setup.py --all

# Or run steps individually:
python setup/elasticsearch_setup.py --create-index
python setup/elasticsearch_setup.py --create-endpoint
python setup/elasticsearch_setup.py --create-pipeline
python setup/elasticsearch_setup.py --load-sample-data
```

### 4. Start MCP servers with Docker Compose (Optional)

**Note**: Docker is optional. For Claude Desktop, running locally (without Docker) is simpler and recommended.

If you want to run in Docker containers:

```bash
# Build and start servers
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

The servers will run as stdio-based MCP servers in containers.

### 5. Manage services

```bash
# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f commute-server
docker-compose logs -f elasticsearch-server

# Restart a service
docker-compose restart commute-server
```

### 6. Connect with Claude Desktop

MCP servers run as stdio-based processes, not HTTP servers. Add them to your Claude Desktop config:

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "kitsap-commute": {
      "command": "/usr/local/bin/python3",
      "args": ["/absolute/path/to/kitsap-commute-helper/commute_server.py"]
    },
    "kitsap-events": {
      "command": "/usr/local/bin/python3",
      "args": ["/absolute/path/to/kitsap-commute-helper/elasticsearch_server.py"]
    }
  }
}
```

**Important**:
- Use absolute paths for both the Python binary and script paths
- Find your Python path with: `which python3`
- If using pyenv/virtualenv, use the full path to that Python binary

After updating the config, restart Claude Desktop.

---

## Alternative: Running without Docker

If you prefer to run without Docker (recommended for Claude Desktop):

1. Install dependencies:
   ```bash
   pip install elasticsearch fastmcp pydantic python-dotenv requests
   ```

2. Set up `.env` file with your API keys

3. Run servers directly for testing:
   ```bash
   python commute_server.py
   python elasticsearch_server.py  # in a separate terminal
   ```

4. Or connect via Claude Desktop (preferred method, see above)

---

## Features

### Commute Planning
- **Smart route planning**: Automatically provides 3 route options (1 driving-only + 2 ferry combinations)
- **Real-time drive times**: Uses Google Maps API with traffic data
- **Cost calculations**:
  - Mileage cost at $0.77/mile for driving routes
  - Ferry fares from WSDOT API (supports walk-on, standard/small/motorcycle vehicles)
  - Understands WA ferry pricing (eastbound paid, westbound free)
- **Ferry schedules**: Static schedules with weekday/weekend differentiation
- **Arrival buffer**: All routes guarantee arrival 15 minutes before event time
- **Terminal finder**: Finds nearest ferry terminals to any address

### Event Management
- **Hybrid search**: Combines semantic (E5 embeddings) and keyword search using RRF
- **Flexible filtering**: Search by time range, topic, location, title, or presenting status
- **Sample data**: Includes tech events in King County (Dec 2025 - Feb 2026)

### Performance
- **Optimized loading**: Static data loaded once at startup
- **Logging**: Structured logging for debugging and monitoring
- **Error handling**: Graceful degradation with informative error messages

---

## MCP Server Capabilities

### Commute Server (`commute_server.py`)

**Resources**:
- `fetch_ferry_schedules(direction)` - Get ferry schedules, optionally filtered by direction
- `fetch_terminals()` - Get all ferry terminals from WSDOT API

**Tools**:
- `find_nearby_ferry_terminals(address, max_results)` - Find closest ferry terminals to an address
- `drive_time_tool(origin, destination, departure_time, arrival_time)` - Calculate drive times with mileage cost ($0.77/mile)
- `get_ferry_times(origin, destination, event_time)` - Get sailings for a specific route
- `ferry_cost(trip_date, departing_terminal, arriving_terminal, travel_mode, vehicle_size)` - Get ferry fares from WSDOT API

**Prompts**:
- `user_preferences()` - Default trip planning preferences (3 routes, 1 driving-only, 15-min buffer)
- `plan_trip(origin, destination, event_time)` - Comprehensive trip planning with ferry and car options

### Event Server (`elasticsearch_server.py`)

**Tools**:
- `search_events(start_time, end_time, topic, title, location, description_query, presenting, top_k)` - Hybrid semantic + keyword search
- `create_event(title, description, location, topic, start_time, end_time, url, presenting, talk_title)` - Add new events

---

## Notes
- All required API keys and endpoints are listed in `.env.example`
- Ferry schedules are static; for production, integrate with WSDOT real-time API
- Sample events are synthetic data for demonstration purposes (Dec 2025 - Feb 2026)
- No frontend included—interact via Claude Desktop or MCP-compatible clients
