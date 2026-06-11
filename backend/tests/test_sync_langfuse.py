from pathlib import Path
from unittest.mock import MagicMock, patch

import sync_langfuse


def test_load_prompts():
    config_path = Path(__file__).resolve().parents[2] / "config" / "langfuse" / "prompts.yaml"
    data = sync_langfuse.load_prompts(config_path)
    assert "rag-system" in data["prompts"]


def test_sync_prompt_dry_run(capsys):
    definition = {
        "type": "text",
        "template": "Hello {{context}}",
        "config": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        "labels": ["production"],
    }
    sync_langfuse.sync_prompt(None, "rag-system", definition, dry_run=True)
    captured = capsys.readouterr()
    assert "dry-run" in captured.out
    assert "anthropic" in captured.out


@patch("sync_langfuse.Langfuse")
def test_sync_prompt_calls_api(mock_langfuse_cls):
    mock_client = MagicMock()
    mock_langfuse_cls.return_value = mock_client
    definition = {
        "type": "text",
        "template": "Hello {{context}}",
        "config": {"provider": "anthropic", "model": "claude-sonnet-4-6", "temperature": 0.2},
        "labels": ["production"],
    }
    sync_langfuse.sync_prompt(mock_client, "rag-system", definition, dry_run=False)
    mock_client.create_prompt.assert_called_once()
    assert mock_client.create_prompt.call_args.kwargs["config"]["provider"] == "anthropic"
