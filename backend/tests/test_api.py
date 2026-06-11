from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.retrieval.vector import ScoredChunk


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_type(client):
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    data = {"strategy": "fixed_size"}
    response = await client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 400


@pytest.mark.asyncio
@patch("app.main.retrieve", new_callable=AsyncMock)
@patch("app.main.generate_answer", new_callable=AsyncMock)
async def test_chat_returns_answer(mock_generate, mock_retrieve, client):
    chunk = ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="demo.pdf",
        chunk_index=0,
        content="RAG context",
        score=0.88,
        source="hybrid",
    )
    mock_retrieve.return_value = [chunk]
    mock_generate.return_value = ("Grounded answer", {"total_tokens": 10})

    response = await client.post(
        "/api/v1/chat",
        json={"question": "What is RAG?", "rag_mode": "hybrid", "rerank_enabled": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Grounded answer"
    assert len(body["sources"]) == 1


@pytest.mark.asyncio
@patch("app.main.retrieve", new_callable=AsyncMock)
@patch("app.main.log_generation")
@patch("app.main.log_retrieval")
@patch("app.main.trace_rag")
async def test_chat_returns_trace_id(mock_trace_rag, mock_log_retrieval, mock_log_gen, mock_retrieve, client):
    chunk = ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="demo.pdf",
        chunk_index=0,
        content="RAG context",
        score=0.88,
        source="hybrid",
    )
    mock_retrieve.return_value = [chunk]
    mock_trace = MagicMock()
    mock_trace_rag.return_value.__enter__.return_value = mock_trace
    mock_trace_rag.return_value.__exit__.return_value = None
    mock_log_gen.return_value = "trace-abc"

    with patch("app.main.generate_answer", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = ("Grounded answer", {"total_tokens": 10})
        response = await client.post(
            "/api/v1/chat",
            json={"question": "What is RAG?", "rag_mode": "hybrid", "rerank_enabled": False},
        )

    assert response.status_code == 200
    assert response.json()["trace_id"] == "trace-abc"
    mock_log_retrieval.assert_called_once()
    mock_log_gen.assert_called_once()


@pytest.mark.asyncio
@patch("app.main.retrieve", new_callable=AsyncMock)
async def test_chat_stream_returns_sse_with_trace_id(mock_retrieve, client):
    chunk = ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="demo.pdf",
        chunk_index=0,
        content="RAG context",
        score=0.88,
        source="hybrid",
    )
    mock_retrieve.return_value = [chunk]

    async def fake_stream(question, context):
        yield "Hi"

    with (
        patch("app.generation.streaming.stream_answer", fake_stream),
        patch("app.generation.streaming.start_rag_trace") as mock_start,
        patch("app.generation.streaming.log_generation", return_value="trace-stream"),
        patch("app.generation.streaming.flush_langfuse"),
    ):
        mock_start.return_value = MagicMock()
        async with client.stream(
            "POST",
            "/api/v1/chat/stream",
            json={"question": "What is RAG?", "rag_mode": "hybrid", "rerank_enabled": False},
        ) as response:
            assert response.status_code == 200
            body = ""
            async for chunk in response.aiter_text():
                body += chunk

    assert '"trace_id": "trace-stream"' in body
    assert '"done": true' in body


@pytest.mark.asyncio
@patch("app.main.list_documents", new_callable=AsyncMock)
async def test_list_documents(mock_list, client):
    mock_list.return_value = []
    response = await client.get("/api/v1/documents")
    assert response.status_code == 200
    assert response.json() == []
