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
WSDOT_API_KEY = os.getenv("WSDOT_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Elasticsearch
ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT", "http://localhost:9200")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
EVENT_INDEX = os.getenv("EVENT_INDEX", "events")


def validate_config():
    """Validate required environment variables are set."""
    missing = []
    if not WSDOT_API_KEY:
        missing.append("WSDOT_API_KEY")
    if not GOOGLE_MAPS_API_KEY:
        missing.append("GOOGLE_MAPS_API_KEY")

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


# Optional: Validate on import (commented out for flexibility)
# validate_config()
