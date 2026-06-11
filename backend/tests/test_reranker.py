from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.retrieval.reranker import rerank_chunks
from app.retrieval.vector import ScoredChunk


def _chunk(content: str) -> ScoredChunk:
    return ScoredChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="doc.pdf",
        chunk_index=0,
        content=content,
        score=0.5,
        source="hybrid",
    )


@patch("app.retrieval.reranker._get_cross_encoder")
def test_rerank_reorders_by_score(mock_encoder):
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.2, 0.9]
    mock_encoder.return_value = mock_model

    chunks = [_chunk("low relevance"), _chunk("high relevance keyword match")]
    ranked = rerank_chunks("keyword match", chunks, top_k=2)

    assert ranked[0].content == "high relevance keyword match"
    assert ranked[0].source == "rerank"


def test_rerank_empty():
    assert rerank_chunks("query", []) == []
