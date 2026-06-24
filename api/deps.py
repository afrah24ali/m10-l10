"""FastAPI dependency-injection helpers."""

from collections.abc import Generator
from typing import Any

from fastapi import Request


def get_session(request: Request) -> Generator[Any, None, None]:
    """Yield one Neo4j session per request from the shared driver."""
    driver = request.app.state.neo4j_driver
    with driver.session() as session:
        yield session


def get_weaviate(request: Request) -> Any:
    """Return the process-scoped Weaviate client constructed in lifespan."""
    return request.app.state.weaviate_client


def get_generator(request: Request) -> Any:
    """Return the process-scoped flan-t5-base generator constructed in lifespan."""
    return request.app.state.generator


def get_nlp(request: Request) -> Any:
    """Return the process-scoped spaCy pipeline constructed in lifespan."""
    return request.app.state.nlp


def get_embedder(request: Request) -> Any:
    """Return the process-scoped sentence-transformers embedder."""
    return request.app.state.embedder

def get_driver(request: Request) -> Any:
    return request.app.state.neo4j_driver