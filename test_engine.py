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
            "outreach",
            "order_manager",
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

    def test_order_lifecycle_payment_must_match_amount_and_currency(self):
        from order_manager import OrderManager

        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd()
            os.chdir(temp_dir)
            try:
                manager = OrderManager()
                order = manager.create_order("Customer", "Example Cafe", "Growth Kit", 35, "USD")
                self.assertEqual(order["status"], "payment_pending")
                self.assertFalse(manager.confirm_payment(order["order_id"], "tx-amount", confirmed=True))

                payments = manager.load_payment_records()
                payments[0]["amount"] = 34
                with open("payments.json", "w", encoding="utf-8") as file:
                    json.dump(payments, file)
                self.assertFalse(manager.confirm_payment(order["order_id"], "tx-amount", confirmed=True))

                payments[0]["amount"] = 35
                payments[0]["currency"] = "EUR"
                with open("payments.json", "w", encoding="utf-8") as file:
                    json.dump(payments, file)
                self.assertFalse(manager.confirm_payment(order["order_id"], "tx-currency", confirmed=True))
            finally:
                os.chdir(original)

    def test_order_lifecycle_blocks_delivery_until_verified_payment(self):
        from order_manager import OrderManager

        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd()
            os.chdir(temp_dir)
            try:
                manager = OrderManager()
                order = manager.create_order("Customer", "Example Cafe", "Growth Kit", 35)
                self.assertFalse(manager.mark_delivered(order["order_id"], "deliveries/file.txt"))
                self.assertFalse(manager.complete_order(order["order_id"]))

                self.assertTrue(manager.confirm_payment(order["order_id"], "tx-paid", confirmed=True))
                paid = manager.get_order(order["order_id"])
                self.assertEqual(paid["status"], "paid")
                self.assertEqual(paid["payment_status"], "paid")

                self.assertTrue(manager.mark_delivered(order["order_id"], "deliveries/file.txt"))
                delivered = manager.get_order(order["order_id"])
                self.assertEqual(delivered["status"], "delivered")
                self.assertTrue(manager.complete_order(order["order_id"]))
                self.assertEqual(manager.get_order(order["order_id"])["status"], "completed")
                self.assertTrue(manager.complete_order(order["order_id"]))
            finally:
                os.chdir(original)

    def test_order_lifecycle_rejects_transaction_reuse(self):
        from order_manager import OrderManager

        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd()
            os.chdir(temp_dir)
            try:
                manager = OrderManager()
                first = manager.create_order("A", "Cafe A", "Growth Kit", 35)
                second = manager.create_order("B", "Cafe B", "Growth Kit", 35)
                self.assertTrue(manager.confirm_payment(first["order_id"], "tx-shared", confirmed=True))
                self.assertFalse(manager.confirm_payment(second["order_id"], "tx-shared", confirmed=True))
                self.assertEqual(manager.get_order(second["order_id"])["status"], "payment_pending")
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
