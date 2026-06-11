# RAG-Architecture-TT

Educational Retrieval-Augmented Generation (RAG) proof of concept for the tech talk **Designing RAG Architectures: From Basic Retrieval to Production-Ready AI Systems**.

## Stack

- **FastAPI** — ingestion, retrieval, generation, streaming API
- **Streamlit** — upload UI and chat demo
- **PostgreSQL + pgvector** — vector storage and hybrid BM25 search (384-d local embeddings)
- **pgAdmin** — inspect documents, chunks, embeddings
- **LangFuse (self-hosted)** — LLM tracing, prompt/config sync, provider routing with code fallback
- **Claude Sonnet** — default LLM via Anthropic API (`claude-sonnet-4-6`)
- **Local embeddings** — `all-MiniLM-L6-v2` (sentence-transformers; no embedding API key)
- **OpenAI** — optional; used when LangFuse config sets `provider: openai`
- **Docker Compose** — full local stack

**Note:** Anthropic does not offer an embeddings API. This POC uses local sentence-transformers for vectors.

## Quick start

```bash
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and LangFuse keys after first boot

docker compose up --build

# After LangFuse project is created, sync local prompt config:
chmod +x scripts/sync_langfuse.sh
./scripts/sync_langfuse.sh
```

| Service | URL |
|---------|-----|
| Streamlit UI | http://localhost:8501 |
| FastAPI docs | http://localhost:8000/docs |
| LangFuse | http://localhost:3000 |
| pgAdmin | http://localhost:5050 |
| RAG Postgres | localhost:5430 |

**First boot:** LangFuse may take 2–3 minutes (ClickHouse init). Ensure ~8–16 GB RAM available.

**Fresh DB required** if migrating from OpenAI 1536-d embeddings: reset the RAG volume before re-ingesting documents.

### pgAdmin connection

- Host: `postgres-rag`
- Port: `5432`
- Database: `ragdb`
- Username: `rag`
- Password: `ragpassword`

## Sync LangFuse config from local files

Prompts, models, provider, and temperature are defined in [`config/langfuse/prompts.yaml`](config/langfuse/prompts.yaml):

```bash
./scripts/sync_langfuse.sh              # push to LangFuse
./scripts/sync_langfuse.sh --dry-run    # preview only
./scripts/sync_langfuse.sh --prompt rag-system
```

## Run tests with coverage

```bash
chmod +x scripts/test.sh
./scripts/test.sh
```

Prints a terminal coverage table and writes HTML to `coverage_html/`.

## Demo flow (10 min)

1. Upload a PDF with **fixed_size** chunking → inspect 384-d embeddings in pgAdmin
2. Ask a keyword-heavy question → compare **Naive** vs **Hybrid** RAG
3. Open LangFuse trace → walk ingest / retrieve / generate spans (provider + model)
4. Edit `config/langfuse/prompts.yaml` (`provider: openai`) → `./scripts/sync_langfuse.sh` → compare GPT vs Claude
5. Stop LangFuse → verify YAML-based code fallback still works

## Documentation

- [Architecture](docs/architecture.md)
- [Chunking strategies](docs/chunking-strategies.md)
- [RAG types](docs/rag-types.md)
- [Best practices & trends](docs/best-practices-and-trends.md)
- [LangFuse setup](docs/langfuse-setup.md)
- [Presentation alignment](docs/presentation-alignment.md)

## Environment variables

See [`.env.example`](.env.example) for all settings. Key variables:

- `ANTHROPIC_API_KEY` — required for default Claude Sonnet generation
- `OPENAI_API_KEY` — optional; required when LangFuse/YAML config uses `provider: openai`
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` — from LangFuse project settings
- `EMBEDDING_MODEL` — local model name (default `all-MiniLM-L6-v2`)
- `RAG_MODE` — `hybrid` (default) or `naive`

## Project layout

```
backend/app/           FastAPI RAG pipeline
config/langfuse/       Prompt registry (source of truth)
frontend/              Streamlit UI
scripts/               test.sh, sync_langfuse.sh
db/init.sql            pgvector schema (384-d)
uploads/               Local document storage (gitignored)
docs/                  Tech talk reference documentation
```
