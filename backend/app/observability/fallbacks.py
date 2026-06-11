from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.observability.prompt_registry import get_local_fallback_config, langfuse_to_python_template


@dataclass
class ModelConfig:
    provider: str
    model: str
    temperature: float
    prompt_template: str

    def compile_prompt(self, **kwargs: str) -> str:
        return self.prompt_template.format(**kwargs)


def _config_from_registry(name: str = "rag-system") -> ModelConfig:
    path = settings.prompts_config_path or None
    try:
        data = get_local_fallback_config(name, path)
    except (FileNotFoundError, KeyError):
        data = {
            "provider": settings.llm_provider,
            "model": settings.anthropic_model if settings.llm_provider == "anthropic" else settings.openai_model,
            "temperature": 0.2,
            "prompt_template": "Context:\n{context}\n\nQuestion:\n{question}",
        }
    return ModelConfig(
        provider=data["provider"],
        model=data["model"],
        temperature=data["temperature"],
        prompt_template=data["prompt_template"],
    )


def get_fallback_model_config() -> ModelConfig:
    return _config_from_registry("rag-system")


def get_prompt_template(name: str = "rag-system", langfuse_client=None) -> str:
    if settings.langfuse_enabled and langfuse_client is not None:
        try:
            prompt = langfuse_client.get_prompt(name)
            return langfuse_to_python_template(prompt.prompt)
        except Exception:
            pass
    return get_fallback_model_config().prompt_template


def get_model_config(langfuse_client=None) -> ModelConfig:
    fallback = get_fallback_model_config()
    if langfuse_client is None:
        from app.observability.langfuse_client import get_langfuse

        langfuse_client = get_langfuse()
    if not settings.langfuse_enabled or langfuse_client is None:
        return fallback

    try:
        prompt = langfuse_client.get_prompt("rag-system")
        config = prompt.config or {}
        template = prompt.prompt or ""
        return ModelConfig(
            provider=config.get("provider", fallback.provider),
            model=config.get("model", fallback.model),
            temperature=float(config.get("temperature", fallback.temperature)),
            prompt_template=langfuse_to_python_template(template or fallback.prompt_template),
        )
    except Exception:
        return fallback
