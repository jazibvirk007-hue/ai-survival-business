import io
import unittest
from unittest.mock import patch

from cortex_web_research import CortexWebResearch, WebResearchError


class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class FakeResponse:
    def __init__(self, body, content_type="text/html"):
        self.body = body.encode("utf-8")
        self.headers = FakeHeaders({"Content-Type": content_type})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body if size < 0 else self.body[:size]


class CortexWebResearchTests(unittest.TestCase):
    def opener(self, request, timeout=0):
        return FakeResponse(
            '<a class="result__a" href="https://example.com/a">Example</a>'
            '<div class="result__snippet">A useful market signal.</div>'
        )

    def test_search_returns_public_results(self):
        engine = CortexWebResearch(opener=self.opener)
        results = engine.search("digital products")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Example")
        self.assertEqual(results[0].source, "public_web_search")

    def test_private_targets_are_blocked(self):
        with patch("cortex_web_research.socket.getaddrinfo", return_value=[(None, None, None, None, ("127.0.0.1", 0))]):
            with self.assertRaises(WebResearchError):
                CortexWebResearch._validate_public_url("http://127.0.0.1:8080")

    def test_non_html_is_rejected(self):
        def opener(request, timeout=0):
            return FakeResponse("PDF", "application/pdf")

        with self.assertRaises(WebResearchError):
            CortexWebResearch(opener=opener)._get("https://example.com/file.pdf")

    def test_query_is_bounded(self):
        with self.assertRaises(ValueError):
            CortexWebResearch(opener=self.opener).search("x" * 501)

    def test_status_is_explicit(self):
        status = CortexWebResearch(opener=self.opener).status()
        self.assertEqual(status["internet"], "public_http_https")
        self.assertEqual(status["private_network_targets"], "blocked")


if __name__ == "__main__":
    unittest.main()
