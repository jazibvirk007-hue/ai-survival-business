import importlib
import os
import tempfile
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
        from payment_tracker import create_payment_request, verify_payment, verified_revenue

        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd()
            os.chdir(temp_dir)
            try:
                create_payment_request("order-1", 35)
                self.assertFalse(verify_payment("order-1", "tx-123"))
                self.assertFalse(verify_payment("order-1", "tx-123", confirmed=False))
                self.assertEqual(verified_revenue(), 0.0)
                self.assertTrue(verify_payment("order-1", "tx-123", confirmed=True))
                self.assertEqual(verified_revenue(), 35.0)
                self.assertTrue(verify_payment("order-1", "tx-123", confirmed=True))

                create_payment_request("order-2", 50)
                self.assertFalse(verify_payment("order-2", "tx-123", confirmed=True))
                self.assertEqual(verified_revenue(), 35.0)
            finally:
                os.chdir(original)

    def test_url_normalization(self):
        from website_research import WebsiteResearcher
        researcher = WebsiteResearcher()
        self.assertEqual(researcher.normalize_url("example.com"), "https://example.com")
        self.assertEqual(researcher.normalize_url("https.//example.com"), "https://example.com")

    def test_sales_pipeline_rejects_corrupt_non_list_file(self):
        from sales_engine import SalesEngine

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "pipeline.json")
            with open(path, "w", encoding="utf-8") as file:
                file.write('{"unexpected": "object"}')
            self.assertEqual(SalesEngine(path).load(), [])

    def test_business_financials_only_use_verified_values(self):
        from business import Business

        business = Business()
        business.sync_verified_financials(0, 0)
        self.assertEqual(business.revenue, 0.0)
        self.assertEqual(business.money, 0.0)
        self.assertEqual(business.customers, 0)


if __name__ == "__main__":
    unittest.main()
