"""
Script to manage Elasticsearch index, embedding inference endpoint, and ingest pipeline for events.
Each operation is a separate function for modularity.
"""
import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT", "http://localhost:9200")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
EVENT_INDEX = "events"
EMBEDDING_DIM = 384  # E5-small default
PIPELINE_ID = "event-description-embed-pipeline"

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
            print(f"Deleted existing index '{EVENT_INDEX}'.")
        es.indices.create(index=EVENT_INDEX, body=mapping)
        print(f"Created index '{EVENT_INDEX}'.")
    except Exception as e:
        print(f"Error creating index: {e}")

def create_e5_inference_endpoint():
    """
    Create an inference endpoint for the E5 embedding model using the Elasticsearch ML Inference API.
    Uses elasticsearch-py best practices and follows the documented template.
    """
    try:
        resp = es.options(timeout="60s").inference.put(
            task_type="text_embedding",
            inference_id="e5_event_description",
            inference_config={
                "service": "elasticsearch",
                "service_settings": {
                    "model_id": ".multilingual-e5-small",
                    "num_threads": 2,  # Or 1 or another reasonable value for your cluster
                    "num_allocations": 1  # Or another value, or use "adaptive_allocations"
                }
            }
        )
        print(f"Created inference endpoint 'e5_event_description': {resp}")
    except Exception as e:
        print(f"Error creating inference endpoint: {e}")

def create_ingest_pipeline():
    """
    Create an ingest pipeline that uses the E5 inference endpoint to embed event descriptions.
    Checks for existence before creating. Follows elasticsearch-py best practices.
    """
    pipeline = {
        "description": "Embed event descriptions using E5 model via inference processor.",
        "processors": [
            {
                "inference": {
                    "model_id": "e5_event_description",  # Inference endpoint ID
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
            print(f"Ingest pipeline '{PIPELINE_ID}' already exists.")
        else:
            es.ingest.put_pipeline(id=PIPELINE_ID, body=pipeline)
            print(f"Created ingest pipeline '{PIPELINE_ID}'.")
    except Exception as e:
        print(f"Error creating ingest pipeline: {e}")

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
        print("--- Pipeline simulation result ---")
        from pprint import pprint
        pprint(resp)
    except Exception as e:
        print(f"Error simulating pipeline: {e}")

def bulk_index_events(events):
    """
    Bulk index an array of event documents into the events index.
    Each event should be a dict matching the event schema.
    Uses the _bulk API for efficient ingestion.
    """
    from elasticsearch.helpers import bulk
    actions = [
        {
            "_index": EVENT_INDEX,
            "_source": event
        } for event in events
    ]
    try:
        success, failed = bulk(es, actions, stats_only=True, pipeline=PIPELINE_ID)
        print(f"Bulk indexed {success} events. Failed: {failed}")
    except Exception as e:
        print(f"Error during bulk indexing: {e}")

import json

def search_events(
    start_time: str = None,
    end_time: str = None,
    topic: str = None,
    title: str = None,
    location: str = None,
    description_query: str = None,
    presenting: bool = None,
    top_k: int = 10
) -> dict:
    """
    Standalone version of the search_events function for manual testing.
    """
    must = []
    if start_time and end_time:
        must.append({"range": {"start_time": {"gte": start_time, "lte": end_time}}})
    if topic:
        must.append({"match": {"topic": topic}})
    if title:
        must.append({"match": {"title": title}})
    if location:
        must.append({"match": {"location": location}})
    if presenting is not None:
        must.append({"term": {"presenting": presenting}})

    if description_query:
        retriever = {
            "rrf": {
                "retrievers": [
                    {
                        "standard": {
                            "query": {
                                "multi_match": {
                                    "query": description_query,
                                    "fields": ["title", "description", "topic"]
                                }
                            }
                        }
                    },
                    {
                        "knn": {
                            "field": "description_vector",
                            "query_vector_builder": {
                                "text_embedding": {
                                    "model_id": "e5_event_description",
                                    "model_text": description_query
                                }
                            },
                            "k": top_k,
                            "num_candidates": 3 * top_k
                        }
                    }
                ],
                "rank_window_size": top_k,
                "rank_constant": 20
            }
        }
        resp = es.search(
            index=EVENT_INDEX,
            retriever=retriever,
            size=top_k,
            _source={"excludes": ["description_vector"]}
        )
    else:
        query = {"bool": {"must": must}} if must else {"match_all": {}}
        resp = es.search(index=EVENT_INDEX, query=query, size=top_k, _source={"excludes": ["description_vector"]})
    events = [hit["_source"] for hit in resp["hits"]["hits"]]
    return {"events": events}


def bulk_add_king_county_events():
    """
    Load king_county_tech_events.json and bulk index all events to the events index.
    """
    try:
        import os
        events_path = 'king_county_tech_events.json'
        with open(events_path, "r") as f:
            events = json.load(f)
        print(f"Loaded {len(events)} events from king_county_tech_events.json.")
        bulk_index_events(events)
    except Exception as e:
        print(f"Error loading or indexing king county events: {e}")


def create_event(
    title: str,
    description: str,
    location: str,
    topic: str,
    start_time: str,
    end_time: str,
    url: str = None,
    presenting: bool = False,
    talk_title: str = None
) -> dict:
    """
    Create a new event in Elasticsearch. Embeds the description for semantic search (placeholder embedding).
    """

    event_doc = {
        "title": title,
        "description": description,
        "location": location,
        "topic": topic,
        "start_time": start_time,
        "end_time": end_time,
        "url": url,
        "presenting": presenting,
        "talk_title": talk_title,
    }
    resp = es.index(index=EVENT_INDEX, document=event_doc, pipeline="event-description-embed-pipeline")
    return {"event_id": resp["_id"], "event": event_doc}

sample_event = {
    "title": "Kitsap Tech Meetup",
    "description": "This event brings together software developers, IT professionals, and tech entrepreneurs from across the Kitsap Peninsula. Attendees will have the opportunity to network, share ideas, and learn about emerging trends in artificial intelligence and cloud computing. Whether you're a seasoned engineer or just beginning your tech journey, you'll find valuable insights and connections at this meetup.",
    "location": "Sheridan Park Community Center 680 Lebo Blvd. Bremerton, WA 98310",
    "topic": "Technology",
    "start_time": "2025-07-15T18:00:00-07:00",
    "end_time": "2025-07-15T20:00:00-07:00",
    "url": "https://www.kitsaptechmeetup.com",
    "presenting": True,
    "talk_title": "The Future of AI in Kitsap"
}


if __name__ == "__main__":
    print("Elasticsearch initialization script started.")
    # simulate_pipeline()
       
    # create_event_index()
    
    # bulk_add_king_county_events()
    
    # result = create_event(**sample_event)
    # print(result)
    
    # results = search_events(description_query="crypto strategies")
    # for result in results["events"]:
    #     print(result["title"])
    #     print(result["description"])
    #     print("---")
