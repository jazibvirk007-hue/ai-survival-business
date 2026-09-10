import importlib
import json
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
            "order_engine",
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

    def test_payment_ledger_rejects_duplicate_order_records(self):
        from payment_tracker import verify_payment

        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd()
            os.chdir(temp_dir)
            try:
                payments = [
                    {"order_id": "order-1", "amount": 35, "status": "requested"},
                    {"order_id": "order-1", "amount": 35, "status": "requested"},
                ]
                with open("payments.json", "w", encoding="utf-8") as file:
                    json.dump(payments, file)
                self.assertFalse(verify_payment("order-1", "tx-duplicate", confirmed=True))
            finally:
                os.chdir(original)

    def test_verified_revenue_deduplicates_corrupt_records(self):
        from payment_tracker import verified_payments, verified_revenue

        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd()
            os.chdir(temp_dir)
            try:
                payments = [
                    {"order_id": "order-1", "amount": 35, "status": "verified", "transaction_id": "tx-1"},
                    {"order_id": "order-1", "amount": 35, "status": "verified", "transaction_id": "tx-1"},
                    {"order_id": "order-2", "amount": 50, "status": "verified", "transaction_id": "tx-2"},
                ]
                with open("payments.json", "w", encoding="utf-8") as file:
                    json.dump(payments, file)
                self.assertEqual(verified_revenue(), 85.0)
                self.assertEqual(len(verified_payments()), 2)
            finally:
                os.chdir(original)

    def test_order_lifecycle_is_payment_gated(self):
        from order_engine import create_order, get_order, mark_delivered, verify_order_payment

        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd()
            os.chdir(temp_dir)
            try:
                order = create_order(
                    "ORD-TEST-1", "Customer", "Example Cafe", "Growth Kit", 35
                )
                self.assertEqual(order["status"], "payment_pending")
                self.assertEqual(order["payment_status"], "unpaid")
                self.assertFalse(mark_delivered("ORD-TEST-1", "deliveries/test.txt"))

                self.assertFalse(verify_order_payment("ORD-TEST-1", "tx-1", confirmed=False))
                self.assertEqual(get_order("ORD-TEST-1")["payment_status"], "unpaid")

                self.assertTrue(verify_order_payment("ORD-TEST-1", "tx-1", confirmed=True))
                paid = get_order("ORD-TEST-1")
                self.assertEqual(paid["status"], "paid")
                self.assertEqual(paid["payment_status"], "paid")
                self.assertEqual(paid["delivery_status"], "ready")

                self.assertTrue(mark_delivered("ORD-TEST-1", "deliveries/ORD-TEST-1.txt"))
                delivered = get_order("ORD-TEST-1")
                self.assertEqual(delivered["status"], "delivered")
                self.assertEqual(delivered["delivery_status"], "delivered")
            finally:
                os.chdir(original)

    def test_order_payment_amount_must_match(self):
        from order_engine import create_order, get_order, verify_order_payment
        from payment_tracker import load_payments, save_payments

        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd()
            os.chdir(temp_dir)
            try:
                create_order("ORD-TEST-2", "Customer", "Example Cafe", "Growth Kit", 35)
                payments = load_payments()
                payments[0]["amount"] = 34
                save_payments(payments)
                self.assertFalse(verify_order_payment("ORD-TEST-2", "tx-2", confirmed=True))
                self.assertEqual(get_order("ORD-TEST-2")["payment_status"], "unpaid")
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
