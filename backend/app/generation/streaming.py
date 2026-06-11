from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from app.generation.llm_client import stream_answer
from app.observability.fallbacks import get_model_config
from app.observability.langfuse_client import (
    build_generation_input,
    flush_langfuse,
    log_generation,
    log_retrieval,
    start_rag_trace,
)


def _stream_usage() -> dict[str, Any]:
    model_config = get_model_config()
    return {
        "provider": model_config.provider,
        "model": model_config.model,
    }


async def sse_stream(
    question: str,
    context: str,
    sources: list | None = None,
    *,
    metadata: dict[str, Any] | None = None,
) -> AsyncGenerator[str, None]:
    trace = start_rag_trace(question, metadata)
    if trace is not None and sources is not None:
        log_retrieval(trace, sources)

    tokens: list[str] = []
    try:
        async for token in stream_answer(question, context):
            tokens.append(token)
            payload = json.dumps({"token": token})
            yield f"data: {payload}\n\n"

        answer = "".join(tokens)
        usage = _stream_usage() if trace else None
        trace_id = log_generation(
            trace,
            answer,
            usage,
            input=build_generation_input(question, context) if trace else None,
        )

        done_payload: dict[str, Any] = {"done": True}
        if trace_id:
            done_payload["trace_id"] = trace_id
        if sources is not None:
            done_payload["sources"] = [
                {
                    "chunk_id": str(s.chunk_id),
                    "document_id": str(s.document_id),
                    "filename": s.filename,
                    "chunk_index": s.chunk_index,
                    "content": s.content,
                    "score": s.score,
                    "source": s.source,
                }
                for s in sources
            ]
        yield f"data: {json.dumps(done_payload)}\n\n"
    finally:
        flush_langfuse()
