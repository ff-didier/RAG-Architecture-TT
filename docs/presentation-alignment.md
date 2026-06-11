# Presentation Alignment

Map each tech talk agenda item to POC features — what to **demo live** vs **reference in docs**.

## Agenda mapping

| # | Talk section | Live demo | Doc reference |
|---|--------------|-----------|---------------|
| 1 | Quick recap — What is RAG? | Chat UI end-to-end | [architecture.md](architecture.md) |
| 2 | Why RAG vs fine-tuning? | Show retrieval sources panel | [rag-types.md](rag-types.md) |
| 3 | High-level architecture | Architecture diagram + Docker services | [architecture.md](architecture.md) |
| 4 | Embeddings vs tokens vs context | LangFuse token usage + chunk token counts | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 5 | Semantic vs keyword search | Naive vs Hybrid toggle on same question | [rag-types.md](rag-types.md) |
| 6 | Documents vs chunks | pgAdmin: 1 document → N chunk rows | [chunking-strategies.md](chunking-strategies.md) |
| 7 | Vector DB vs knowledge base | pgvector schema walkthrough | [architecture.md](architecture.md) |
| 8 | RAG vs fine-tuning | Explain while showing grounded citations | [rag-types.md](rag-types.md) |
| 9 | Anatomy of RAG pipeline | LangFuse trace waterfall | [architecture.md](architecture.md) |
| 10 | Data ingestion | Upload PDF in Streamlit | README demo flow |
| 11 | Chunking and embeddings | Compare 3 strategies on same file | [chunking-strategies.md](chunking-strategies.md) |
| 12 | Retrieval flow | Sources panel with scores | [architecture.md](architecture.md) |
| 13 | Prompt augmentation | LangFuse managed prompt | [langfuse-setup.md](langfuse-setup.md) |
| 14 | Streaming responses | Enable stream checkbox in chat | Streamlit chat page |
| 15 | Fixed-size chunking | Upload with `fixed_size` | [chunking-strategies.md](chunking-strategies.md) |
| 16 | Semantic chunking | Upload with `semantic` | [chunking-strategies.md](chunking-strategies.md) |
| 17 | Sliding window | Upload with `sliding_window` | [chunking-strategies.md](chunking-strategies.md) |
| 18 | Hierarchical chunking | Show `parent_chunk_id` column | [chunking-strategies.md](chunking-strategies.md) |
| 19 | Chunking tradeoffs | pgAdmin side-by-side comparison | [chunking-strategies.md](chunking-strategies.md) |
| 20 | Naive RAG | `rag_mode=naive` | [rag-types.md](rag-types.md) |
| 21 | Hybrid Search RAG | `rag_mode=hybrid` (default) | [rag-types.md](rag-types.md) |
| 22 | Agentic RAG | Slides only | [rag-types.md](rag-types.md) |
| 23 | Graph RAG | Slides only | [rag-types.md](rag-types.md) |
| 24 | Multimodal RAG | Slides only | [rag-types.md](rag-types.md) |
| 25 | Matching architecture to needs | Decision table discussion | [rag-types.md](rag-types.md) |
| 26 | Cost vs performance | Token logs + rerank latency note | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 27 | Scalability / maintainability | Docker Compose → K8s mention | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 28 | LangFuse | Trace UI walkthrough | [langfuse-setup.md](langfuse-setup.md) |
| 29 | Secrets / env vars | Show `.env.example` | [langfuse-setup.md](langfuse-setup.md) |
| 30 | Prompt versioning | Edit prompt in LangFuse, re-query | [langfuse-setup.md](langfuse-setup.md) |
| 31 | Production challenges | Low-score retrieval example | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 32 | Hallucinations | Citation-enforced prompt | [langfuse-setup.md](langfuse-setup.md) |
| 33 | Token limits | Chunk size + top-k discussion | [chunking-strategies.md](chunking-strategies.md) |
| 34 | Latency / cost | LangFuse span timings | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 35 | Security / ACL | Doc-only patterns | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 36 | Reranking | Enable rerank checkbox | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 37 | Query rewriting | Doc-only | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 38 | Context compression | Doc-only | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 39 | Memory systems | Doc-only | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 40 | Tool calling / MCP | Doc-only | [best-practices-and-trends.md](best-practices-and-trends.md) |
| 41 | Key takeaways | Recap hybrid + observability + eval | All docs |

## Suggested 10-minute demo script

| Step | Action | Talk point |
|------|--------|------------|
| 1 | Open pgAdmin, show empty chunks table | Documents vs chunks |
| 2 | Upload PDF (`fixed_size`) | Ingestion pipeline |
| 3 | Show chunk rows with embeddings | Vector DB |
| 4 | Ask keyword-specific question — **Naive** mode | Semantic vs keyword gap |
| 5 | Same question — **Hybrid** mode | Hybrid Search RAG wins |
| 6 | Re-upload with **semantic** chunking | Chunking strategies |
| 7 | Open LangFuse trace | Observability |
| 8 | Enable **rerank**, compare sources | Modern enhancements |
| 9 | Stop LangFuse, query again | Code fallback / resilience |

## URLs cheat sheet (presenter)

| Tool | URL |
|------|-----|
| Streamlit | http://localhost:8501 |
| API Swagger | http://localhost:8000/docs |
| LangFuse | http://localhost:3000 |
| pgAdmin | http://localhost:5050 |

## Pre-demo checklist

- [ ] `.env` has valid `OPENAI_API_KEY`
- [ ] LangFuse keys configured (or plan to demo fallback)
- [ ] Sample PDF prepared for upload
- [ ] Keyword-heavy test question written (e.g. specific product code from PDF)
- [ ] Docker Compose running, all services healthy
- [ ] ~8 GB+ RAM free for LangFuse stack
