from unittest.mock import MagicMock, patch

from app.observability.langfuse_client import (
    build_generation_input,
    get_langfuse,
    log_generation,
    log_retrieval,
    trace_ingestion,
    trace_rag,
)
from app.retrieval.vector import ScoredChunk
from uuid import uuid4


@patch("app.observability.langfuse_client.settings")
def test_get_langfuse_disabled(mock_settings):
    mock_settings.langfuse_enabled = False
    assert get_langfuse() is None


@patch("app.observability.langfuse_client.settings")
def test_trace_ingestion_no_client(mock_settings):
    mock_settings.langfuse_enabled = False
    trace_ingestion("id", "file.pdf", "fixed_size", 3)


def test_trace_rag_without_client():
    with trace_rag("question") as trace:
        assert trace is None


def test_log_retrieval_and_generation_no_trace():
    log_retrieval(None, [])
    assert log_generation(None, "answer") is None


@patch("app.observability.langfuse_client.get_langfuse")
def test_trace_ingestion_with_client(mock_get):
    client = MagicMock()
    mock_get.return_value = client
    trace_ingestion("doc-id", "file.pdf", "semantic", 2)
    client.trace.assert_called_once()
    client.flush.assert_called_once()


@patch("app.observability.langfuse_client.get_model_config")
@patch("app.observability.langfuse_client.get_langfuse")
def test_log_generation_with_trace(mock_get, mock_model_config):
    client = MagicMock()
    mock_get.return_value = client
    trace = MagicMock()
    trace.id = "trace-123"

    mock_config = MagicMock()
    mock_config.provider = "anthropic"
    mock_config.model = "claude-sonnet-4-6"
    mock_config.compile_prompt.return_value = "System with context"
    mock_model_config.return_value = mock_config

    prompt_input = build_generation_input("What is RAG?", "chunk text")
    trace_id = log_generation(trace, "answer", {"total_tokens": 5, "model": "claude-sonnet-4-6"}, input=prompt_input)

    assert trace_id == "trace-123"
    trace.generation.assert_called_once()
    call_kwargs = trace.generation.call_args.kwargs
    assert call_kwargs["input"]["messages"][0]["content"] == "System with context"
    assert call_kwargs["input"]["messages"][1]["content"] == "What is RAG?"
    assert call_kwargs["output"] == "answer"


def test_log_retrieval_with_trace():
    trace = MagicMock()
    chunk = ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="f.pdf",
        chunk_index=0,
        content="c",
        score=0.5,
        source="vector",
    )
    log_retrieval(trace, [chunk])
    trace.span.assert_called_once()
