import json
import os
import unittest
from unittest.mock import patch

from cortex_ai_runtime import AIRuntimeError, AISelection, CortexAIRuntime


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.payload


def opener_for(payload):
    def opener(request, timeout):
        return FakeResponse(payload)
    return opener


class CortexAIRuntimeTests(unittest.TestCase):
    def test_openai_compatible_model_discovery(self):
        runtime = CortexAIRuntime(opener=opener_for({"data": [{"id": "model-a"}, {"id": "model-b"}]}))
        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=False):
            self.assertEqual(runtime.discover_models("openai"), ["model-a", "model-b"])

    def test_gemini_model_discovery(self):
        runtime = CortexAIRuntime(opener=opener_for({"models": [{"name": "models/gemini-test"}]}))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret"}, clear=False):
            self.assertEqual(runtime.discover_models("google_gemini"), ["gemini-test"])

    def test_anthropic_native_generation(self):
        runtime = CortexAIRuntime(opener=opener_for({"content": [{"text": "hello"}]}))
        selection = AISelection("anthropic", "claude-test")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "secret"}, clear=False):
            self.assertEqual(runtime.generate(selection, [{"role": "user", "content": "hi"}]), "hello")

    def test_gemini_native_generation(self):
        runtime = CortexAIRuntime(opener=opener_for({"candidates": [{"content": {"parts": [{"text": "hello"}]}}]}))
        selection = AISelection("google_gemini", "gemini-test")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret"}, clear=False):
            self.assertEqual(runtime.generate(selection, [{"role": "user", "content": "hi"}]), "hello")

    def test_cohere_native_generation(self):
        runtime = CortexAIRuntime(opener=opener_for({"message": {"content": [{"text": "hello"}]}}))
        selection = AISelection("cohere", "command-test")
        with patch.dict(os.environ, {"COHERE_API_KEY": "secret"}, clear=False):
            self.assertEqual(runtime.generate(selection, [{"role": "user", "content": "hi"}]), "hello")

    def test_missing_secret_fails_closed(self):
        runtime = CortexAIRuntime(opener=opener_for({}))
        selection = AISelection("openai", "model-a")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(AIRuntimeError):
                runtime.generate(selection, [{"role": "user", "content": "hi"}])

    def test_status_never_contains_secret(self):
        runtime = CortexAIRuntime()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "TOP_SECRET"}, clear=False):
            status = runtime.status(AISelection("openai", "model-a"))
        self.assertTrue(status["configured"])
        self.assertNotIn("TOP_SECRET", str(status))


if __name__ == "__main__":
    unittest.main()
