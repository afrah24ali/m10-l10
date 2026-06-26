from fastapi import HTTPException, Request, status


async def get_session(request: Request):
    driver = getattr(request.app.state, "neo4j_driver", None)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j driver is not ready",
        )

    with driver.session() as session:
        yield session


def get_weaviate(request: Request):
    client = getattr(request.app.state, "weaviate_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weaviate client is not ready",
        )
    return client


def get_nlp(request: Request):
    nlp = getattr(request.app.state, "nlp", None)
    if nlp is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="spaCy pipeline is not ready",
        )
    return nlp


def get_generator(request: Request):
    generator = getattr(request.app.state, "generator", None)
    if generator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Generator is not ready",
        )
    return generator


def get_embedder(request: Request):
    embedder = getattr(request.app.state, "embedder", None)
    if embedder is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedder is not ready",
        )
    return embedder