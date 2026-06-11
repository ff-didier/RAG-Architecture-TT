#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langfuse import Langfuse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPTS_PATH = ROOT / "config" / "langfuse" / "prompts.yaml"


def load_env() -> None:
    env_file = ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)


def load_prompts(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def sync_prompt(client: Langfuse, name: str, definition: dict, dry_run: bool) -> None:
    prompt_type = definition.get("type", "text")
    template = definition.get("template", "")
    config = definition.get("config", {})
    labels = definition.get("labels", ["production"])

    provider = config.get("provider", "unknown")
    model = config.get("model", "unknown")

    if dry_run:
        print(f"[dry-run] Would sync prompt '{name}' ({prompt_type}) provider={provider} model={model}")
        return

    client.create_prompt(
        name=name,
        type=prompt_type,
        prompt=template,
        config=config,
        labels=labels,
    )
    print(f"Synced prompt '{name}' provider={provider} model={model} labels={labels}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync local LangFuse prompt config to LangFuse server")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without calling LangFuse API")
    parser.add_argument("--prompt", help="Sync only this prompt name")
    parser.add_argument("--config", default=str(DEFAULT_PROMPTS_PATH), help="Path to prompts.yaml")
    args = parser.parse_args()

    load_env()
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 1

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

    if not args.dry_run and (not public_key or not secret_key):
        print("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in .env", file=sys.stderr)
        return 1

    data = load_prompts(config_path)
    prompts = data.get("prompts", {})
    if not prompts:
        print("No prompts found in config", file=sys.stderr)
        return 1

    if args.prompt:
        if args.prompt not in prompts:
            print(f"Prompt '{args.prompt}' not found", file=sys.stderr)
            return 1
        prompts = {args.prompt: prompts[args.prompt]}

    client = None if args.dry_run else Langfuse(public_key=public_key, secret_key=secret_key, host=host)

    for name, definition in prompts.items():
        sync_prompt(client, name, definition, args.dry_run)

    if client is not None:
        client.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
