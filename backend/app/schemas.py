from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkingStrategy(str, Enum):
    fixed_size = "fixed_size"
    sliding_window = "sliding_window"
    semantic = "semantic"


class RagMode(str, Enum):
    naive = "naive"
    hybrid = "hybrid"


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    mime_type: str
    uploaded_at: datetime
    chunk_count: int = 0

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    document: DocumentResponse
    chunks_created: int
    strategy: ChunkingStrategy


class RetrievedChunk(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    chunk_index: int
    content: str
    score: float
    source: str = Field(description="vector | keyword | hybrid | rerank")


class ChatRequest(BaseModel):
    question: str
    rag_mode: Optional[RagMode] = None
    rerank_enabled: Optional[bool] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[RetrievedChunk]
    trace_id: Optional[str] = None
    rag_mode: str
    rerank_enabled: bool
