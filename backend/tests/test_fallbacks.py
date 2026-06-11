from unittest.mock import MagicMock, patch

from app.observability.fallbacks import ModelConfig, get_fallback_model_config, get_model_config, get_prompt_template


def test_fallback_model_config_uses_yaml():
    config = get_fallback_model_config()
    assert config.provider == "anthropic"
    assert config.model == "claude-sonnet-4-6"
    assert "{context}" in config.prompt_template


def test_get_model_config_without_langfuse():
    config = get_model_config(langfuse_client=None)
    assert config.provider == "anthropic"


@patch("app.observability.fallbacks.settings")
def test_get_model_config_langfuse_failure(mock_settings):
    mock_settings.langfuse_enabled = True
    mock_settings.prompts_config_path = ""
    client = MagicMock()
    client.get_prompt.side_effect = RuntimeError("langfuse down")

    config = get_model_config(langfuse_client=client)
    assert config.provider == "anthropic"


def test_get_prompt_template_fallback():
    template = get_prompt_template("rag-system", langfuse_client=None)
    assert "{context}" in template


@patch("app.observability.fallbacks.settings")
def test_get_model_config_from_langfuse(mock_settings):
    mock_settings.langfuse_enabled = True
    client = MagicMock()
    prompt = MagicMock()
    prompt.prompt = "Managed {{context}} {{question}}"
    prompt.config = {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.1}
    client.get_prompt.return_value = prompt

    config = get_model_config(langfuse_client=client)
    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.temperature == 0.1
