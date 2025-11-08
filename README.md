# Kitsap Commute & Event Minder

A Python-based app to help Kitsap County residents plan commutes and manage events, using real-time WSDOT and Google Maps data. The application provides ferry, drive, and event creation and search. These are MCP servers that can be used with Claude Desktop or any other client that uses MCP.

## Main Components
- `commute_server.py`: MCP server for commute and ferry options
- `elasticsearch_server.py`: MCP server for event storage, search, and recommendations
- `config.py`: Centralized configuration management
- `setup/`: One-time Elasticsearch setup scripts
- `data/`: Reference data and sample events

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

### 1. Set up environment variables

Copy `.env.example` to `.env` and fill in all required API keys:

```bash
cp .env.example .env
# Edit .env and add your actual keys:
# - GOOGLE_MAPS_API_KEY
# - WSDOT_API_KEY
# - ELASTIC_ENDPOINT (default: http://elasticsearch:9200)
# - ELASTIC_API_KEY (optional for local Elasticsearch)
```

### 2. Start all services with Docker Compose

This will start Elasticsearch and both MCP servers:

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

Services will be available at:
- **Elasticsearch**: http://localhost:9200
- **Commute Server**: http://localhost:8000
- **Event Server**: http://localhost:8001

### 3. Set up Elasticsearch (First Time Only)

After Elasticsearch is healthy, initialize the index and load sample data:

```bash
# Run setup inside the elasticsearch-server container
docker-compose exec elasticsearch-server python setup/elasticsearch_setup.py --all

# Or run steps individually:
docker-compose exec elasticsearch-server python setup/elasticsearch_setup.py --create-index
docker-compose exec elasticsearch-server python setup/elasticsearch_setup.py --create-endpoint
docker-compose exec elasticsearch-server python setup/elasticsearch_setup.py --create-pipeline
docker-compose exec elasticsearch-server python setup/elasticsearch_setup.py --load-sample-data
```

### 4. Manage services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears Elasticsearch data)
docker-compose down -v

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f commute-server
docker-compose logs -f elasticsearch-server

# Restart a service
docker-compose restart commute-server
```

### 5. Connect with Claude Desktop

To connect Claude Desktop to your Docker-based MCP servers, update your Claude Desktop config to point to the containerized servers:

```json
{
  "mcpServers": {
    "kitsap-commute": {
      "url": "http://localhost:8000"
    },
    "kitsap-events": {
      "url": "http://localhost:8001"
    }
  }
}
```

---

## Alternative: Running without Docker

If you prefer to run without Docker:

1. Install dependencies:
   ```bash
   pip install elasticsearch fastmcp pydantic python-dotenv requests
   ```

2. Set up `.env` file with your API keys

3. Run servers directly:
   ```bash
   python commute_server.py
   python elasticsearch_server.py  # in a separate terminal
   ```

---

### Notes
- All required API keys and endpoints are listed in `.env.example`.
- See code comments and inline docs for usage examples and API details.
- No frontend or backend web app is included—interact via Claude Desktop or API clients.
