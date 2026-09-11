import unittest
from unittest.mock import patch

from cortex_live_observability import build_live_observability


class LiveObservabilityTests(unittest.TestCase):
    @patch("cortex_live_observability.communication_status", return_value={"enabled": True, "events": 2, "live_stream_ready": True})
    @patch("cortex_live_observability.recent_messages", return_value=[{"id": "e2", "sender": "CEO", "recipient": "Growth", "summary": "ranked"}])
    def test_combines_bounded_read_only_surfaces(self, messages, status):
        result = build_live_observability({"history": [{"cycle_id": "c1", "action": "research_market", "executed": False}]}, limit=10)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["cycles"]["count"], 1)
        self.assertEqual(len(result["communications"]["events"]), 1)
        self.assertIn("observational only", result["truth_policy"])


if __name__ == "__main__":
    unittest.main()
