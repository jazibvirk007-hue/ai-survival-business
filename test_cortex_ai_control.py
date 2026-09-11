import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cortex_ai_control import AIControlSelection, load_selection, safe_provider_catalog, safe_selection_status, save_selection
from cortex_ai_runtime import CortexAIRuntime


class CortexAIControlTests(unittest.TestCase):
    def test_save_and_load_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.json"
            save_selection(AIControlSelection("google_gemini", "gemini-test"), path)
            self.assertEqual(load_selection(path), AIControlSelection("google_gemini", "gemini-test"))

    def test_corrupt_selection_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.json"
            path.write_text("not-json", encoding="utf-8")
            self.assertIsNone(load_selection(path))

    def test_invalid_provider_rejected(self):
        with self.assertRaises(ValueError):
            save_selection(AIControlSelection("unknown", "model"), "/tmp/cortex-invalid.json")

    def test_catalog_has_no_secret_values(self):
        catalog = safe_provider_catalog()
        encoded = json.dumps(catalog).lower()
        self.assertNotIn("api_key", encoded)
        self.assertTrue(any(item["id"] == "google_gemini" for item in catalog))

    def test_status_does_not_expose_credential_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.json"
            save_selection(AIControlSelection("openai", "model-a"), path)
            runtime = CortexAIRuntime()
            with patch.dict("os.environ", {"OPENAI_API_KEY": "SECRET"}, clear=False):
                status = safe_selection_status(runtime, path)
            self.assertTrue(status["configured"])
            self.assertNotIn("SECRET", json.dumps(status))
            self.assertNotIn("credential_env", status)


if __name__ == "__main__":
    unittest.main()
