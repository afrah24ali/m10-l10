"""FastAPI application — recipe service.

This module wires the path operations, lifespan, and CORS middleware.

Discipline gates the autograder enforces:
- Neo4j driver, Weaviate client, spaCy pipeline, and the flan-t5-base
  generator are constructed exactly once per process inside `lifespan`.
- `CORSMiddleware` is registered with `allow_origins=[WEB_ORIGIN]`.
- `/extract`, `/kg/query`, `/rag/answer` use Pydantic shapes from
  `models.py` (no anonymous dicts; use Pydantic v2 idioms (model_dump, not the deprecated v1 serialization shortcut)).
- `/kg/query` converts `UnsupportedQueryError` to 422 with structured
  detail (`{"reason": "unsupported_question", "supported_patterns": [...]}`).
- `/readyz` probes Neo4j (`RETURN 1`) AND Weaviate (`client.is_ready()`)
  within 2 seconds; failure → 503.
- `/healthz` does NOT touch Neo4j or Weaviate.
"""

import os
from contextlib import asynccontextmanager
from neo4j import GraphDatabase
import spacy
import weaviate
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel

from .auth import create_access_token, require_api_key_or_jwt, require_jwt_admin,verify_jwt
from .deps import get_embedder, get_generator, get_nlp, get_session, get_weaviate
from .models import (
    Entity,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    KGRequest,
    KGResponse,
    RAGRequest,
    RAGResponse,
    UnsupportedQueryDetail,
)

WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


DEV_USER = {
    "username": "demo",
    "password_hash": "$2b$12$2nQ1Ai9MKY7PoCJt14Bud.DuBYCE39MVWULoBvJtJaxR8i4txLQB6",
}

def load_generator():
    return pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
    )
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Process-scoped resource setup and teardown.

    Keep your original Module 10 lifespan code here.
    It should create Neo4j, Weaviate, spaCy, generator, and embedder once.
    """

    app.state.neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
auth=(
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "password"),
        ),    )

    app.state.weaviate_client = weaviate.Client(
        os.getenv("WEAVIATE_URL", "http://localhost:8080")
    )

    app.state.nlp = spacy.load("en_core_web_sm")

    app.state.generator = load_generator()


    app.state.embedder = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    try:
        yield
    finally:
        app.state.neo4j_driver.close()


app = FastAPI(title="M10 Recipe Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """Login endpoint.

    Accepts {"username": "...", "password": "..."}.
    Returns {"access_token": "...", "token_type": "bearer"}.
    """

    if req.username != DEV_USER["username"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not pwd_context.verify(req.password, DEV_USER["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(subject=req.username)
    return LoginResponse(access_token=token)


@app.get("/admin/echo")
def admin_echo(payload: dict = Depends(require_jwt_admin)):

    """JWT-only test endpoint.

    API key should NOT work here.
    Valid Bearer JWT should return the decoded JWT payload.
    """
    return payload


@app.post("/extract", response_model=ExtractResponse)
def extract(
    req: ExtractRequest,
    auth=Depends(require_api_key_or_jwt),
    nlp=Depends(get_nlp),
):
    """Run spaCy NER on the input text; return entities ordered by `start`.

    Returns ExtractResponse with entities sorted by `start` ascending.
    """

    # PUT YOUR ORIGINAL /extract BODY HERE.
    #
    # Do NOT leave this empty.
    # Do NOT return anonymous dicts if your models expect ExtractResponse.
    #
    # Example shape only:
    # doc = nlp(req.text)
    # entities = [
    #     Entity(
    #         text=ent.text,
    #         label=ent.label_,
    #         start=ent.start_char,
    #         end=ent.end_char,
    #     )
    #     for ent in doc.ents
    # ]
    # entities.sort(key=lambda entity: entity.start)
    # return ExtractResponse(entities=entities)

    doc = nlp(req.text)
    entities = [
        Entity(
            text=ent.text,
            label=ent.label_,
            start=ent.start_char,
            end=ent.end_char,
        )
        for ent in doc.ents
    ]
    entities.sort(key=lambda entity: entity.start)
    return ExtractResponse(entities=entities)


@app.post("/kg/query", response_model=KGResponse)
def kg_query(
    req: KGRequest,
    auth=Depends(require_api_key_or_jwt),
    session=Depends(get_session),
):
    """Run the W9B mapper and execute the resulting Cypher.

    Returns KGResponse(cypher=..., rows=[r.data() for r in session.run(...)], count=len(rows)).
    UnsupportedQueryError → HTTPException(422, detail=UnsupportedQueryDetail(...).model_dump()).
    """

    # PUT YOUR ORIGINAL /kg/query BODY HERE.
    #
    # The body depends on your mapper function name.
    # I cannot safely invent it because you did not paste that file.
    #
    # Your final body should do something like:
    # try:
    #     cypher = map_question_to_cypher(req.question)
    # except UnsupportedQueryError:
    #     detail = UnsupportedQueryDetail(
    #         reason="unsupported_question",
    #         supported_patterns=[...],
    #     )
    #     raise HTTPException(status_code=422, detail=detail.model_dump())
    #
    # rows = [record.data() for record in session.run(cypher)]
    # return KGResponse(cypher=cypher, rows=rows, count=len(rows))

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Paste your original /kg/query implementation here.",
    )


@app.post("/rag/answer", response_model=RAGResponse)
def rag_answer(
    req: RAGRequest,
    auth=Depends(require_api_key_or_jwt),
    weaviate_client=Depends(get_weaviate),
    generator=Depends(get_generator),
    embedder=Depends(get_embedder),
):
    """Retrieve → assemble → generate → cite → grounding check.

    Returns RAGResponse with citations populated when a grounded answer
    is available, or the SENTINEL with empty citations when retrieval
    or citation extraction fails.
    """

    # PUT YOUR ORIGINAL /rag/answer BODY HERE.
    #
    # The body depends on your retrieval/generation helper function names.
    # I cannot safely invent it because you did not paste those files.
    #
    # Keep your original RAG logic and only add:
    # auth=Depends(require_api_key_or_jwt)
    # in the function signature.

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Paste your original /rag/answer implementation here.",
    )


@app.get("/healthz", response_model=HealthResponse)
def healthz():
    """Liveness probe. Must NOT touch Neo4j or Weaviate."""

    # Adjust this only if your HealthResponse model uses different fields.
    return HealthResponse(status="ok")


@app.get("/readyz")
def readyz(
    session=Depends(get_session),
    weaviate_client=Depends(get_weaviate),
):
    """Readiness probe.

    Returns 200 only if `RETURN 1` against Neo4j AND `client.is_ready()`
    against Weaviate both succeed within 2 seconds. Otherwise 503 with
    structured detail naming which backend failed.
    """

    result = {
        "neo4j": "ok",
        "weaviate": "ok",
    }

    try:
        session.run("RETURN 1").single()
    except Exception:
        result["neo4j"] = "down"

    try:
        if not weaviate_client.is_ready():
            result["weaviate"] = "down"
    except Exception:
        result["weaviate"] = "down"

    if result["neo4j"] != "ok" or result["weaviate"] != "ok":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result,
        )

    return result