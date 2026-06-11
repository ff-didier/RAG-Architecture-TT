from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.generation.embedding_client import embed_texts
from app.ingestion.chunker import chunk_text
from app.ingestion.parser import parse_document
from app.models import Chunk, Document
from app.observability.langfuse_client import trace_ingestion
from app.schemas import ChunkingStrategy


async def ingest_file(
    session: AsyncSession,
    file_path: Path,
    filename: str,
    mime_type: str,
    strategy: ChunkingStrategy,
) -> tuple[Document, int]:
    text = parse_document(file_path, mime_type)
    text_chunks = chunk_text(text, strategy)

    document = Document(
        filename=filename,
        file_path=str(file_path),
        mime_type=mime_type,
        metadata_={"strategy": strategy.value, "char_count": len(text)},
    )
    session.add(document)
    await session.flush()

    embeddings: list[list[float]] = []
    if text_chunks:
        embeddings = await embed_texts([c.content for c in text_chunks])

    chunk_rows: list[Chunk] = []
    for idx, (text_chunk, embedding) in enumerate(zip(text_chunks, embeddings, strict=False)):
        chunk_rows.append(
            Chunk(
                document_id=document.id,
                content=text_chunk.content,
                chunk_index=text_chunk.chunk_index,
                strategy=strategy.value,
                token_count=text_chunk.token_count,
                parent_chunk_id=uuid.UUID(text_chunk.parent_chunk_id) if text_chunk.parent_chunk_id else None,
                embedding=embedding,
            )
        )

    session.add_all(chunk_rows)
    await session.commit()
    await session.refresh(document)

    trace_ingestion(
        document_id=str(document.id),
        filename=filename,
        strategy=strategy.value,
        chunk_count=len(chunk_rows),
    )

    return document, len(chunk_rows)


async def list_documents(session: AsyncSession) -> list[tuple[Document, int]]:
    stmt = (
        select(Document, func.count(Chunk.id).label("chunk_count"))
        .outerjoin(Chunk, Chunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.uploaded_at.desc())
    )
    result = await session.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]


async def delete_document(session: AsyncSession, document_id: uuid.UUID) -> bool:
    stmt = select(Document).where(Document.id == document_id)
    result = await session.execute(stmt)
    document = result.scalar_one_or_none()
    if not document:
        return False

    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()

    await session.execute(delete(Chunk).where(Chunk.document_id == document_id))
    await session.delete(document)
    await session.commit()
    return True


def save_upload(upload_dir: Path, filename: str, content: bytes) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}_{filename}"
    path = upload_dir / safe_name
    path.write_bytes(content)
    return path
