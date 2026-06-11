# RAG Architecture Types

This POC implements **Hybrid Search RAG** as the primary architecture, with **Naive RAG** as a comparison baseline. Other architecture types are documented for the talk but not built in code.

## 1. Naive RAG

**Flow:** Embed query → vector similarity search → append chunks to prompt → generate.

**POC:** Toggle `rag_mode=naive` in the Streamlit UI or API.

**Limitations:** Misses exact keyword matches (product codes, error IDs, version numbers). Pure dense retrieval fails on ~20–40% of enterprise queries that require lexical matching.

## 2. Hybrid Search RAG (POC default)

**Flow:** Run dense (pgvector) and sparse (BM25/tsvector) retrieval in parallel → fuse with **Reciprocal Rank Fusion (RRF)** → optional rerank → generate.

**POC:** Default `rag_mode=hybrid`.

**Why default:** 2025–2026 industry consensus — hybrid retrieval is table stakes for technical documentation and enterprise knowledge bases.

## 3. Agentic RAG

**Concept:** An agent decides whether to retrieve, rewrite the query, call tools, or answer from parametric knowledge.

**POC status:** Documented only. Would add orchestration layer (LangGraph, LlamaIndex agents) and tool routing.

**When to choose:** Multi-step research, dynamic source selection, workflows requiring external APIs.

## 4. Graph RAG

**Concept:** Knowledge graph entities and relationships augment or replace flat chunk retrieval.

**POC status:** Documented only. Would require entity extraction, graph store (Neo4j, etc.), and graph-aware retrieval.

**When to choose:** Highly connected domain knowledge (org charts, dependency graphs, compliance chains).

## 5. Multimodal RAG

**Concept:** Index and retrieve images, tables, and diagrams — not just text.

**POC status:** Documented only. Would need vision embeddings and multimodal parsers.

**When to choose:** PDFs with critical figures, scanned documents, visual inspection manuals.

## Choosing the right architecture

| Business need | Recommended starting point |
|---------------|---------------------------|
| Q&A over text docs | Hybrid Search RAG (this POC) |
| Exact identifiers / codes | Hybrid + rerank |
| Multi-hop reasoning | Agentic RAG |
| Relationship-heavy domains | Graph RAG |
| Image/table-heavy PDFs | Multimodal RAG |

## Cost vs performance

| Architecture | Relative cost | Relative quality | Complexity |
|--------------|---------------|------------------|------------|
| Naive RAG | Low | Baseline | Low |
| Hybrid RAG | Medium | +10–25% MRR typical | Medium |
| Hybrid + rerank | Medium-high | Highest ROI lift | Medium |
| Agentic | High (multi-step LLM) | Variable | High |
| Graph | High (build + maintain graph) | High for structured domains | High |

## POC mapping

```
This POC = Hybrid Search RAG + Naive baseline + optional rerank
```

Use the UI toggle to demonstrate the quality gap between naive and hybrid retrieval during the talk.
