from __future__ import annotations

from app.config import settings
from app.retrieval.vector import ScoredChunk

_cross_encoder = None


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder

        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder


def rerank_chunks(query: str, chunks: list[ScoredChunk], top_k: int | None = None) -> list[ScoredChunk]:
    if not chunks:
        return []

    limit = top_k or settings.rerank_top_k
    encoder = _get_cross_encoder()
    pairs = [[query, chunk.content] for chunk in chunks]
    scores = encoder.predict(pairs)

    ranked = sorted(
        zip(chunks, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )[:limit]

    return [
        ScoredChunk(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            filename=chunk.filename,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=float(score),
            source="rerank",
        )
        for chunk, score in ranked
    ]
