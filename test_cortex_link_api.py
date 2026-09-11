import unittest

from cortex_link_api import CortexLinkAPI


class FakeCommand:
    def catalog(self):
        return {"providers": [{"id": "local_ollama", "name": "Ollama"}]}
    def selected(self):
        return {"selected": True, "provider_id": "local_ollama", "model": "test", "configured": True}
    def models(self, provider_id):
        if provider_id != "local_ollama":
            raise ValueError("bad provider")
        return {"provider_id": provider_id, "models": ["test"]}
    def select(self, payload):
        return {"selected": True, **payload}
    def connection_test(self):
        return {"ok": True, "provider_id": "local_ollama", "model": "test"}


class CortexLinkAPITests(unittest.TestCase):
    def setUp(self):
        self.api = CortexLinkAPI(command=FakeCommand())

    def test_routes_catalog(self):
        status, body = self.api.handle("GET", "/api/ai/catalog")
        self.assertEqual(status, 200)
        self.assertEqual(body["providers"][0]["id"], "local_ollama")

    def test_routes_model_discovery(self):
        status, body = self.api.handle("GET", "/api/ai/models", provider_id="local_ollama")
        self.assertEqual(status, 200)
        self.assertEqual(body["models"], ["test"])

    def test_selection_is_bounded(self):
        status, body = self.api.handle("POST", "/api/ai/select", {"provider_id": "local_ollama", "model": "test"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_credentials_are_not_an_api_surface(self):
        status, body = self.api.handle("POST", "/api/ai/select", {"provider_id": "local_ollama", "model": "test", "api_key": "secret"})
        self.assertEqual(status, 200)
        self.assertNotIn("api_key", body)

    def test_unknown_route(self):
        status, body = self.api.handle("GET", "/api/ai/secret")
        self.assertEqual(status, 404)
        self.assertFalse(body["ok"])


if __name__ == "__main__":
    unittest.main()
