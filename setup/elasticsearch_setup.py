"""
Elasticsearch setup script for Kitsap Commute MCP.

This script manages the Elasticsearch index for events.
Embeddings are generated automatically using the semantic_text field type.

Usage:
    python setup/elasticsearch_setup.py --create-index
    python setup/elasticsearch_setup.py --load-sample-data
    python setup/elasticsearch_setup.py --all  # Run all setup steps
"""

import sys
from pathlib import Path

# Add parent directory to path to allow importing from config.py
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from config import (
    ELASTIC_ENDPOINT,
    ELASTIC_API_KEY,
    EVENT_INDEX,
    DATA_DIR,
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Elasticsearch client
es = Elasticsearch(hosts=ELASTIC_ENDPOINT, api_key=ELASTIC_API_KEY)


def create_event_index():
    """
    Create the events index with mapping for dense_vector embedding.
    Follows elasticsearch-py best practices for error handling and existence checks.
    """
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "description": {"type": "text", "copy_to": "description_vector"},
                "description_vector": {"type": "semantic_text"},
                "location": {"type": "text"},
                "topic": {"type": "keyword"},
                "start_time": {"type": "date"},
                "end_time": {"type": "date"},
                "url": {"type": "keyword"},
                "presenting": {"type": "boolean"},
                "talk_title": {"type": "text"},
            }
        }
    }
    try:
        if es.indices.exists(index=EVENT_INDEX):
            es.indices.delete(index=EVENT_INDEX)
            logger.info(f"Deleted existing index '{EVENT_INDEX}'.")
        es.indices.create(index=EVENT_INDEX, body=mapping)
        logger.info(f"Created index '{EVENT_INDEX}'.")
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise


def bulk_index_events(events):
    """
    Bulk index an array of event documents into the events index.
    Each event should be a dict matching the event schema.
    Uses the _bulk API for efficient ingestion.
    The description field is automatically copied to description_vector via copy_to in the index mapping.

    Args:
        events (list): List of event dictionaries to index
    """
    actions = [{"_index": EVENT_INDEX, "_source": event} for event in events]
    try:
        success, failed = bulk(es, actions, stats_only=True)
        logger.info(f"Bulk indexed {success} events. Failed: {failed}")
    except Exception as e:
        logger.error(f"Error during bulk indexing: {e}")
        raise


def load_sample_events():
    """
    Load sample events from data/sample_events.json.

    Returns:
        list: List of event dictionaries
    """
    try:
        events_path = DATA_DIR / "sample_events.json"
        with open(events_path, "r") as f:
            events = json.load(f)
        logger.info(f"Loaded {len(events)} events from {events_path}")
        return events
    except Exception as e:
        logger.error(f"Error loading sample events: {e}")
        raise


def bulk_add_sample_events():
    """
    Load sample events from JSON and bulk index them to the events index.
    """
    events = load_sample_events()
    bulk_index_events(events)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup Elasticsearch for Kitsap Commute MCP events"
    )
    parser.add_argument(
        "--create-index", action="store_true", help="Create the events index"
    )
    parser.add_argument(
        "--load-sample-data",
        action="store_true",
        help="Load sample events from data/sample_events.json",
    )
    parser.add_argument("--all", action="store_true", help="Run all setup steps")

    args = parser.parse_args()

    if args.all or args.create_index:
        create_event_index()
    if args.all or args.load_sample_data:
        bulk_add_sample_events()

    if not any(vars(args).values()):
        parser.print_help()
