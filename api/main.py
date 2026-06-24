"""FastAPI application — recipe service."""

from __future__ import annotations
# pyrefly: ignore [missing-import]
import spacy
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any


# pyrefly: ignore [missing-import]
import weaviate
# pyrefly: ignore [missing-import]
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from neo4j import GraphDatabase
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer

from .deps import get_embedder, get_generator, get_nlp, get_session, get_weaviate
from .kg import UnsupportedQueryError, get_supported_patterns, run_kg_query
from .models import (
    Entity,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    KGRequest,
    KGResponse,
    RAGRequest,
    RAGResponse,
    ReadyDetail,
    UnsupportedQueryDetail,
)
from .nlp import extract_entities
from .rag import answer_question

try:
    from .nlp import load_pipeline
except ImportError:
    from .nlp import load_nlp as load_pipeline

try:
    from .rag import load_generator
except ImportError:
    from .m8_rag import load_generator


WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
EMBEDDER_MODEL = os.getenv("EMBEDDER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load process-scoped resources once.

    Do not load spaCy, Neo4j, Weaviate, embedder, or generator inside endpoints.
    """
    app.state.nlp = spacy.load("en_core_web_sm")

    app.state.neo4j_driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        connection_timeout=2,
    )

    app.state.weaviate_client = weaviate.Client(WEAVIATE_URL)

    app.state.embedder = SentenceTransformer(EMBEDDER_MODEL)

    app.state.generator = load_generator()

    try:
        yield
    finally:
        app.state.neo4j_driver.close()

        close = getattr(app.state.weaviate_client, "close", None)
        if callable(close):
            close()


app = FastAPI(
    title="M10 Recipe Service",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.perf_counter()
    status_code = 500

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    finally:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        print(
            json.dumps(
                {
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status": status_code,
                    "latency_ms": latency_ms,
                }
            )
        )


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    """
    Liveness probe.

    This must not touch Neo4j or Weaviate.
    """
    return HealthResponse(status="ok")


@app.get("/readyz", response_model=ReadyDetail)
@app.get("/readyz", response_model=ReadyDetail)
def readyz(
    session: Any = Depends(get_session),
    weaviate_client: Any = Depends(get_weaviate),
) -> ReadyDetail:
    """
    Readiness probe.

    This checks Neo4j and Weaviate.
    """
    neo4j_ok = True
    weaviate_ok = True
    errors: list[str] = []

    try:
        result = session.run("RETURN 1 AS ok")
        row = result.single()

        if row is None:
            neo4j_ok = False
            errors.append("Neo4j query returned no rows")
        else:
            row_data = row.data()

            if row_data.get("ok") != 1 and row_data.get("n") != 1:
                neo4j_ok = False
                errors.append("Neo4j query did not return 1")

    except Exception as exc:
        neo4j_ok = False
        errors.append(f"Neo4j connection error: {exc}")

    try:
        if not weaviate_client.is_ready():
            weaviate_ok = False
            errors.append("Weaviate client is not ready")
    except Exception as exc:
        weaviate_ok = False
        errors.append(f"Weaviate connection error: {exc}")

    ready_detail = ReadyDetail(
        status="ready" if neo4j_ok and weaviate_ok else "not_ready",
        neo4j=neo4j_ok,
        weaviate=weaviate_ok,
        errors=errors,
    )

    if not neo4j_ok or not weaviate_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ready_detail.model_dump(),
        )

    return ready_detail


@app.post("/extract", response_model=ExtractResponse)
def extract(
    req: ExtractRequest,
    nlp: Any = Depends(get_nlp),
) -> ExtractResponse:
    entities = extract_entities(req.text, nlp)
    return ExtractResponse(entities=entities)


@app.post("/kg/query", response_model=KGResponse)
def kg_query(
    req: KGRequest,
    session: Any = Depends(get_session),
) -> KGResponse:
    """
    Run the W9B deterministic mapper and execute the resulting Cypher.
    """
    try:
        return run_kg_query(req.question, session)

    except UnsupportedQueryError as exc:
        patterns = (
            getattr(exc, "supported_patterns", None)
            or getattr(exc, "patterns", None)
            or get_supported_patterns()
        )

        detail = UnsupportedQueryDetail(
            reason="unsupported_question",
            supported_patterns=list(patterns),
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail.model_dump(),
        ) from exc


@app.post("/rag/answer", response_model=RAGResponse)
def rag_answer(
    req: RAGRequest,
    weaviate_client: Any = Depends(get_weaviate),
    generator: Any = Depends(get_generator),
    embedder: Any = Depends(get_embedder),
) -> RAGResponse:
    return answer_question(
        question=req.question,
        k=req.k,
        weaviate_client=weaviate_client,
        generator=generator,
        embedder=embedder,
    )