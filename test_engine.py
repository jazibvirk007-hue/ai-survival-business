import importlib
import json
import os
import tempfile
import unittest
from unittest import mock


class EngineSmokeTests(unittest.TestCase):
    def test_imports(self):
        modules = [
            "ai_brain", "ai_ceo", "business", "main", "market_research", "memory",
            "order_engine", "outreach", "payment_tracker", "payment_webhook",
            "product_factory", "prospect_database", "prospect_research",
            "prospect_scoring", "sales_engine", "website_research",
        ]
        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)

    def test_product_to_outreach_flow(self):
        from outreach import OutreachGenerator
        from product_factory import ProductFactory
        from prospect_scoring import ProspectScorer
        prospect = {"name": "Example Cafe", "category": "cafe", "website": "example.com", "phone": "+1 555 0100"}
        product = ProductFactory().build_product("small business marketing service", {"opportunity": "small business marketing service", "score": 80})
        website_data = {"success": True, "website": "https://example.com", "title": "Example Cafe", "text_length": 900, "signals": {"social_media": ["instagram"], "marketing": ["special offer", "book now"]}}
        score = ProspectScorer().score(prospect, website_data)
        self.assertGreaterEqual(score["score"], 50)
        draft = OutreachGenerator().generate(prospect, product, website_data)
        self.assertIsInstance(draft, dict)
        self.assertIn("message", draft)
        self.assertIn("Example Cafe", draft["message"])

    def test_payment_requires_confirmation(self):
        from payment_tracker import create_payment_request, verify_payment, verified_revenue
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
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
            finally: os.chdir(original)

    def test_payment_ledger_rejects_duplicate_order_records(self):
        from payment_tracker import verify_payment
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                with open("payments.json", "w", encoding="utf-8") as file:
                    json.dump([{"order_id": "order-1", "amount": 35, "status": "requested"}, {"order_id": "order-1", "amount": 35, "status": "requested"}], file)
                self.assertFalse(verify_payment("order-1", "tx-duplicate", confirmed=True))
            finally: os.chdir(original)

    def test_corrupt_payment_ledger_fails_closed(self):
        from payment_tracker import load_payments
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                with open("payments.json", "w", encoding="utf-8") as file: file.write("not-json")
                with self.assertRaises(RuntimeError): load_payments()
            finally: os.chdir(original)

    def test_verified_revenue_deduplicates_corrupt_records(self):
        from payment_tracker import verified_payments, verified_revenue
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                with open("payments.json", "w", encoding="utf-8") as file:
                    json.dump([{"order_id": "order-1", "amount": 35, "status": "verified", "transaction_id": "tx-1"}, {"order_id": "order-1", "amount": 35, "status": "verified", "transaction_id": "tx-1"}, {"order_id": "order-2", "amount": 50, "status": "verified", "transaction_id": "tx-2"}], file)
                self.assertEqual(verified_revenue(), 85.0)
                self.assertEqual(len(verified_payments()), 2)
            finally: os.chdir(original)

    def test_monetary_precision_and_invalid_values(self):
        from payment_tracker import create_payment_request, verified_revenue
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                create_payment_request("order-precise", "0.10")
                self.assertAlmostEqual(verified_revenue(), 0.0)
                with self.assertRaises(ValueError): create_payment_request("order-zero", "0")
                with self.assertRaises(ValueError): create_payment_request("order-nan", "NaN")
                with self.assertRaises(ValueError): create_payment_request("order-inf", "Infinity")
                with self.assertRaises(ValueError): create_payment_request("order-currency", 10, "USDX")
            finally: os.chdir(original)

    def test_order_lifecycle_is_payment_gated(self):
        from order_engine import create_order, get_order, mark_delivered, verify_order_payment
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                order = create_order("ORD-TEST-1", "Customer", "Example Cafe", "Growth Kit", 35)
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
            finally: os.chdir(original)

    def test_delivery_path_traversal_is_rejected(self):
        from order_engine import create_order, mark_delivered, verify_order_payment
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                create_order("ORD-PATH", "Customer", "Cafe", "Kit", 35)
                self.assertTrue(verify_order_payment("ORD-PATH", "tx-path", confirmed=True))
                self.assertFalse(mark_delivered("ORD-PATH", "../secret.txt"))
                self.assertFalse(mark_delivered("ORD-PATH", "/tmp/secret.txt"))
                self.assertFalse(mark_delivered("ORD-PATH", "exports/secret.txt"))
            finally: os.chdir(original)

    def test_corrupt_order_ledger_fails_closed(self):
        from order_engine import load_orders
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                with open("orders.json", "w", encoding="utf-8") as file: file.write("not-json")
                with self.assertRaises(RuntimeError): load_orders()
            finally: os.chdir(original)

    def test_order_payment_amount_must_match(self):
        from order_engine import create_order, get_order, verify_order_payment
        from payment_tracker import load_payments, save_payments
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                create_order("ORD-TEST-2", "Customer", "Example Cafe", "Growth Kit", 35)
                payments = load_payments(); payments[0]["amount"] = 34; save_payments(payments)
                self.assertFalse(verify_order_payment("ORD-TEST-2", "tx-2", confirmed=True))
                self.assertEqual(get_order("ORD-TEST-2")["payment_status"], "unpaid")
            finally: os.chdir(original)

    def test_order_creation_rolls_back_if_payment_request_fails(self):
        import order_engine
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                with mock.patch.object(order_engine, "create_payment_request", side_effect=RuntimeError("gateway unavailable")):
                    with self.assertRaises(RuntimeError): order_engine.create_order("ORD-ROLLBACK", "Customer", "Cafe", "Kit", 25)
                self.assertIsNone(order_engine.get_order("ORD-ROLLBACK"))
                self.assertEqual(order_engine.load_orders(), [])
            finally: os.chdir(original)

    def test_webhook_requires_valid_signature(self):
        from payment_webhook import process_webhook
        body = json.dumps({"event_id": "evt-1", "type": "payment.succeeded", "order_id": "ORD-TEST", "transaction_id": "tx-1", "amount": 35, "currency": "USD"}).encode()
        self.assertEqual(process_webhook(body, "sha256=bad", "secret")["status"], 401)

    def test_webhook_verifies_and_is_idempotent(self):
        from order_engine import create_order, get_order
        from payment_webhook import process_webhook, sign_payload
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                create_order("ORD-WEBHOOK", "Customer", "Cafe", "Kit", 35, "USD")
                body = json.dumps({"event_id": "evt-1", "type": "payment.succeeded", "order_id": "ORD-WEBHOOK", "transaction_id": "tx-web-1", "amount": 35, "currency": "USD"}, separators=(",", ":")).encode()
                signature = sign_payload(body, "secret")
                result = process_webhook(body, signature, "secret")
                self.assertTrue(result["ok"])
                self.assertEqual(get_order("ORD-WEBHOOK")["payment_status"], "paid")
                duplicate = process_webhook(body, signature, "secret")
                self.assertTrue(duplicate["ok"])
                self.assertTrue(duplicate["duplicate"])
            finally: os.chdir(original)

    def test_webhook_rejects_amount_or_currency_mismatch(self):
        from order_engine import create_order, get_order
        from payment_webhook import process_webhook, sign_payload
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                create_order("ORD-WEBHOOK-2", "Customer", "Cafe", "Kit", 35, "USD")
                body = json.dumps({"event_id": "evt-2", "type": "payment.succeeded", "order_id": "ORD-WEBHOOK-2", "transaction_id": "tx-web-2", "amount": 34, "currency": "USD"}).encode()
                result = process_webhook(body, sign_payload(body, "secret"), "secret")
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], 400)
                self.assertEqual(get_order("ORD-WEBHOOK-2")["payment_status"], "unpaid")
            finally: os.chdir(original)

    def test_corrupt_webhook_event_store_fails_closed(self):
        from payment_webhook import process_webhook, sign_payload
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                with open("webhook_events.json", "w", encoding="utf-8") as file: file.write("not-json")
                body = json.dumps({"event_id": "evt-corrupt", "type": "payment.succeeded", "order_id": "ORD-MISSING", "transaction_id": "tx", "amount": 35, "currency": "USD"}).encode()
                result = process_webhook(body, sign_payload(body, "secret"), "secret")
                self.assertEqual(result["status"], 503)
            finally: os.chdir(original)

    def test_webhook_rejects_non_finite_amount(self):
        from order_engine import create_order
        from payment_webhook import process_webhook, sign_payload
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.getcwd(); os.chdir(temp_dir)
            try:
                create_order("ORD-WEBHOOK-3", "Customer", "Cafe", "Kit", 35, "USD")
                body = json.dumps({"event_id": "evt-3", "type": "payment.succeeded", "order_id": "ORD-WEBHOOK-3", "transaction_id": "tx-web-3", "amount": "NaN", "currency": "USD"}).encode()
                result = process_webhook(body, sign_payload(body, "secret"), "secret")
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], 400)
            finally: os.chdir(original)

    def test_url_normalization(self):
        from website_research import WebsiteResearcher
        researcher = WebsiteResearcher()
        self.assertEqual(researcher.normalize_url("example.com"), "https://example.com")
        self.assertEqual(researcher.normalize_url("https.//example.com"), "https://example.com")

    def test_sales_pipeline_rejects_corrupt_non_list_file(self):
        from sales_engine import SalesEngine
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "pipeline.json")
            with open(path, "w", encoding="utf-8") as file: file.write('{"unexpected": "object"}')
            self.assertEqual(SalesEngine(path).load(), [])

    def test_business_financials_only_use_verified_values(self):
        from business import Business
        business = Business(); business.sync_verified_financials(0, 0)
        self.assertEqual(business.revenue, 0.0)
        self.assertEqual(business.money, 0.0)
        self.assertEqual(business.customers, 0)


if __name__ == "__main__":
    unittest.main()
