import unittest

from cortex_cycle_history import build_cycle_history


class CycleHistoryTests(unittest.TestCase):
    def test_newest_first_and_bounded(self):
        snapshot = {"history": [{"cycle_id": "1", "action": "research_market", "executed": True, "outcome": {"success": True}}, {"cycle_id": "2", "action": "create_product", "executed": False, "outcome": {"success": None}}]}
        result = build_cycle_history(snapshot, limit=2)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["cycles"][0]["cycle_id"], "2")
        self.assertEqual(result["count"], 2)

    def test_missing_history_fails_closed(self):
        result = build_cycle_history({"state": {}})
        self.assertEqual(result["status"], "DEGRADED")
        self.assertEqual(result["cycles"], [])

    def test_limit_is_bounded(self):
        with self.assertRaises(ValueError):
            build_cycle_history({"history": []}, 51)


if __name__ == "__main__":
    unittest.main()
