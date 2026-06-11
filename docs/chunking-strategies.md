# Chunking Strategies

This document describes chunking approaches covered in the tech talk and how they are implemented in the POC.

## Why chunking matters

LLMs have finite context windows. RAG splits documents into **chunks** so retrieval returns only the most relevant segments instead of entire files.

| Concept | Meaning |
|---------|---------|
| Document | Full uploaded file |
| Chunk | Sub-segment indexed for retrieval |
| Token | Model input unit (≈ word pieces) |

## Strategies in this POC

### 1. Fixed-size chunking (default)

**Algorithm:** Split text into 512-token windows with 50-token overlap using `tiktoken`.

**When to use:** General-purpose baseline; predictable chunk counts; fast ingest.

**Tradeoffs:**

| Pros | Cons |
|------|------|
| Simple, fast | May split mid-sentence |
| Easy to tune (size/overlap) | Ignores document structure |

**POC default:** Best for live demos — consistent behavior across file types.

### 2. Sliding window

**Algorithm:** 512-token window with 256-token stride (higher overlap than fixed-size).

**When to use:** When answers may span chunk boundaries; recall-focused scenarios.

**Tradeoffs:**

| Pros | Cons |
|------|------|
| Better boundary coverage | More chunks → higher storage/cost |
| Higher recall | Redundant content across chunks |

### 3. Semantic (lightweight)

**Algorithm:** Split on paragraph boundaries (`\n\n`); merge paragraphs until token budget (512) is reached; oversized paragraphs fall back to fixed-size splitting.

**When to use:** Structured prose (policies, reports, documentation with clear sections).

**Tradeoffs:**

| Pros | Cons |
|------|------|
| Respects natural boundaries | No embedding-based boundary detection |
| Better context coherence | Uneven chunk sizes |

**Production upgrade:** Embedding-based semantic chunking (compare consecutive segment embeddings; split when similarity drops).

### 4. Hierarchical chunking (documented, partial POC support)

**Concept:** Parent chunks (sections) and child chunks (paragraphs); retrieve children, optionally expand to parent for broader context.

**POC status:** `parent_chunk_id` column exists; full two-pass hierarchical retrieval is **not implemented** (scope limit). Discuss during talk as a production pattern.

## Configuration

| Setting | Default | Env / code |
|---------|---------|------------|
| Chunk size | 512 tokens | `chunk_size` in config |
| Overlap | 50 tokens | `chunk_overlap` |
| Sliding stride | 256 tokens | `sliding_stride` |

Select strategy at upload time in the Streamlit UI or via `POST /api/v1/documents/upload` form field `strategy`.

## Best practices (2025–2026)

1. **Start with fixed-size** — establish baseline retrieval quality before optimizing chunking.
2. **Match strategy to content** — legal/technical docs benefit from structure-aware splitting.
3. **Log chunk stats** — token counts per chunk help debug context budget issues.
4. **Evaluate, don't guess** — use a labeled Q&A set (RAGAS) to compare strategies on your corpus.
5. **Consider contextual retrieval** — prepend a short document-level summary to each chunk before embedding (Anthropic contextual retrieval; ~49% retrieval failure reduction in their study).

## Talk alignment

| Slide topic | POC feature |
|-------------|-------------|
| Fixed-size chunking | `fixed_size` strategy |
| Semantic chunking | `semantic` strategy |
| Sliding window | `sliding_window` strategy |
| Hierarchical chunking | Schema support + documentation |
| Tradeoffs & best practices | This document + live pgAdmin comparison |
