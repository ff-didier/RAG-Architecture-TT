from app.ingestion.chunker import chunk_text, count_tokens
from app.schemas import ChunkingStrategy


def test_empty_text_returns_no_chunks():
    assert chunk_text("   ", ChunkingStrategy.fixed_size) == []


def test_fixed_size_produces_multiple_chunks():
    text = "word " * 2000
    chunks = chunk_text(text, ChunkingStrategy.fixed_size)
    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].token_count > 0


def test_sliding_window_overlap():
    text = "token " * 1500
    chunks = chunk_text(text, ChunkingStrategy.sliding_window)
    assert len(chunks) >= 2


def test_semantic_respects_paragraphs():
    text = "Paragraph one about RAG.\n\nParagraph two about pgvector.\n\nParagraph three about LangFuse."
    chunks = chunk_text(text, ChunkingStrategy.semantic)
    assert len(chunks) >= 1
    assert "Paragraph one" in chunks[0].content
    assert "Paragraph two" in chunks[0].content


def test_count_tokens_positive():
    assert count_tokens("hello world") > 0
