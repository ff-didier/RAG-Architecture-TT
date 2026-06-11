from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.retrieval.vector import ScoredChunk


async def keyword_search(session: AsyncSession, query: str, top_k: int | None = None) -> list[ScoredChunk]:
    k = top_k or settings.keyword_top_k
    stmt = text(
        """
        SELECT c.id, c.document_id, d.filename, c.chunk_index, c.content,
               ts_rank(c.search_vector, plainto_tsquery('english', :query)) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.search_vector @@ plainto_tsquery('english', :query)
        ORDER BY score DESC
        LIMIT :limit
        """
    )
    result = await session.execute(stmt, {"query": query, "limit": k})
    rows = result.fetchall()
    return [
        ScoredChunk(
            chunk_id=row[0],
            document_id=row[1],
            filename=row[2],
            chunk_index=row[3],
            content=row[4],
            score=float(row[5]),
            source="keyword",
        )
        for row in rows
    ]
