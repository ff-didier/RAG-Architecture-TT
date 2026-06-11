from __future__ import annotations

from uuid import UUID

from app.config import settings
from app.retrieval.vector import ScoredChunk


def reciprocal_rank_fusion(
    ranked_lists: list[list[ScoredChunk]],
    top_k: int | None = None,
    k: int | None = None,
) -> list[ScoredChunk]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion."""
    rrf_k = k or settings.rrf_k
    limit = top_k or settings.hybrid_top_k
    scores: dict[UUID, float] = {}
    best: dict[UUID, ScoredChunk] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            scores[item.chunk_id] = scores.get(item.chunk_id, 0.0) + 1.0 / (rrf_k + rank)
            if item.chunk_id not in best or item.score > best[item.chunk_id].score:
                best[item.chunk_id] = item

    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)[:limit]
    merged: list[ScoredChunk] = []
    for chunk_id in sorted_ids:
        item = best[chunk_id]
        merged.append(
            ScoredChunk(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                filename=item.filename,
                chunk_index=item.chunk_index,
                content=item.content,
                score=scores[chunk_id],
                source="hybrid",
            )
        )
    return merged
