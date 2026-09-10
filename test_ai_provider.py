import json
import os
import unittest
from urllib.error import URLError

from ai_provider import AIProviderConfig, AIProviderError, OpenAICompatibleProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class FakeOpener:
    def __init__(self, payload=None, error=None):
        self.payload = payload or {"data": [{"id": "test-model"}]}
        self.error = error
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        if self.error:
            raise self.error
        return FakeResponse(self.payload)


class AIProviderTests(unittest.TestCase):
    def test_local_connection_does_not_need_key(self):
        opener = FakeOpener()
        provider = OpenAICompatibleProvider(
            AIProviderConfig(mode="local", model="test-model"), opener=opener
        )
        status = provider.test_connection()
        self.assertTrue(status["connected"])
        self.assertEqual(status["models"], ["test-model"])
        self.assertNotIn("api_key", status)

    def test_api_requires_server_side_key(self):
        old = os.environ.pop("TJ_CORTEX_AI_API_KEY", None)
        try:
            provider = OpenAICompatibleProvider(
                AIProviderConfig(mode="api", base_url="https://example.test/v1", model="test-model"),
                opener=FakeOpener(),
            )
            status = provider.test_connection()
            self.assertFalse(status["connected"])
            self.assertIn("server-side", status["error"])
        finally:
            if old is not None:
                os.environ["TJ_CORTEX_AI_API_KEY"] = old

    def test_api_key_is_sent_only_as_authorization_header(self):
        old = os.environ.get("TJ_CORTEX_AI_API_KEY")
        os.environ["TJ_CORTEX_AI_API_KEY"] = "secret-value"
        try:
            opener = FakeOpener({"choices": [{"message": {"content": "hello"}}]})
            provider = OpenAICompatibleProvider(
                AIProviderConfig(mode="api", base_url="https://example.test/v1", model="test-model"),
                opener=opener,
            )
            self.assertEqual(provider.generate([{"role": "user", "content": "hi"}]), "hello")
            headers = opener.requests[0][0].headers
            self.assertEqual(headers.get("Authorization"), "Bearer secret-value")
        finally:
            if old is None:
                os.environ.pop("TJ_CORTEX_AI_API_KEY", None)
            else:
                os.environ["TJ_CORTEX_AI_API_KEY"] = old

    def test_connection_failure_is_safe(self):
        provider = OpenAICompatibleProvider(
            AIProviderConfig(model="test-model"), opener=FakeOpener(error=URLError("offline"))
        )
        status = provider.test_connection()
        self.assertFalse(status["connected"])
        self.assertIn("connection failed", status["error"])

    def test_invalid_provider_configuration_rejected(self):
        with self.assertRaises(ValueError):
            AIProviderConfig(mode="unknown", model="test-model")
        with self.assertRaises(ValueError):
            AIProviderConfig(model="")
        with self.assertRaises(ValueError):
            AIProviderConfig(model="test-model", timeout_seconds=0)

    def test_bad_generation_response_fails_closed(self):
        provider = OpenAICompatibleProvider(
            AIProviderConfig(model="test-model"), opener=FakeOpener({"choices": []})
        )
        with self.assertRaises(AIProviderError):
            provider.generate([{"role": "user", "content": "hi"}])


if __name__ == "__main__":
    unittest.main()
