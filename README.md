# Kitsap Commute & Event Minder

A Python-based app to help Kitsap County residents plan commutes and manage events, using real-time WSDOT and Google Maps data. The application provides ferry, drive, and event creation and search. These are MCP servers that can be used with Claude Desktop or any other client that uses MCP.

## Main Components
- `commute_server.py`: MCP server for commute and ferry options
- `elasticsearch_server.py`: MCP server for event storage, search, and recommendations

## Getting Started

### 1. Set up environment variables
- Copy `.env.example` to `.env` and fill in all required API keys (Elasticsearch, Google Maps, WSDOT, Claude Desktop, etc.).

```bash
cp .env.example .env
# Edit .env and add your actual keys
```

### 2. Set up the Python environment using uv
This project uses [uv](https://github.com/astral-sh/uv) for fast, reproducible Python dependency management (see `uv.lock`).

#### a. (Optional) Initialize the uv project (if not already done)
If you are starting from scratch or want to reinitialize:
```bash
uv init
```
This will create a `pyproject.toml` if it doesn't exist.

#### b. Sync packages from pyproject.toml
To install all dependencies as specified in `pyproject.toml`:
```bash
uv sync
```

#### c. (Recommended) Start a uv-managed virtual environment
To create and activate a virtual environment using uv:
```bash
uv venv .venv
source .venv/bin/activate
```

#### d. (Alternative) Install from requirements.txt
If you prefer, you can also install from `requirements.txt`:
```bash
uv pip install -r requirements.txt
```

- If you don't have uv installed, follow the instructions at https://github.com/astral-sh/uv

### 3. Run the servers
- Start the commute server:
```bash
python commute_server.py
```
- Start the Elasticsearch event server (in a separate terminal):
```bash
python elasticsearch_server.py
```

### 4. Connect with Claude Desktop
- Ensure your `.env` file contains `CLAUDE_DESKTOP_API_KEY`.
- In Claude Desktop, add the MCP server URLs (e.g., `http://localhost:8000` for commute, `http://localhost:8001` for events) in the integrations/settings panel.
- Make sure Claude Desktop is running and can reach your local MCP servers.

---

### Notes
- All required API keys and endpoints are listed in `.env.example`.
- See code comments and inline docs for usage examples and API details.
- No frontend or backend web app is included—interact via Claude Desktop or API clients.
