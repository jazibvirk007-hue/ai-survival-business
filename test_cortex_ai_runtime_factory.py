import json
import tempfile
import unittest
from pathlib import Path

from cortex_ai_runtime_factory import build_configured_ai


class CortexAIRuntimeFactoryTests(unittest.TestCase):
    def test_unconfigured_is_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_configured_ai(selection_path=str(Path(tmp) / "missing.json"))
        self.assertIsNotNone(result["runtime"])
        self.assertIsNone(result["selection"])
        self.assertFalse(result["status"]["selected"])

    def test_persisted_selection_is_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.json"
            path.write_text(json.dumps({"provider_id": "openai", "model": "model-a"}), encoding="utf-8")
            result = build_configured_ai(selection_path=str(path))
        self.assertEqual(result["selection"].provider_id, "openai")
        self.assertEqual(result["selection"].model, "model-a")
        self.assertTrue(result["status"]["selected"])
        self.assertNotIn("credential_env", result["status"])


if __name__ == "__main__":
    unittest.main()
