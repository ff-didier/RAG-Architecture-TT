from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

LANGFUSE_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")
PYTHON_VAR_PATTERN = re.compile(r"\{(\w+)\}")


def _default_prompts_path() -> Path:
    env_path = os.getenv("PROMPTS_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    project_root = Path(__file__).resolve().parents[3]
    docker_path = Path("/app/config/langfuse/prompts.yaml")
    if docker_path.exists():
        return docker_path
    return project_root / "config" / "langfuse" / "prompts.yaml"


def langfuse_to_python_template(template: str) -> str:
    return LANGFUSE_VAR_PATTERN.sub(r"{\1}", template)


def python_to_langfuse_template(template: str) -> str:
    return PYTHON_VAR_PATTERN.sub(r"{{\1}}", template)


@lru_cache(maxsize=1)
def load_prompts_config(path: str | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else _default_prompts_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Prompts config not found: {config_path}")
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def get_prompt_definition(name: str = "rag-system", path: str | None = None) -> dict[str, Any]:
    data = load_prompts_config(path)
    prompts = data.get("prompts", {})
    if name not in prompts:
        raise KeyError(f"Prompt '{name}' not found in prompts config")
    return prompts[name]


def get_local_fallback_config(name: str = "rag-system", path: str | None = None) -> dict[str, Any]:
    definition = get_prompt_definition(name, path)
    config = definition.get("config", {})
    template = definition.get("template", "")
    return {
        "provider": config.get("provider", "anthropic"),
        "model": config.get("model", "claude-sonnet-4-6"),
        "temperature": float(config.get("temperature", 0.2)),
        "prompt_template": langfuse_to_python_template(template),
    }


def list_sync_prompts(path: str | None = None) -> dict[str, dict[str, Any]]:
    data = load_prompts_config(path)
    return data.get("prompts", {})
