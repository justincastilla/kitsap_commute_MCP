"""
Elasticsearch setup script for Kitsap Commute MCP.

This script manages Elasticsearch index, embedding inference endpoint,
and ingest pipeline for events. Each operation is a separate function
for modularity.

Usage:
    python setup/elasticsearch_setup.py --create-index
    python setup/elasticsearch_setup.py --create-endpoint
    python setup/elasticsearch_setup.py --create-pipeline
    python setup/elasticsearch_setup.py --load-sample-data
    python setup/elasticsearch_setup.py --all  # Run all setup steps
"""
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from config import (
    ELASTIC_ENDPOINT,
    ELASTIC_API_KEY,
    EVENT_INDEX,
    EMBEDDING_DIM,
    EMBEDDING_MODEL_ID,
    INFERENCE_ENDPOINT_ID,
    PIPELINE_ID,
    DATA_DIR
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
                "description": {"type": "text"},
                "description_vector": {
                    "type": "dense_vector",
                    "dims": EMBEDDING_DIM,
                    "index": True,
                    "similarity": "cosine"
                },
                "location": {"type": "text"},
                "topic": {"type": "keyword"},
                "start_time": {"type": "date"},
                "end_time": {"type": "date"},
                "url": {"type": "keyword"},
                "presenting": {"type": "boolean"},
                "talk_title": {"type": "text"}
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


def create_e5_inference_endpoint():
    """
    Create an inference endpoint for the E5 embedding model using the
    Elasticsearch ML Inference API. Uses elasticsearch-py best practices
    and follows the documented template.
    """
    try:
        resp = es.options(timeout="60s").inference.put(
            task_type="text_embedding",
            inference_id=INFERENCE_ENDPOINT_ID,
            inference_config={
                "service": "elasticsearch",
                "service_settings": {
                    "model_id": EMBEDDING_MODEL_ID,
                    "num_threads": 2,
                    "num_allocations": 1
                }
            }
        )
        logger.info(f"Created inference endpoint '{INFERENCE_ENDPOINT_ID}': {resp}")
    except Exception as e:
        logger.error(f"Error creating inference endpoint: {e}")
        raise


def create_ingest_pipeline():
    """
    Create an ingest pipeline that uses the E5 inference endpoint to embed
    event descriptions. Checks for existence before creating. Follows
    elasticsearch-py best practices.
    """
    pipeline = {
        "description": "Embed event descriptions using E5 model via inference processor.",
        "processors": [
            {
                "inference": {
                    "model_id": INFERENCE_ENDPOINT_ID,
                    "input_output": [
                        {
                            "input_field": "description",
                            "output_field": "description_vector"
                        }
                    ],
                    "inference_config": {
                        "text_embedding": {}
                    }
                }
            }
        ]
    }
    try:
        existing = es.ingest.get_pipeline(id=PIPELINE_ID, ignore=[404])
        if PIPELINE_ID in existing:
            logger.info(f"Ingest pipeline '{PIPELINE_ID}' already exists.")
        else:
            es.ingest.put_pipeline(id=PIPELINE_ID, body=pipeline)
            logger.info(f"Created ingest pipeline '{PIPELINE_ID}'.")
    except Exception as e:
        logger.error(f"Error creating ingest pipeline: {e}")
        raise


def simulate_pipeline():
    """
    Simulate the ingest pipeline with a dummy event document.
    """
    dummy_event = {
        "title": "Test Event",
        "description": "A fun event for all ages about science and technology.",
        "location": "123 Main St, Seattle, WA 98101",
        "topic": "Science",
        "start_time": "2025-08-01T15:00:00-07:00",
        "end_time": "2025-08-01T17:00:00-07:00",
        "url": "https://example.com/event",
        "presenting": True,
        "talk_title": "The Future of Robotics"
    }
    try:
        resp = es.ingest.simulate(
            id=PIPELINE_ID,
            body={"docs": [{"_source": dummy_event}]}
        )
        logger.info("--- Pipeline simulation result ---")
        from pprint import pprint
        pprint(resp)
    except Exception as e:
        logger.error(f"Error simulating pipeline: {e}")
        raise


def bulk_index_events(events):
    """
    Bulk index an array of event documents into the events index.
    Each event should be a dict matching the event schema.
    Uses the _bulk API for efficient ingestion.

    Args:
        events (list): List of event dictionaries to index
    """
    actions = [
        {
            "_index": EVENT_INDEX,
            "_source": event
        } for event in events
    ]
    try:
        success, failed = bulk(es, actions, stats_only=True, pipeline=PIPELINE_ID)
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
        events_path = DATA_DIR / 'sample_events.json'
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
    parser.add_argument("--create-index", action="store_true",
                        help="Create the events index")
    parser.add_argument("--create-endpoint", action="store_true",
                        help="Create the E5 inference endpoint")
    parser.add_argument("--create-pipeline", action="store_true",
                        help="Create the embedding ingest pipeline")
    parser.add_argument("--simulate", action="store_true",
                        help="Simulate the pipeline with test data")
    parser.add_argument("--load-sample-data", action="store_true",
                        help="Load sample events from data/sample_events.json")
    parser.add_argument("--all", action="store_true",
                        help="Run all setup steps")

    args = parser.parse_args()

    if args.all or args.create_index:
        create_event_index()
    if args.all or args.create_endpoint:
        create_e5_inference_endpoint()
    if args.all or args.create_pipeline:
        create_ingest_pipeline()
    if args.simulate:
        simulate_pipeline()
    if args.all or args.load_sample_data:
        bulk_add_sample_events()

    if not any(vars(args).values()):
        parser.print_help()
