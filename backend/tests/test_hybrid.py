from uuid import uuid4

from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.vector import ScoredChunk


def _chunk(name: str, score: float, source: str = "vector") -> ScoredChunk:
    cid = uuid4()
    return ScoredChunk(
        chunk_id=cid,
        document_id=uuid4(),
        filename=name,
        chunk_index=0,
        content=f"content for {name}",
        score=score,
        source=source,
    )


def test_rrf_promotes_items_in_both_lists():
    a = _chunk("a.pdf", 0.9)
    b = _chunk("b.pdf", 0.8)
    c = _chunk("c.pdf", 0.7, source="keyword")

    merged = reciprocal_rank_fusion([[a, b], [c, a]], top_k=3, k=60)
    assert merged[0].chunk_id == a.chunk_id
    assert len(merged) == 3


def test_rrf_respects_top_k():
    items = [_chunk(f"{i}.pdf", 0.5) for i in range(5)]
    merged = reciprocal_rank_fusion([items], top_k=2, k=60)
    assert len(merged) == 2


def test_rrf_empty_lists():
    assert reciprocal_rank_fusion([[], []]) == []
