from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Chunk, Document


@dataclass
class ScoredChunk:
    chunk_id: UUID
    document_id: UUID
    filename: str
    chunk_index: int
    content: str
    score: float
    source: str


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


async def vector_search(session: AsyncSession, query_embedding: list[float], top_k: int | None = None) -> list[ScoredChunk]:
    k = top_k or settings.vector_top_k
    stmt = text(
        """
        SELECT c.id, c.document_id, d.filename, c.chunk_index, c.content,
               1 - (c.embedding <=> CAST(:embedding AS vector)) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
        """
    )
    result = await session.execute(stmt, {"embedding": _vector_literal(query_embedding), "limit": k})
    rows = result.fetchall()
    return [
        ScoredChunk(
            chunk_id=row[0],
            document_id=row[1],
            filename=row[2],
            chunk_index=row[3],
            content=row[4],
            score=float(row[5]),
            source="vector",
        )
        for row in rows
    ]


async def naive_retrieve(session: AsyncSession, query_embedding: list[float]) -> list[ScoredChunk]:
    return await vector_search(session, query_embedding, top_k=settings.naive_top_k)
