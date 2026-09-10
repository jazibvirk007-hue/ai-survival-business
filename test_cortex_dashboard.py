import unittest
from unittest.mock import patch

import cortex_dashboard


class FakeProvider:
    mode = "local"
    model = "test-model"
    base_url = "http://127.0.0.1:11434/v1"


class DashboardTests(unittest.TestCase):
    def test_snapshot_uses_real_ledger_values(self):
        orders = [{"order_id": "O1", "status": "payment_pending"}, {"order_id": "O2", "status": "paid"}]
        verified = [{"order_id": "O2", "amount": 25.0, "status": "verified"}]
        pending = [orders[0]]
        with patch.object(cortex_dashboard, "load_orders", return_value=orders), \
             patch.object(cortex_dashboard, "verified_payments", return_value=verified), \
             patch.object(cortex_dashboard, "pending_payments", return_value=pending), \
             patch.object(cortex_dashboard, "verified_revenue", return_value=25.0), \
             patch.object(cortex_dashboard, "provider_from_env", return_value=FakeProvider()):
            snapshot = cortex_dashboard.build_snapshot()
        self.assertEqual(snapshot["orders"], 2)
        self.assertEqual(snapshot["verified_payments"], 1)
        self.assertEqual(snapshot["pending_payments"], 1)
        self.assertEqual(snapshot["verified_revenue"], 25.0)
        self.assertEqual(snapshot["ai_provider"]["mode"], "local")
        self.assertEqual(snapshot["ai_provider"]["model"], "test-model")

    def test_snapshot_fails_closed_when_ledger_is_corrupt(self):
        with patch.object(cortex_dashboard, "load_orders", side_effect=RuntimeError("corrupt")), \
             patch.object(cortex_dashboard, "verified_payments", side_effect=RuntimeError("corrupt")), \
             patch.object(cortex_dashboard, "pending_payments", side_effect=RuntimeError("corrupt")), \
             patch.object(cortex_dashboard, "provider_from_env", return_value=FakeProvider()):
            snapshot = cortex_dashboard.build_snapshot()
        self.assertEqual(snapshot["ledger"], "DEGRADED")
        self.assertIsNone(snapshot["verified_revenue"])

    def test_handler_routes(self):
        self.assertIn("/api/status", cortex_dashboard.CortexHandler.do_GET.__code__.co_consts)
        self.assertIn("/", cortex_dashboard.HTML)
        self.assertIn("TJ CORTEX", cortex_dashboard.HTML)


if __name__ == "__main__":
    unittest.main()
