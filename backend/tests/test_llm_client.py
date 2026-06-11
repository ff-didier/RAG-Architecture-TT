from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.generation.llm_client import build_context, generate_answer, stream_answer
from app.observability.fallbacks import ModelConfig
from app.retrieval.vector import ScoredChunk


def test_build_context_formats_sources():
    chunk = ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="doc.pdf",
        chunk_index=1,
        content="RAG content",
        score=0.75,
        source="hybrid",
    )
    context = build_context([chunk])
    assert "doc.pdf" in context
    assert "RAG content" in context


@pytest.mark.asyncio
@patch("app.generation.llm_client.get_model_config")
@patch("app.generation.llm_client._generate_anthropic", new_callable=AsyncMock)
async def test_generate_answer_routes_anthropic(mock_generate, mock_config):
    mock_config.return_value = ModelConfig(
        provider="anthropic",
        model="claude-sonnet-4-6",
        temperature=0.2,
        prompt_template="{context}{question}",
    )
    mock_generate.return_value = ("Answer", {"total_tokens": 3, "provider": "anthropic"})
    answer, usage = await generate_answer("q", "ctx")
    assert answer == "Answer"
    mock_generate.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.generation.llm_client.get_model_config")
@patch("app.generation.llm_client._generate_openai", new_callable=AsyncMock)
async def test_generate_answer_routes_openai(mock_generate, mock_config):
    mock_config.return_value = ModelConfig(
        provider="openai",
        model="gpt-4o",
        temperature=0.2,
        prompt_template="{context}{question}",
    )
    mock_generate.return_value = ("Answer", {"total_tokens": 3, "provider": "openai"})
    answer, _ = await generate_answer("q", "ctx")
    assert answer == "Answer"
    mock_generate.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.generation.llm_client.get_anthropic_client")
async def test_generate_anthropic(mock_get_client):
    mock_client = AsyncMock()
    mock_get_client.return_value = mock_client
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Claude answer"
    mock_response.content = [mock_block]
    mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    model_config = ModelConfig(
        provider="anthropic",
        model="claude-sonnet-4-6",
        temperature=0.2,
        prompt_template="Ctx {context} Q {question}",
    )
    from app.generation.llm_client import _generate_anthropic

    answer, usage = await _generate_anthropic(model_config, "question", "context")
    assert answer == "Claude answer"
    assert usage["provider"] == "anthropic"


@pytest.mark.asyncio
@patch("app.generation.llm_client.get_openai_client")
async def test_generate_openai(mock_get_client):
    mock_client = AsyncMock()
    mock_get_client.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="GPT answer"))]
    mock_response.usage = MagicMock(prompt_tokens=8, completion_tokens=4, total_tokens=12)
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    model_config = ModelConfig(
        provider="openai",
        model="gpt-4o",
        temperature=0.2,
        prompt_template="Ctx {context} Q {question}",
    )
    from app.generation.llm_client import _generate_openai

    answer, usage = await _generate_openai(model_config, "question", "context")
    assert answer == "GPT answer"
    assert usage["provider"] == "openai"


@pytest.mark.asyncio
@patch("app.generation.llm_client.get_model_config")
@patch("app.generation.llm_client._stream_anthropic")
async def test_stream_answer_routes_anthropic(mock_stream, mock_config):
    mock_config.return_value = ModelConfig(
        provider="anthropic",
        model="claude-sonnet-4-6",
        temperature=0.2,
        prompt_template="{context}{question}",
    )

    async def fake_stream(*args, **kwargs):
        yield "Hi"

    mock_stream.side_effect = fake_stream
    tokens = [token async for token in stream_answer("q", "ctx")]
    assert tokens == ["Hi"]
