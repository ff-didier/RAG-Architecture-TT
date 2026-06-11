from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.generation.embedding_client import embed_query
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.keyword import keyword_search
from app.retrieval.reranker import rerank_chunks
from app.retrieval.vector import ScoredChunk, naive_retrieve, vector_search
from app.schemas import RagMode


async def retrieve(
    session: AsyncSession,
    query: str,
    rag_mode: RagMode | None = None,
    rerank_enabled: bool | None = None,
) -> list[ScoredChunk]:
    mode = rag_mode or RagMode(settings.rag_mode)
    use_rerank = settings.rerank_enabled if rerank_enabled is None else rerank_enabled
    query_embedding = await embed_query(query)

    if mode == RagMode.naive:
        results = await naive_retrieve(session, query_embedding)
    else:
        dense = await vector_search(session, query_embedding)
        sparse = await keyword_search(session, query)
        results = reciprocal_rank_fusion([dense, sparse])

    if use_rerank and results:
        results = rerank_chunks(query, results)

    return results
