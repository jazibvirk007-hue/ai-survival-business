import importlib
import unittest


class EngineSmokeTests(unittest.TestCase):
    def test_imports(self):
        modules = [
            "ai_brain",
            "business",
            "main",
            "market_research",
            "memory",
            "outreach",
            "payment_tracker",
            "product_factory",
            "prospect_database",
            "prospect_research",
            "prospect_scoring",
            "sales_engine",
            "website_research",
        ]
        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)

    def test_product_to_outreach_flow(self):
        from outreach import OutreachGenerator
        from product_factory import ProductFactory
        from prospect_scoring import ProspectScorer

        prospect = {
            "name": "Example Cafe",
            "category": "cafe",
            "website": "example.com",
            "phone": "+1 555 0100",
        }
        product = ProductFactory().build_product(
            "small business marketing service",
            {"opportunity": "small business marketing service", "score": 80},
        )

        # Keep this smoke test deterministic: do not make a real HTTP request.
        # This represents a successfully researched public website.
        website_data = {
            "success": True,
            "website": "https://example.com",
            "title": "Example Cafe",
            "text_length": 900,
            "signals": {
                "social_media": ["instagram"],
                "marketing": ["special offer", "book now"],
            },
        }

        score = ProspectScorer().score(prospect, website_data)
        self.assertGreaterEqual(score["score"], 50)

        draft = OutreachGenerator().generate(prospect, product, website_data)
        self.assertIsInstance(draft, dict)
        self.assertIn("message", draft)
        self.assertIn("Example Cafe", draft["message"])

    def test_payment_requires_confirmation(self):
        from payment_tracker import verify_payment
        self.assertFalse(verify_payment("missing-order", "tx-123"))
        self.assertFalse(verify_payment("missing-order", "tx-123", confirmed=False))

    def test_url_normalization(self):
        from website_research import WebsiteResearcher
        researcher = WebsiteResearcher()
        self.assertEqual(researcher.normalize_url("example.com"), "https://example.com")
        self.assertEqual(researcher.normalize_url("https.//example.com"), "https://example.com")


if __name__ == "__main__":
    unittest.main()
