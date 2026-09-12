import hashlib
import hmac
import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

import cortex_stripe_adapter as stripe


class StripeAdapterTests(unittest.TestCase):
    def test_signature_verification_accepts_fresh_valid_signature(self):
        body = b'{"id":"evt_test"}'
        secret = "whsec_test"
        timestamp = 1_700_000_000
        digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        signature = f"t={timestamp},v1={digest}"
        self.assertTrue(stripe.verify_stripe_signature(body, signature, secret, now=timestamp))

    def test_signature_verification_rejects_stale_signature(self):
        body = b"{}"
        secret = "whsec_test"
        timestamp = 1_700_000_000
        digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        self.assertFalse(stripe.verify_stripe_signature(body, f"t={timestamp},v1={digest}", secret, now=timestamp + 301))

    def test_connect_rejects_bad_key_without_network(self):
        self.assertEqual(stripe.connect("not-a-stripe-key")["status"], 400)

    def test_status_is_disconnected_without_credentials(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"CORTEX_STRIPE_CREDENTIALS_FILE": os.path.join(directory, "stripe.json")}, clear=False):
            self.assertFalse(stripe.status()["connected"])

    def test_process_checkout_event_normalizes_to_cortex_payment(self):
        timestamp = int(time.time())
        secret = "whsec_test"
        payload = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {"object": {
                "id": "cs_123",
                "payment_status": "paid",
                "amount_total": 1250,
                "currency": "usd",
                "payment_intent": "pi_123",
                "metadata": {"cortex_order_id": "order_123"},
            }},
        }
        raw = json.dumps(payload, separators=(",", ":")).encode()
        digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()
        with patch.object(stripe, "process_event", return_value={"ok": True, "status": 200, "order_id": "order_123"}) as processor:
            result = stripe.process_stripe_webhook(raw, f"t={timestamp},v1={digest}", secret)
        self.assertEqual(result["status"], 200)
        processor.assert_called_once_with({
            "event_id": "evt_123",
            "type": "payment.succeeded",
            "order_id": "order_123",
            "transaction_id": "pi_123",
            "amount": "12.50",
            "currency": "USD",
        })


if __name__ == "__main__":
    unittest.main()
