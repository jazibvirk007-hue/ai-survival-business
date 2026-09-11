import unittest

from cortex_ai_command import CortexAICommand


class TestCortexAICommandValidation(unittest.TestCase):
    def test_select_rejects_missing_provider(self):
        with self.assertRaisesRegex(ValueError, "provider_id is required"):
            CortexAICommand().select({"model": "x"})

    def test_select_rejects_missing_model(self):
        with self.assertRaisesRegex(ValueError, "model is required"):
            CortexAICommand().select({"provider_id": "local_ollama"})

    def test_select_rejects_oversized_model(self):
        with self.assertRaisesRegex(ValueError, "model is required"):
            CortexAICommand().select({"provider_id": "local_ollama", "model": "x" * 201})


if __name__ == "__main__":
    unittest.main()
