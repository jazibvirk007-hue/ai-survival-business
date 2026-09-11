import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cortex_ai_control import AIControlSelection, save_selection
from cortex_ai_factory import build_runtime


class TestCortexAIFactory(unittest.TestCase):
    def test_factory_returns_none_without_selection(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            self.assertIsNone(build_runtime(selection_path=path))

    def test_factory_loads_governed_selection(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.json"
            save_selection(AIControlSelection("local_ollama", "test-model"), path)
            bundle = build_runtime(selection_path=path)
            self.assertIsNotNone(bundle)
            self.assertEqual(bundle.selection.provider_id, "local_ollama")
            self.assertEqual(bundle.selection.model, "test-model")

    def test_factory_accepts_test_opener(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.json"
            save_selection(AIControlSelection("local_ollama", "test-model"), path)

            def opener(*args, **kwargs):
                raise OSError("offline")

            bundle = build_runtime(selection_path=path, opener=opener)
            self.assertIsNotNone(bundle)
            self.assertEqual(bundle.runtime.timeout_seconds, 30.0)


if __name__ == "__main__":
    unittest.main()
