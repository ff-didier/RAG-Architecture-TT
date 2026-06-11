#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -d "$ROOT/.venv" ]; then
  source "$ROOT/.venv/bin/activate"
fi

pip install -q -r backend/requirements.txt python-dotenv

python3 "$ROOT/scripts/sync_langfuse.py" "$@"
