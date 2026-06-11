# Best Practices and Market Trends (2025–2026)

Synthesis of current RAG engineering guidance aligned with this POC and the tech talk agenda.

## Key market trends

### 1. Hybrid retrieval is the default

Pure vector search is increasingly treated as an anti-pattern for production technical content. The standard stack:

1. Dense retrieval (embeddings / pgvector)
2. Sparse retrieval (BM25 / tsvector)
3. Fusion (RRF or weighted combination)
4. Cross-encoder reranking

**POC alignment:** Hybrid mode with RRF (k=60) and optional `ms-marco-MiniLM-L-6-v2` reranker.

### 2. pgvector as pragmatic starting point

Teams already on PostgreSQL can add the `vector` extension and avoid operating a separate vector DB until ~1–5M chunks or specialized filtering needs arise.

**POC alignment:** Single Postgres instance with HNSW index on embeddings + GIN on tsvector.

### 3. Contextual retrieval at ingest

Anthropic's contextual retrieval prepends a 50–100 token document-level summary to each chunk before embedding. Reported ~49% reduction in failed retrievals; ~67% with reranking.

**POC status:** Documented as enhancement path — not implemented to keep ingest simple.

### 4. Observability before optimization

You cannot fix what you cannot see. Trace every stage: query → retrieval scores → prompt → generation → tokens/latency.

**POC alignment:** Self-hosted LangFuse with ingestion, retrieval, and generation spans.

### 5. Evaluation harnesses (RAGAS)

Automated metrics (faithfulness, answer relevance, context precision) catch regressions when changing chunking, models, or retrieval params.

**POC status:** Documented as production next step — not implemented.

## Modern enhancements (talk section)

| Enhancement | Status in POC | Notes |
|-------------|---------------|-------|
| Reranking | Optional toggle | Cross-encoder on top candidates |
| Query rewriting | Documented | HyDE, multi-query expansion |
| Context compression | Documented | LLM summarization of retrieved chunks |
| Memory systems | Documented | Session / long-term memory layers |
| Tool calling / MCP | Documented | Agentic extension beyond flat RAG |

## Production challenges

### Hallucinations and retrieval quality

- Require citations in system prompt (implemented)
- Show retrieval scores in UI (implemented)
- Add score thresholds in production

### Token and context limitations

- Log token usage via LangFuse
- Budget top-k chunks by relevance (rerank helps)
- "Lost in the middle" — place best chunk first

### Latency and cost

| Stage | Typical cost driver |
|-------|---------------------|
| Embedding ingest | One-time per chunk |
| Retrieval | DB query (cheap at POC scale) |
| Rerank | CPU/GPU cross-encoder |
| Generation | Dominates $ at scale |

Optimize generation (smaller model for simple queries) before over-engineering retrieval.

### Security and access control

POC has no auth. Production patterns:

- Document-level ACLs in metadata + retrieval filters
- Secrets via env / vault (never in code)
- PII scanning at ingest

## Recommended evolution path

1. **Ship:** Hybrid RAG + LangFuse + pgvector (this POC)
2. **Add:** Reranker + eval set (50 labeled Q&A pairs)
3. **Add:** Contextual retrieval at ingest
4. **Add:** Query rewriting for ambiguous questions
5. **Consider:** Agentic layer when workflows need tools

## Reference stack (2026 consensus)

| Layer | Common choices |
|-------|----------------|
| Embeddings | Local MiniLM, Voyage AI (Anthropic-recommended), OpenAI, BGE-M3 |
| LLM | Claude Sonnet (Anthropic), GPT-4o (OpenAI) |
| Vector store | pgvector → Qdrant/Pinecone at scale |
| Reranker | Cohere Rerank 3, BGE reranker, ms-marco-MiniLM |
| Observability | LangFuse, LangSmith, Arize Phoenix |
| Evaluation | RAGAS, custom golden sets |

**Anthropic note:** Claude has no embeddings API. Production Anthropic RAG stacks typically pair Claude with Voyage AI or local/open embeddings. This POC uses local MiniLM for simplicity.

## Embeddings vs tokens vs context (talk recap)

| Term | Definition |
|------|------------|
| Token | Unit the LLM processes; drives cost and limits |
| Embedding | Dense vector representing semantic meaning |
| Context window | Max tokens the LLM can accept per request |
| Chunk | Retrieved text segment added to context |

Retrieval quality is a **data engineering** problem first; model choice is second.
