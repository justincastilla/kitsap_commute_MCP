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

**Usage:** Load with `python setup/elasticsearch_setup.py --load-sample-data`

---

## Scripts (Deprecated)

### `elasticsearch_initialization.py`
**DEPRECATED:** This file has been moved to `setup/elasticsearch_setup.py`.

This file is kept for backward compatibility and will show a deprecation warning when imported.

**Migration:**
```python
# Old (deprecated)
from data.elasticsearch_initialization import create_event_index

# New (recommended)
from setup.elasticsearch_setup import create_event_index
```

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

# Load sample events
with open(DATA_DIR / "sample_events.json") as f:
    events = json.load(f)
```

---

## File Inventory

```
data/
├── README.md                           # This file
├── ferry_terminals.json                # 7 ferry terminals with geocoded locations
├── ferry_schedules.json                # Static schedules for major routes
├── sample_events.json                  # ~50 sample tech events for testing
└── elasticsearch_initialization.py     # DEPRECATED - backward compat shim
```
