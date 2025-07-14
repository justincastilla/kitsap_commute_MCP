"""
MCP server for Elasticsearch-backed event search and semantic event queries.
This server exposes tools for searching, filtering, and semantically matching events stored in Elasticsearch.
"""
import os
from fastmcp import FastMCP
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT", "http://localhost:9200")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
EVENT_INDEX = os.getenv("EVENT_INDEX", "events")


es = Elasticsearch(hosts=ELASTIC_ENDPOINT, api_key=ELASTIC_API_KEY)


mcp = FastMCP(
    name="Elasticsearch Server",
)

@mcp.tool(
    name="search_events",
    description="Search events by time range, topic, title, location, or semantic description. Returns a list of matching event docs."
)
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
    Search for events in Elasticsearch using structured and/or semantic filters.
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
        # Prepare the retriever block for hybrid RRF search
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
                            # You will need to generate the embedding for the query here. For now, use the query_vector_builder if supported, or insert the vector if you have it.
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

@mcp.tool(
    name="create_event",
    description="Create a new event in Elasticsearch. Requires title, description, location, topic, start_time, end_time, url, presenting (bool), and talk_title."
)
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

if __name__ == "__main__":
    mcp.run()
