"""Pydantic request/response models for the recipe service.

These are the typed-boundary contracts. They must mirror the TypeScript
interfaces in `web/lib/types.ts` exactly — drift produces silent render
failures in the Next.js frontend.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SENTINEL_ANSWER = "I cannot answer this from the available sources"

# --- /extract --------------------------------------------------------

class ExtractRequest(BaseModel):
    """Request body for POST /extract.

    The request field has a length constraint that gates 422 on empty
    or oversized input.
    """
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, max_length=5000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value

class Entity(BaseModel):
    """A single named-entity span.

    Field names must match the corresponding TypeScript Entity
    interface in `web/lib/types.ts` exactly.
    """
    model_config = ConfigDict(extra="forbid")

    text: str
    label: str
    start: int
    end: int


class ExtractResponse(BaseModel):
    """Response body for POST /extract.

    Per the Evaluation Methodology, the returned list is ordered by
    start offset ascending.
    """
    model_config = ConfigDict(extra="forbid")

    entities: list[Entity]


# --- /kg/query -------------------------------------------------------

class KGRequest(BaseModel):
    """Request body for POST /kg/query."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=500)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be empty")
        return value


class KGResponse(BaseModel):
    """Response body for POST /kg/query."""

    model_config = ConfigDict(extra="forbid")

    cypher: str
    rows: list[dict[str, Any]]
    count: int


class UnsupportedQueryDetail(BaseModel):
    """Structured detail returned on 422 from /kg/query."""

    model_config = ConfigDict(extra="forbid")

    reason: Literal["unsupported_question"]
    supported_patterns: list[str]


# --- /rag/answer -----------------------------------------------------

class RAGRequest(BaseModel):
    """Request body for POST /rag/answer.

    The question field has a length constraint; `k` is a bounded
    integer with a default.
    """
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=500)
    k: int = Field(default=4, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value


class Citation(BaseModel):
    """One citation: chunk id and retrieval score.

    Field names must match the TypeScript Citation interface.
    """
    model_config = ConfigDict(extra="forbid")

    chunk_id: int
    score: float


class RAGResponse(BaseModel):
    """Response body for POST /rag/answer.

    Grounding contract: when grounded is true, citations must not be empty.
    """
    model_config = ConfigDict(extra="forbid")

    answer: str
    citations: list[Citation]
    confidence: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def enforce_grounding_contract(self) -> "RAGResponse":
        if self.answer == SENTINEL_ANSWER:
            if self.citations:
                raise ValueError("sentinel response must not include citations")
            if self.confidence != 0.0:
                raise ValueError("sentinel response confidence must be 0.0")
        elif not self.citations:
            raise ValueError("non-sentinel answers must include citations")

        return self


# --- Health / readiness ---------------------------------------------

class HealthResponse(BaseModel):
    """Liveness response."""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]


class ReadyDetail(BaseModel):
    """Readiness detail naming each backend's status."""
    model_config = ConfigDict(extra="forbid")

    status: str
    neo4j: bool
    weaviate: bool
    errors: list[str] = []