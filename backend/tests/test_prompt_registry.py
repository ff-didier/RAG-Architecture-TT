from pathlib import Path

from app.observability.prompt_registry import (
    get_local_fallback_config,
    langfuse_to_python_template,
    list_sync_prompts,
    load_prompts_config,
)


def test_langfuse_to_python_template():
    template = "Hello {{context}} and {{question}}"
    assert langfuse_to_python_template(template) == "Hello {context} and {question}"


def test_load_prompts_config():
    path = Path(__file__).resolve().parents[2] / "config" / "langfuse" / "prompts.yaml"
    data = load_prompts_config(str(path))
    assert "rag-system" in data["prompts"]


def test_get_local_fallback_config():
    path = Path(__file__).resolve().parents[2] / "config" / "langfuse" / "prompts.yaml"
    config = get_local_fallback_config("rag-system", str(path))
    assert config["provider"] == "anthropic"
    assert config["model"] == "claude-sonnet-4-6"
    assert "{context}" in config["prompt_template"]


def test_list_sync_prompts():
    path = Path(__file__).resolve().parents[2] / "config" / "langfuse" / "prompts.yaml"
    prompts = list_sync_prompts(str(path))
    assert "rag-system" in prompts
