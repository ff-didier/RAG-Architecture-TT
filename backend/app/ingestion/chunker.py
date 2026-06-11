from __future__ import annotations

from dataclasses import dataclass

import tiktoken

from app.config import settings
from app.schemas import ChunkingStrategy

ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    token_count: int
    parent_chunk_id: str | None = None


def count_tokens(text: str) -> int:
    return len(ENCODING.encode(text))


def chunk_text(text: str, strategy: ChunkingStrategy) -> list[TextChunk]:
    if not text.strip():
        return []

    if strategy == ChunkingStrategy.fixed_size:
        return _fixed_size_chunks(text)
    if strategy == ChunkingStrategy.sliding_window:
        return _sliding_window_chunks(text)
    if strategy == ChunkingStrategy.semantic:
        return _semantic_chunks(text)
    raise ValueError(f"Unknown chunking strategy: {strategy}")


def _fixed_size_chunks(text: str) -> list[TextChunk]:
    tokens = ENCODING.encode(text)
    chunks: list[TextChunk] = []
    start = 0
    index = 0
    size = settings.chunk_size
    overlap = settings.chunk_overlap

    while start < len(tokens):
        end = min(start + size, len(tokens))
        content = ENCODING.decode(tokens[start:end])
        chunks.append(TextChunk(content=content, chunk_index=index, token_count=end - start))
        index += 1
        if end >= len(tokens):
            break
        start = max(start + size - overlap, start + 1)

    return chunks


def _sliding_window_chunks(text: str) -> list[TextChunk]:
    tokens = ENCODING.encode(text)
    chunks: list[TextChunk] = []
    window = settings.chunk_size
    stride = settings.sliding_stride
    index = 0

    for start in range(0, len(tokens), stride):
        end = min(start + window, len(tokens))
        content = ENCODING.decode(tokens[start:end])
        chunks.append(TextChunk(content=content, chunk_index=index, token_count=end - start))
        index += 1
        if end >= len(tokens):
            break

    return chunks


def _semantic_chunks(text: str) -> list[TextChunk]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[TextChunk] = []
    buffer: list[str] = []
    buffer_tokens = 0
    index = 0
    max_tokens = settings.chunk_size

    def flush() -> None:
        nonlocal index, buffer, buffer_tokens
        if not buffer:
            return
        content = "\n\n".join(buffer)
        chunks.append(TextChunk(content=content, chunk_index=index, token_count=buffer_tokens))
        index += 1
        buffer = []
        buffer_tokens = 0

    for paragraph in paragraphs:
        para_tokens = count_tokens(paragraph)
        if para_tokens > max_tokens:
            flush()
            sub_chunks = _fixed_size_chunks(paragraph)
            for sub in sub_chunks:
                sub.chunk_index = index
                chunks.append(sub)
                index += 1
            continue

        if buffer_tokens + para_tokens > max_tokens and buffer:
            flush()

        buffer.append(paragraph)
        buffer_tokens += para_tokens

    flush()
    return chunks
