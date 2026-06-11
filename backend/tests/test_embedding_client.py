from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.generation.embedding_client import embed_query, embed_texts


@pytest.mark.asyncio
async def test_embed_texts_empty():
    assert await embed_texts([]) == []


@pytest.mark.asyncio
@patch("app.generation.embedding_client._get_model")
async def test_embed_texts_returns_vectors(mock_get_model):
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    mock_get_model.return_value = mock_model

    vectors = await embed_texts(["hello"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 3


@pytest.mark.asyncio
@patch("app.generation.embedding_client.embed_texts")
async def test_embed_query(mock_embed):
    mock_embed.return_value = [[0.5, 0.6]]
    vector = await embed_query("test")
    assert vector == [0.5, 0.6]
