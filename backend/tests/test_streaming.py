import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.generation.streaming import sse_stream
from app.retrieval.vector import ScoredChunk


@pytest.mark.asyncio
async def test_sse_stream_emits_tokens_and_done():
    events = []

    async def fake_stream(question, context):
        yield "Hello"
        yield " world"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.generation.streaming.stream_answer", fake_stream)
        async for event in sse_stream("q", "ctx"):
            events.append(event)

    assert any("Hello" in e for e in events)
    assert any('"done": true' in e for e in events)


@pytest.mark.asyncio
async def test_sse_stream_includes_sources_on_done():
    chunk = ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="a.pdf",
        chunk_index=0,
        content="text",
        score=0.9,
        source="hybrid",
    )

    async def fake_stream(question, context):
        yield "ok"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.generation.streaming.stream_answer", fake_stream)
        events = [e async for e in sse_stream("q", "ctx", sources=[chunk])]

    assert any("sources" in e for e in events)


@pytest.mark.asyncio
@patch("app.generation.streaming.log_generation")
@patch("app.generation.streaming.log_retrieval")
@patch("app.generation.streaming.start_rag_trace")
async def test_sse_stream_includes_trace_id_on_done(mock_start, mock_retrieval, mock_log_gen):
    trace = MagicMock()
    trace.id = "trace-stream-1"
    mock_start.return_value = trace
    mock_log_gen.return_value = "trace-stream-1"

    async def fake_stream(question, context):
        yield "Answer"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.generation.streaming.stream_answer", fake_stream)
        mp.setattr("app.generation.streaming.flush_langfuse", lambda: None)
        events = [e async for e in sse_stream("What is RAG?", "ctx", metadata={"rag_mode": "hybrid"})]

    mock_start.assert_called_once()
    mock_log_gen.assert_called_once()
    done_events = [e for e in events if '"done": true' in e]
    assert done_events
    payload = json.loads(done_events[-1].removeprefix("data: ").strip())
    assert payload["trace_id"] == "trace-stream-1"
