import unittest

from cortex_ai_catalog import get_provider, providers


class CortexAICatalogTests(unittest.TestCase):
    def test_core_provider_families_are_available(self):
        ids = {item["id"] for item in providers()}
        for expected in {"local_ollama", "openai", "google_gemini", "anthropic", "mistral", "xai", "deepseek", "groq", "cohere", "together", "openrouter", "custom_openai"}:
            self.assertIn(expected, ids)

    def test_catalog_never_contains_secret_values(self):
        for item in providers():
            self.assertNotIn("api_key", item)
            self.assertNotIn("secret", item)
            self.assertNotIn("token", item)

    def test_provider_lookup(self):
        google = get_provider("google_gemini")
        self.assertEqual(google.auth_env, "GEMINI_API_KEY")
        self.assertEqual(google.protocol, "gemini")

    def test_unknown_provider_rejected(self):
        with self.assertRaises(ValueError):
            get_provider("not-a-provider")


if __name__ == "__main__":
    unittest.main()
