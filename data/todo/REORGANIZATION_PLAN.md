# Project Reorganization Plan

**Date:** 2025-11-08
**Goal:** Clean up testing files and improve data organization
**Approach:** Option B - Simple, clear, best practices for demo application

---

## Current State Analysis

### Problems Identified

1. **`data/elasticsearch_initialization.py` (299 lines) doing too much:**
   - ✅ Setup functions (index creation, inference endpoint, pipeline)
   - ❌ Duplicate `search_events()` (already in elasticsearch_server.py:27-100)
   - ❌ Duplicate `create_event()` (already in elasticsearch_server.py:102-133)
   - ❌ Sample test data mixed with production code
   - ❌ Commented-out test code in `__main__`

2. **Data files lack clarity:**
   - `static_ferry_schedules.json` - not obvious it's static reference data
   - `king_county_tech_events.json` - not clear it's sample/seed data
   - No documentation on what each file is for

3. **No actual test infrastructure:**
   - No `tests/` directory
   - Commented-out test code scattered in scripts
   - Ad-hoc testing via `__main__` blocks

---

## Target Structure

```
kitsap_commute_MCP/
├── commute_server.py                 # Main MCP server for commute
├── elasticsearch_server.py           # Main MCP server for events
├── utilities.py                      # Shared utilities
├── config.py                         # NEW: Centralized configuration
│
├── data/                             # All data files
│   ├── README.md                     # NEW: Explains each file
│   ├── ferry_terminals.json          # Reference: Ferry terminal locations
│   ├── ferry_schedules.json          # Reference: Static ferry schedules (RENAMED)
│   └── sample_events.json            # Sample: King County tech events (RENAMED)
│
└── setup/                            # NEW: One-time setup scripts
    ├── __init__.py
    └── elasticsearch_setup.py        # Clean setup functions only
```

---

## Detailed Changes

### 1. Create `config.py` - Centralized Configuration

**New file:** `config.py`

```python
"""
Centralized configuration for Kitsap Commute MCP servers.
Loads environment variables and validates required settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"

# API Keys
WSDOT_API_KEY = os.getenv('WSDOT_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Elasticsearch
ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT", "http://localhost:9200")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
EVENT_INDEX = os.getenv("EVENT_INDEX", "events")

# Elasticsearch model settings
EMBEDDING_DIM = 384  # E5-small default
EMBEDDING_MODEL_ID = ".multilingual-e5-small"
INFERENCE_ENDPOINT_ID = "e5_event_description"
PIPELINE_ID = "event-description-embed-pipeline"

def validate_config():
    """Validate required environment variables are set."""
    missing = []
    if not WSDOT_API_KEY:
        missing.append("WSDOT_API_KEY")
    if not GOOGLE_MAPS_API_KEY:
        missing.append("GOOGLE_MAPS_API_KEY")

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Validate on import (optional - can be called explicitly instead)
# validate_config()
```

**Benefits:**
- Single source of truth for all configuration
- Easy to test (mock config values)
- Clear documentation of all settings
- Validation in one place

---

### 2. Split `data/elasticsearch_initialization.py`

#### 2a. Create `setup/elasticsearch_setup.py`

**New file:** `setup/elasticsearch_setup.py`

**Contains ONLY:**
- `create_event_index()` - Creates Elasticsearch index with mappings
- `create_e5_inference_endpoint()` - Sets up ML inference endpoint
- `create_ingest_pipeline()` - Creates embedding pipeline
- `simulate_pipeline()` - Tests the pipeline
- `bulk_index_events(events)` - Generic bulk indexing utility
- `load_sample_events()` - NEW: Loads sample events from JSON

**Removes:**
- ❌ Duplicate `search_events()` function
- ❌ Duplicate `create_event()` function
- ❌ `sample_event` dict (move to JSON if needed)

**New `__main__` block:**
```python
if __name__ == "__main__":
    """
    Elasticsearch setup script for Kitsap Commute MCP.

    Usage:
        python setup/elasticsearch_setup.py --create-index
        python setup/elasticsearch_setup.py --create-endpoint
        python setup/elasticsearch_setup.py --create-pipeline
        python setup/elasticsearch_setup.py --load-sample-data
        python setup/elasticsearch_setup.py --all  # Run all setup steps
    """
    import argparse

    parser = argparse.ArgumentParser(description="Setup Elasticsearch for events")
    parser.add_argument("--create-index", action="store_true")
    parser.add_argument("--create-endpoint", action="store_true")
    parser.add_argument("--create-pipeline", action="store_true")
    parser.add_argument("--load-sample-data", action="store_true")
    parser.add_argument("--all", action="store_true")

    args = parser.parse_args()

    if args.all or args.create_index:
        create_event_index()
    if args.all or args.create_endpoint:
        create_e5_inference_endpoint()
    if args.all or args.create_pipeline:
        create_ingest_pipeline()
    if args.all or args.load_sample_data:
        events = load_sample_events()
        bulk_index_events(events)
```

#### 2b. Create backward compatibility shim

**Updated file:** `data/elasticsearch_initialization.py`

```python
"""
DEPRECATED: This module has been moved to setup/elasticsearch_setup.py

This file is kept for backward compatibility.
Please update your imports to use setup/elasticsearch_setup instead.
"""
import warnings
from setup.elasticsearch_setup import *

warnings.warn(
    "data/elasticsearch_initialization.py is deprecated. "
    "Use setup/elasticsearch_setup.py instead.",
    DeprecationWarning,
    stacklevel=2
)
```

**Benefits:**
- Existing scripts don't break
- Clear deprecation warning
- Easy migration path

---

### 3. Rename Data Files

**Changes:**
```bash
# Before
data/static_ferry_schedules.json
data/king_county_tech_events.json

# After
data/ferry_schedules.json          # Clearer: these ARE the schedules
data/sample_events.json            # Clearer: these are samples
```

**Update imports in:**
- `utilities.py:47` - Update path to `ferry_schedules.json`
- `setup/elasticsearch_setup.py` - Update path to `sample_events.json`

---

### 4. Add `data/README.md`

**New file:** `data/README.md`

```markdown
# Data Directory

This directory contains reference data and sample data for the Kitsap Commute MCP servers.

## Reference Data (Static)

### `ferry_terminals.json`
List of Washington State Ferry terminals with geocoded locations.

**Schema:**
- `name`: Terminal code name (e.g., "Bremerton", "Seattle")
- `display_name`: Human-readable name with location
- `address`: Full street address
- `lat`, `lng`: Coordinates for distance calculations
- `place_id`: Google Maps place ID
- `city`, `neighborhood`, `county`: Location hierarchy

**Source:** Manual compilation from WSDOT ferry terminal data and Google Maps geocoding.

**Updates:** Rarely - only when new terminals open or addresses change.

---

### `ferry_schedules.json`
Static ferry schedules for major Kitsap routes.

**Schema:**
- Route key format: `"{origin}-{destination}"` (lowercase)
- Each route contains:
  - `direction`: Array of directions (e.g., `["east", "king"]`)
  - `weekday`: Array of departure times
  - `weekend`: Array of departure times

**Source:** WSDOT ferry schedules (simplified/static for demo purposes).

**Updates:** Periodically - when ferry schedules change seasonally.

**Note:** For production use, integrate with WSDOT real-time API.

---

## Sample Data

### `sample_events.json`
Sample tech events in King County for testing and demonstration.

**Schema:**
- `title`: Event name
- `description`: Full event description (used for semantic search)
- `location`: Event address
- `topic`: Event category/topic (keyword)
- `start_time`, `end_time`: ISO 8601 datetime strings
- `url`: Event URL (optional)
- `presenting`: Boolean - whether you're presenting
- `talk_title`: Your talk title if presenting (optional)

**Source:** Synthetic data for demonstration purposes.

**Updates:** As needed for demos and testing.

**Usage:** Load with `setup/elasticsearch_setup.py --load-sample-data`

---

## Usage

### Loading Sample Events
```bash
python setup/elasticsearch_setup.py --load-sample-data
```

### Accessing Data in Code
```python
from config import DATA_DIR
import json

# Load ferry terminals
with open(DATA_DIR / "ferry_terminals.json") as f:
    terminals = json.load(f)

# Load schedules
with open(DATA_DIR / "ferry_schedules.json") as f:
    schedules = json.load(f)
```
```

---

### 5. Update Server Files

#### `commute_server.py`
**Changes:**
- Remove API key validation at module level (move to config.py)
- Import from `config` instead of `os.getenv()`
- Update data file paths to use `config.DATA_DIR`

**Before:**
```python
wdot_api_key = os.getenv('WSDOT_API_KEY')
if not wdot_api_key:
    raise Exception("WSDOT_API_KEY environment variable not set")
```

**After:**
```python
from config import WSDOT_API_KEY, GOOGLE_MAPS_API_KEY, DATA_DIR
```

#### `elasticsearch_server.py`
**Changes:**
- Import from `config` instead of individual `os.getenv()` calls
- Remove `load_dotenv()` (handled by config)

**Before:**
```python
load_dotenv()
ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT", "http://localhost:9200")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
EVENT_INDEX = os.getenv("EVENT_INDEX", "events")
```

**After:**
```python
from config import ELASTIC_ENDPOINT, ELASTIC_API_KEY, EVENT_INDEX
```

#### `utilities.py`
**Changes:**
- Update schedule path to `DATA_DIR / 'ferry_schedules.json'`

**Before:**
```python
path = os.path.join(os.path.dirname(__file__), 'data', 'static_ferry_schedules.json')
```

**After:**
```python
from config import DATA_DIR
# ...
path = DATA_DIR / 'ferry_schedules.json'
```

---

### 6. Update Main README

**Add section:**

```markdown
## Project Structure

```
kitsap_commute_MCP/
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

## Setup Elasticsearch (First Time Only)

```bash
# Create index, inference endpoint, pipeline, and load sample data
python setup/elasticsearch_setup.py --all

# Or run steps individually:
python setup/elasticsearch_setup.py --create-index
python setup/elasticsearch_setup.py --create-endpoint
python setup/elasticsearch_setup.py --create-pipeline
python setup/elasticsearch_setup.py --load-sample-data
```
```

---

## Implementation Checklist

### Phase 1: Create New Files
- [ ] Create `config.py`
- [ ] Create `setup/` directory
- [ ] Create `setup/__init__.py`
- [ ] Create `setup/elasticsearch_setup.py` (clean version)
- [ ] Create `data/README.md`

### Phase 2: Rename Files
- [ ] Rename `data/static_ferry_schedules.json` → `data/ferry_schedules.json`
- [ ] Rename `data/king_county_tech_events.json` → `data/sample_events.json`

### Phase 3: Update Existing Files
- [ ] Update `commute_server.py` to use config
- [ ] Update `elasticsearch_server.py` to use config
- [ ] Update `utilities.py` to use config and new paths
- [ ] Replace `data/elasticsearch_initialization.py` with backward compatibility shim

### Phase 4: Documentation
- [ ] Update main `README.md` with new structure
- [ ] Add setup instructions using new scripts

### Phase 5: Testing
- [ ] Test `commute_server.py` still runs
- [ ] Test `elasticsearch_server.py` still runs
- [ ] Test `setup/elasticsearch_setup.py --all` works
- [ ] Test backward compatibility imports (should show deprecation warning)

### Phase 6: Commit
- [ ] Commit changes with descriptive message
- [ ] Push to branch

---

## Benefits of This Reorganization

1. **Clarity:** Clear separation of concerns
   - Production code (servers, utilities)
   - Configuration (config.py)
   - Data (data/)
   - Setup scripts (setup/)

2. **Maintainability:**
   - No duplicate code
   - Single source of truth for config
   - Clear documentation

3. **Best Practices:**
   - Centralized configuration
   - Proper file naming
   - Documentation at each level
   - Backward compatibility

4. **Demo-Ready:**
   - Easy to understand structure
   - Clear setup process
   - Well-documented data

---

## Migration Notes

### For Existing Users

If you have scripts importing from `data/elasticsearch_initialization.py`:

**Old:**
```python
from data.elasticsearch_initialization import create_event_index
```

**New (recommended):**
```python
from setup.elasticsearch_setup import create_event_index
```

**Backward compatible (with warning):**
The old import will still work but will show a deprecation warning.

---

## Future Enhancements (Not in This Plan)

- [ ] Add proper pytest test suite (`tests/`)
- [ ] Add logging configuration to `config.py`
- [ ] Add data validation schemas (Pydantic)
- [ ] Add CLI for common operations
- [ ] Add development tools (pre-commit, linting)

---

**End of Reorganization Plan**
