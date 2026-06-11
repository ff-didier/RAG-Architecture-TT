from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.retrieval.rag import retrieve
from app.retrieval.vector import ScoredChunk
from app.schemas import RagMode


@pytest.mark.asyncio
@patch("app.retrieval.rag.embed_query", new_callable=AsyncMock)
@patch("app.retrieval.rag.naive_retrieve", new_callable=AsyncMock)
async def test_retrieve_naive_mode(mock_naive, mock_embed):
    mock_embed.return_value = [0.1, 0.2]
    chunk = ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="a.pdf",
        chunk_index=0,
        content="text",
        score=0.8,
        source="vector",
    )
    mock_naive.return_value = [chunk]
    session = AsyncMock()

    results = await retrieve(session, "query", rag_mode=RagMode.naive, rerank_enabled=False)
    assert len(results) == 1
    mock_naive.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.retrieval.rag.rerank_chunks")
@patch("app.retrieval.rag.reciprocal_rank_fusion")
@patch("app.retrieval.rag.keyword_search", new_callable=AsyncMock)
@patch("app.retrieval.rag.vector_search", new_callable=AsyncMock)
@patch("app.retrieval.rag.embed_query", new_callable=AsyncMock)
async def test_retrieve_hybrid_with_rerank(
    mock_embed, mock_vector, mock_keyword, mock_rrf, mock_rerank
):
    mock_embed.return_value = [0.1]
    dense = [MagicMockChunk()]
    sparse = [MagicMockChunk()]
    mock_vector.return_value = dense
    mock_keyword.return_value = sparse
    fused = [MagicMockChunk()]
    mock_rrf.return_value = fused
    mock_rerank.return_value = fused

    session = AsyncMock()
    results = await retrieve(session, "query", rag_mode=RagMode.hybrid, rerank_enabled=True)
    assert results == fused
    mock_rerank.assert_called_once()


def MagicMockChunk():
    return ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="a.pdf",
        chunk_index=0,
        content="text",
        score=0.5,
        source="hybrid",
    )
