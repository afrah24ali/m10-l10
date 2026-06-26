"""Pydantic request/response models for the recipe service.

These are the typed-boundary contracts. They must mirror the TypeScript
interfaces in `web/lib/types.ts` exactly — drift produces silent render
failures in the Next.js frontend.
"""

from typing import Any, List, Literal

from pydantic import BaseModel, Field


# --- /extract --------------------------------------------------------


class ExtractRequest(BaseModel):
    """Request body for POST /extract."""

    text: str = Field(..., min_length=1, max_length=5000)


class Entity(BaseModel):
    """A single named-entity span."""

    text: str
    label: str
    start: int
    end: int


class ExtractResponse(BaseModel):
    """Response body for POST /extract."""

    entities: List[Entity]


# --- /kg/query -------------------------------------------------------


class KGRequest(BaseModel):
    """Request body for POST /kg/query."""

    question: str = Field(..., min_length=1, max_length=5000)


class KGResponse(BaseModel):
    """Response body for POST /kg/query."""

    cypher: str
    rows: List[dict[str, Any]]
    count: int


class UnsupportedQueryDetail(BaseModel):
    """Structured detail returned on 422 from /kg/query."""

    reason: Literal["unsupported_question"]
    supported_patterns: List[str]


# --- /rag/answer -----------------------------------------------------


class RAGRequest(BaseModel):
    """Request body for POST /rag/answer."""

    question: str = Field(..., min_length=1, max_length=5000)
    k: int = Field(default=4, ge=1, le=10)


class Citation(BaseModel):
    """One citation: chunk id and retrieval score."""

    chunk_id: int
    score: float


class RAGResponse(BaseModel):
    """Response body for POST /rag/answer."""

    answer: str
    citations: List[Citation]
    grounded: bool
    confidence: float


# --- Health / readiness ---------------------------------------------


class HealthResponse(BaseModel):
    """Liveness response."""

    status: str


class ReadyDetail(BaseModel):
    """Readiness detail naming each backend's status."""

    neo4j: str
    weaviate: str