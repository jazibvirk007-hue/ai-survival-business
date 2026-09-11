import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cortex_ai_command import CortexAICommand
from cortex_ai_control import AIControlSelection


class FakeRuntime:
    def status(self, selection):
        return {
            "provider_id": selection.provider_id,
            "provider": "Test Provider",
            "protocol": "openai_compatible",
            "model": selection.model,
            "configured": True,
            "credential_env": "SECRET_ENV",
        }

    def generate(self, selection, messages, temperature=0):
        return "CORTEX_CONNECTION_OK"

    def discover_models(self, provider_id):
        return ["model-a", "model-b"]


class CortexAICommandTests(unittest.TestCase):
    def test_catalog_is_browser_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = CortexAICommand(runtime=FakeRuntime(), selection_path=str(Path(tmp) / "selection.json"))
            payload = json.dumps(command.catalog()).lower()
            self.assertNotIn("api_key", payload)
            self.assertIn("google_gemini", payload)

    def test_selection_and_model_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.json"
            command = CortexAICommand(runtime=FakeRuntime(), selection_path=str(path))
            result = command.select({"provider_id": "openai", "model": "model-a"})
            self.assertTrue(result["selected"])
            self.assertEqual(command.models("openai")["models"], ["model-a", "model-b"])

    def test_selection_file_contains_no_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.json"
            command = CortexAICommand(runtime=FakeRuntime(), selection_path=str(path))
            command.select({"provider_id": "openai", "model": "model-a"})
            self.assertNotIn("SECRET", path.read_text(encoding="utf-8"))

    def test_connection_test_is_successful_without_returning_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = CortexAICommand(runtime=FakeRuntime(), selection_path=str(Path(tmp) / "selection.json"))
            command.select({"provider_id": "openai", "model": "model-a"})
            result = command.connection_test()
            self.assertTrue(result["ok"])
            self.assertNotIn("credential_env", result)
            self.assertNotIn("SECRET", json.dumps(result))

    def test_connection_test_fails_without_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = CortexAICommand(runtime=FakeRuntime(), selection_path=str(Path(tmp) / "selection.json"))
            self.assertFalse(command.connection_test()["ok"])


if __name__ == "__main__":
    unittest.main()
