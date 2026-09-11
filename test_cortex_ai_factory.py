from pathlib import Path

from cortex_ai_control import AIControlSelection, save_selection
from cortex_ai_factory import build_runtime


def test_factory_returns_none_without_selection(tmp_path: Path):
    assert build_runtime(selection_path=tmp_path / "missing.json") is None


def test_factory_loads_governed_selection(tmp_path: Path):
    path = tmp_path / "selection.json"
    save_selection(AIControlSelection("local_ollama", "test-model"), path)
    bundle = build_runtime(selection_path=path)
    assert bundle is not None
    assert bundle.selection.provider_id == "local_ollama"
    assert bundle.selection.model == "test-model"


def test_factory_accepts_test_opener(tmp_path: Path):
    path = tmp_path / "selection.json"
    save_selection(AIControlSelection("local_ollama", "test-model"), path)

    def opener(*args, **kwargs):
        raise OSError("offline")

    bundle = build_runtime(selection_path=path, opener=opener)
    assert bundle is not None
    assert bundle.runtime.timeout_seconds == 30.0
