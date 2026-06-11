from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from langfuse import Langfuse

from app.config import settings
from app.observability.fallbacks import get_model_config

logger = logging.getLogger(__name__)

_langfuse: Langfuse | None = None


def get_langfuse() -> Langfuse | None:
    global _langfuse
    if not settings.langfuse_enabled:
        return None
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    if _langfuse is None:
        _langfuse = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    return _langfuse


def start_rag_trace(question: str, metadata: dict[str, Any] | None = None):
    client = get_langfuse()
    if client is None:
        return None
    return client.trace(name="rag-query", input={"question": question}, metadata=metadata or {})


def flush_langfuse() -> None:
    client = get_langfuse()
    if client:
        client.flush()


@contextmanager
def trace_rag(question: str, metadata: dict[str, Any] | None = None):
    trace = start_rag_trace(question, metadata)
    try:
        yield trace
    finally:
        flush_langfuse()


def trace_ingestion(document_id: str, filename: str, strategy: str, chunk_count: int) -> None:
    client = get_langfuse()
    if client is None:
        return
    client.trace(
        name="document-ingestion",
        input={"filename": filename, "strategy": strategy},
        output={"document_id": document_id, "chunk_count": chunk_count},
    )
    client.flush()


def log_retrieval(trace, chunks: list) -> None:
    if trace is None:
        return
    trace.span(
        name="retrieval",
        output=[
            {
                "chunk_id": str(c.chunk_id),
                "filename": c.filename,
                "score": c.score,
                "source": c.source,
            }
            for c in chunks
        ],
    )


def build_generation_input(question: str, context: str) -> dict[str, Any]:
    model_config = get_model_config()
    system_prompt = model_config.compile_prompt(context=context, question=question)
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "provider": model_config.provider,
        "model": model_config.model,
    }


def log_generation(
    trace,
    answer: str,
    usage: dict | None = None,
    *,
    input: dict[str, Any] | None = None,
) -> str | None:
    if trace is None:
        return None
    model = (usage or {}).get("model")
    trace.generation(
        name="llm-generation",
        input=input,
        output=answer,
        usage=usage,
        model=model,
    )
    client = get_langfuse()
    if client:
        client.flush()
    return trace.id
