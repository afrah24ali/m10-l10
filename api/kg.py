from __future__ import annotations

from typing import Any

# pyrefly: ignore [missing-import]
from neo4j import Session

from .models import KGResponse


try:
    from .w9b_mapper import UnsupportedQueryError, map_question
except ImportError as exc:
    raise ImportError(
        "Could not import map_question or UnsupportedQueryError from api/w9b_mapper. "
        "Do not modify api/w9b_mapper. Check that the folder exists."
    ) from exc


def get_supported_patterns() -> list[str]:
    """
    Return supported question patterns from the vendored mapper.

    This is used in the structured 422 response when the question is unsupported.
    """
    try:
        from .w9b_mapper import SUPPORTED_PATTERNS

        return list(SUPPORTED_PATTERNS)
    except (ImportError, AttributeError):
        pass

    try:
        from .w9b_mapper import supported_patterns

        return list(supported_patterns())
    except (ImportError, AttributeError):
        pass

    try:
        from .w9b_mapper import get_supported_patterns as mapper_get_supported_patterns

        return list(mapper_get_supported_patterns())
    except (ImportError, AttributeError):
        pass

    return [
        "questions about recipes",
        "questions about ingredients",
        "questions about techniques",
    ]


def wrap_kg_query(question: str) -> tuple[str, dict[str, Any]]:
    """
    Convert a natural-language question into Cypher + parameters.

    The vendored mapper usually returns:
        (cypher, params)

    This wrapper also handles simple string/dict returns just in case.
    """
    result = map_question(question)

    if isinstance(result, tuple) or isinstance(result, list):
        cypher = result[0]
        params = result[1] if len(result) > 1 and result[1] is not None else {}
        return str(cypher), dict(params)

    if isinstance(result, dict):
        cypher = result.get("cypher") or result.get("query")
        params = result.get("params") or result.get("parameters") or {}

        if cypher is None:
            raise ValueError("Mapper returned a dict without 'cypher' or 'query'.")

        return str(cypher), dict(params)

    return str(result), {}


def run_kg_query(question: str, session: Session) -> KGResponse:
    """
    Map the question to Cypher, execute it in Neo4j, and return JSON-safe rows.
    """
    cypher, params = wrap_kg_query(question)

    result = session.run(cypher, **params)
    rows = [record.data() for record in result]

    return KGResponse(
        cypher=cypher,
        rows=rows,
        count=len(rows),
    )