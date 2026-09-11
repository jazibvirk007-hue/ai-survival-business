import pytest

from cortex_ai_command import CortexAICommand


def test_select_rejects_missing_provider():
    with pytest.raises(ValueError, match="provider_id is required"):
        CortexAICommand().select({"model": "x"})


def test_select_rejects_missing_model():
    with pytest.raises(ValueError, match="model is required"):
        CortexAICommand().select({"provider_id": "local_ollama"})


def test_select_rejects_oversized_model():
    with pytest.raises(ValueError, match="model is required"):
        CortexAICommand().select({"provider_id": "local_ollama", "model": "x" * 201})
