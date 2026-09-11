from pathlib import Path

from cortex_ai_control import AIControlSelection, save_selection
from cortex_ceo_config import ai_advisory_from_env


def test_invalid_legacy_provider_fails_closed(monkeypatch):
    monkeypatch.delenv("TJ_CORTEX_AI_AUGMENT", raising=False)
    monkeypatch.setenv("TJ_CORTEX_AI_PROVIDER", "not-a-provider")
    monkeypatch.setenv("TJ_CORTEX_AI_MODEL", "model")
    runtime, selection, enabled = ai_advisory_from_env()
    assert runtime is None
    assert selection is None
    assert enabled is False


def test_persisted_selection_is_authoritative(monkeypatch, tmp_path: Path):
    path = tmp_path / "selection.json"
    save_selection(AIControlSelection("local_ollama", "persisted-model"), path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TJ_CORTEX_AI_AUGMENT", "true")
    monkeypatch.setenv("TJ_CORTEX_AI_PROVIDER", "not-a-provider")
    monkeypatch.setenv("TJ_CORTEX_AI_MODEL", "wrong-model")
    runtime, selection, enabled = ai_advisory_from_env()
    assert runtime is not None
    assert selection is not None
    assert selection.provider_id == "local_ollama"
    assert selection.model == "persisted-model"
    assert enabled is True
