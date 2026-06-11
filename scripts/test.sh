#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -d "$ROOT/.venv" ]; then
  source "$ROOT/.venv/bin/activate"
fi

pip install -q -r backend/requirements.txt -r backend/requirements-dev.txt
cd backend
pytest --cov=app --cov-report=term-missing --cov-report=html:"$ROOT/coverage_html" --cov-fail-under=80
