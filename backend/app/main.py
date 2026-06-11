from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.generation.llm_client import build_context, generate_answer
from app.generation.streaming import sse_stream
from app.ingestion.parser import UnsupportedFileTypeError
from app.ingestion.pipeline import delete_document, ingest_file, list_documents, save_upload
from app.observability.langfuse_client import build_generation_input, log_generation, log_retrieval, trace_rag
from app.retrieval.rag import retrieve
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChunkingStrategy,
    DocumentResponse,
    RagMode,
    RetrievedChunk,
    UploadResponse,
)

app = FastAPI(title="RAG Tech Talk POC", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    strategy: ChunkingStrategy = Form(ChunkingStrategy.fixed_size),
    session: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    content = await file.read()
    upload_dir = Path(settings.upload_dir)
    saved_path = save_upload(upload_dir, file.filename, content)

    try:
        document, chunk_count = await ingest_file(
            session,
            saved_path,
            file.filename,
            file.content_type or "application/octet-stream",
            strategy,
        )
    except UnsupportedFileTypeError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return UploadResponse(
        document=DocumentResponse(
            id=document.id,
            filename=document.filename,
            mime_type=document.mime_type,
            uploaded_at=document.uploaded_at,
            chunk_count=chunk_count,
        ),
        chunks_created=chunk_count,
        strategy=strategy,
    )


@app.get("/api/v1/documents", response_model=list[DocumentResponse])
async def get_documents(session: AsyncSession = Depends(get_db)):
    rows = await list_documents(session)
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            mime_type=doc.mime_type,
            uploaded_at=doc.uploaded_at,
            chunk_count=count,
        )
        for doc, count in rows
    ]


@app.delete("/api/v1/documents/{document_id}")
async def remove_document(document_id: UUID, session: AsyncSession = Depends(get_db)):
    deleted = await delete_document(session, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session: AsyncSession = Depends(get_db)):
    rag_mode = request.rag_mode or RagMode(settings.rag_mode)
    rerank_enabled = settings.rerank_enabled if request.rerank_enabled is None else request.rerank_enabled

    with trace_rag(request.question, metadata={"rag_mode": rag_mode.value}) as trace:
        chunks = await retrieve(session, request.question, rag_mode=rag_mode, rerank_enabled=rerank_enabled)
        log_retrieval(trace, chunks)
        context = build_context(chunks)
        answer, usage = await generate_answer(request.question, context)
        trace_id = log_generation(
            trace,
            answer,
            usage,
            input=build_generation_input(request.question, context),
        )

    sources = [
        RetrievedChunk(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            chunk_index=c.chunk_index,
            content=c.content,
            score=c.score,
            source=c.source,
        )
        for c in chunks
    ]

    return ChatResponse(
        answer=answer,
        sources=sources,
        trace_id=trace_id,
        rag_mode=rag_mode.value,
        rerank_enabled=rerank_enabled,
    )


@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest, session: AsyncSession = Depends(get_db)):
    rag_mode = request.rag_mode or RagMode(settings.rag_mode)
    rerank_enabled = settings.rerank_enabled if request.rerank_enabled is None else request.rerank_enabled

    chunks = await retrieve(session, request.question, rag_mode=rag_mode, rerank_enabled=rerank_enabled)
    context = build_context(chunks)

    return StreamingResponse(
        sse_stream(
            request.question,
            context,
            sources=chunks,
            metadata={"rag_mode": rag_mode.value},
        ),
        media_type="text/event-stream",
    )
