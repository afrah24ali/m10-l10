"""RAG composer — retrieve → assemble → generate → cite → grounding check.

Per the Evaluation Methodology Rule, the grounding criterion is:
`len(citations) > 0` is required when `answer` is not the empty-
retrieval sentinel. Every cited `chunk_id` must correspond to a
chunk in the top-`k` retrieved from Weaviate.

The generator call uses `do_sample=False` so retrieval and metric
reproducibility hold across runs.
"""
import re
from typing import Any, Tuple

from .models import Citation, RAGResponse, SENTINEL_ANSWER

PROMPT_TEMPLATE = """\
You are answering a recipe question. Use ONLY the numbered sources below.
Cite each claim with the source number in square brackets, e.g. [1].
If the sources do not contain the answer, say: I cannot answer this from the available sources.

Sources:
{sources}

Question: {question}
Answer:"""

SENTINEL = "I cannot answer this from the available sources"
CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def assemble_prompt(question: str, chunks: list[dict]) -> Tuple[str, dict[int, dict]]:
    """Number the retrieved chunks 1..k and substitute into the prompt template.

    Returns (prompt_str, {citation_index: chunk_dict}).
    """
    sources = []
    numbered = {}
    for i, chunk in enumerate(chunks, 1):
        numbered[i] = chunk
        sources.append(f"[{i}] {chunk.get('text', '')}")
    
    sources_str = "\n".join(sources)
    prompt_str = PROMPT_TEMPLATE.format(sources=sources_str, question=question)
    return prompt_str, numbered


def extract_citations(answer: str, numbered: dict[int, dict]) -> list[dict]:
    """Pull [N]-style markers from `answer` and resolve to retrieved chunks.

    Each return value is shaped {"chunk_id": int, "score": float}. Only
    indices that are present in `numbered` are returned; duplicates are
    de-duplicated.
    """
    seen_chunk_ids = set()
    citations = []
    
    for match in CITATION_PATTERN.finditer(answer):
        index = int(match.group(1))
        if index in numbered:
            chunk = numbered[index]
            chunk_id = chunk["chunk_id"]
            if chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                distance = chunk.get("_additional", {}).get("distance", 0.0)
                score = max(0.0, min(1.0, 1.0 - distance))
                citations.append({
                    "chunk_id": chunk_id,
                    "score": score
                })
    return citations


def compose_rag(question: str, embedder, weaviate_client, generator, k: int = 4) -> dict:
    """Run the four-stage RAG pipeline.

    Returns a dict {"answer": str, "citations": list[dict], "confidence": float}.

    Grounding contract:
    - If Weaviate returns zero chunks → return SENTINEL with citations=[]
      and confidence=0.0.
    - If the generator returns text with no resolvable citation
      markers → also return SENTINEL with citations=[] and
      confidence=0.0. (This is the "refuse rather than hallucinate"
      rule the autograder enforces.)
    """
    # 1. Encode `question` with `embedder`
    vector = embedder.encode(question).tolist()

    # 2. Query Weaviate
    res = weaviate_client.query.get("Chunk", ["text", "chunk_id"])\
        .with_near_vector({"vector": vector})\
        .with_additional(["distance"])\
        .with_limit(k)\
        .do()

    chunks = []
    try:
        chunks = res["data"]["Get"]["Chunk"] or []
    except (KeyError, TypeError):
        pass

    if not chunks:
        return {
            "answer": SENTINEL_ANSWER,
            "citations": [],
            "confidence": 0.0
        }

    # 3. Assemble prompt
    prompt, numbered = assemble_prompt(question, chunks)

    # 4. Generate answer
    gen_res = generator(prompt, max_new_tokens=256, do_sample=False)
    answer_text = gen_res[0]["generated_text"].strip()

    # 5. Extract citations
    citations = extract_citations(answer_text, numbered)

    # 6. Grounding refusal
    if not citations or SENTINEL_ANSWER.lower() in answer_text.lower():
        return {
            "answer": SENTINEL_ANSWER,
            "citations": [],
            "confidence": 0.0
        }

    # 7. Confidence score
    scores = [c["score"] for c in citations]
    confidence = sum(scores) / len(scores) if scores else 0.0
    confidence = max(0.0, min(1.0, confidence))

    # 8. Return dict
    return {
        "answer": answer_text,
        "citations": citations,
        "confidence": confidence
    }


def answer_question(
    question: str,
    k: int,
    weaviate_client: Any,
    generator: Any,
    embedder: Any,
) -> RAGResponse:
    res = compose_rag(question, embedder, weaviate_client, generator, k)
    return RAGResponse(**res)

