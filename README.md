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

#### a. Initialize the uv project (if not already done)
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

#### c. Start a uv-managed virtual environment
To create and activate a virtual environment using uv:
```bash
uv venv .venv
source .venv/bin/activate
```

### 3. Start the servers

- To start the commute server **or** Elasticsearch event server (in separate terminals):
```bash
uv run fastmcp run <server_file.py>```

This is the standard way to run any server in this project.

### 4. Connect with Claude Desktop
- Ensure your `.env` file contains `CLAUDE_DESKTOP_API_KEY`.
- To install and connect Claude Desktop to your MCP server, run:
```bash
fastmcp install claude-desktop <server_file.py>
```
- This will set up integration and ensure Claude Desktop can reach your local MCP servers.
- You may need to inspect your Claude Desktop config.json file to ensure the correct server commands are set.

---

### Notes
- All required API keys and endpoints are listed in `.env.example`.
- See code comments and inline docs for usage examples and API details.
- No frontend or backend web app is included—interact via Claude Desktop or API clients.
