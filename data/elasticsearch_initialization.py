"""
DEPRECATED: This module has been moved to setup/elasticsearch_setup.py

This file is kept for backward compatibility.
Please update your imports to use setup.elasticsearch_setup instead.

All functions are now available from setup.elasticsearch_setup:
- create_event_index()
- create_e5_inference_endpoint()
- create_ingest_pipeline()
- simulate_pipeline()
- bulk_index_events(events)
- load_sample_events()
- bulk_add_sample_events()
"""
import warnings

# Issue deprecation warning
warnings.warn(
    "data.elasticsearch_initialization is deprecated. "
    "Use setup.elasticsearch_setup instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from new location for backward compatibility
from setup.elasticsearch_setup import (
    create_event_index,
    create_e5_inference_endpoint,
    create_ingest_pipeline,
    simulate_pipeline,
    bulk_index_events,
    load_sample_events,
    bulk_add_sample_events,
    es,
    logger
)

__all__ = [
    'create_event_index',
    'create_e5_inference_endpoint',
    'create_ingest_pipeline',
    'simulate_pipeline',
    'bulk_index_events',
    'load_sample_events',
    'bulk_add_sample_events',
    'es',
    'logger'
]
