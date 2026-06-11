# LangFuse Setup

This POC uses **self-hosted LangFuse v3** via Docker Compose alongside the RAG stack.

## Services

LangFuse requires six containers:

- `langfuse-web` — UI and API (port 3000)
- `langfuse-worker` — background jobs
- `langfuse-postgres` — relational metadata
- `clickhouse` — analytics storage
- `redis` — queues
- `minio` — S3-compatible blob storage (port 9090)

First startup may take **2–3 minutes**. ClickHouse initialization is the slowest step.

## Initial setup

1. Start the stack:

```bash
docker compose up --build
```

2. Open http://localhost:3000 and create an account.

3. Create a project (e.g. `rag-tech-talk`).

4. Copy **Public Key** and **Secret Key** from project settings.

5. Add to `.env`:

```env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://langfuse-web:3000
```

6. Sync local prompt config to LangFuse:

```bash
./scripts/sync_langfuse.sh
```

7. Restart the API container if it was already running:

```bash
docker compose restart api
```

## Config as code (recommended workflow)

Managed prompts live in [`config/langfuse/prompts.yaml`](../config/langfuse/prompts.yaml). This file is the **source of truth** for:

- Prompt template text
- LLM `provider` (`anthropic` | `openai`)
- `model` and `temperature`
- `production` label promotion

**Workflow:**

1. Edit `config/langfuse/prompts.yaml`
2. Run `./scripts/sync_langfuse.sh`
3. Verify in LangFuse UI → Prompts

Default `rag-system` config:

```json
{
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "temperature": 0.2
}
```

Switch to OpenAI for a live demo:

```yaml
config:
  provider: openai
  model: gpt-4o
  temperature: 0.2
```

Then re-run `./scripts/sync_langfuse.sh`.

**Drift warning:** edits made only in the LangFuse UI will be overwritten on the next sync. Update YAML first, then sync.

## Runtime behavior

At chat time the API:

1. Fetches `rag-system` from LangFuse (production label)
2. Reads `provider`, `model`, `temperature`, and template
3. Routes to Anthropic Messages API or OpenAI Chat API
4. Falls back to the same YAML defaults if LangFuse is unavailable

Code fallback is loaded from the same YAML via `prompt_registry.py` — no drift between sync and fallback when YAML is kept current.

## Demo: code fallback

1. Send a chat request with LangFuse running — trace appears in UI.
2. Stop LangFuse: `docker compose stop langfuse-web langfuse-worker`
3. Send another chat request — answer still works using YAML/code fallback.
4. Restart LangFuse when done.

## What gets traced

| Event | Trace name | Data |
|-------|------------|------|
| Document upload | `document-ingestion` | filename, strategy, chunk count |
| Chat query | `rag-query` | question, rag_mode |
| Retrieval | span `retrieval` | chunk IDs, scores, sources |
| Generation | generation `llm-generation` | full prompt (`messages` with system + user), answer, provider, model, token usage |

Trace IDs are returned in `/api/v1/chat` responses and in the final SSE `done` event from `/api/v1/chat/stream`. Streamlit shows a LangFuse link for both streaming and non-streaming chat.

## Secrets checklist

| Variable | Purpose |
|----------|---------|
| `NEXTAUTH_SECRET` | LangFuse session signing |
| `SALT` | LangFuse hashing |
| `ENCRYPTION_KEY` | LangFuse encryption (32-byte hex) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | SDK authentication |
| `ANTHROPIC_API_KEY` | Claude generation (default provider) |
| `OPENAI_API_KEY` | Optional GPT generation when `provider: openai` |

Generate secrets for POC:

```bash
openssl rand -base64 32   # NEXTAUTH_SECRET
openssl rand -base64 16   # SALT
openssl rand -hex 32      # ENCRYPTION_KEY
```

**Never commit `.env` to git.**

## Troubleshooting

| Issue | Fix |
|-------|-----|
| LangFuse UI not loading | Wait for ClickHouse health; check `docker compose logs langfuse-web` |
| No traces in UI | Verify API keys in `.env`; restart `api` service |
| Sync script fails | Ensure LangFuse is up and keys are set; try `--dry-run` first |
| High memory usage | LangFuse v3 needs ~8 GB RAM minimum for local demo |
| Port 3000 in use | Change `langfuse-web` port mapping in `docker-compose.yml` |

## Talk alignment

Covers agenda items:

- LangFuse introduction
- Secrets and env variables
- Prompt versioning and config sync
- Provider/model routing without redeploy
- Real-world observability use cases
- Production lesson: graceful degradation via code fallback
