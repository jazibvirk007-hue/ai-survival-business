import tempfile
import unittest

from cortex_deep_memory import CortexDeepMemory
from cortex_memory import CortexMemory


class DeepMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.memory = CortexMemory(self.tmp.name)
        self.deep = CortexDeepMemory(self.memory)

    def test_empty_memory_waits_for_observations(self):
        snapshot = self.deep.analyze()
        self.assertEqual(snapshot["status"], "WAITING_FOR_OBSERVATIONS")
        self.assertEqual(snapshot["observed_outcomes"], 0)

    def test_success_rate_uses_observed_outcomes_only(self):
        self.memory.remember("decision", "research_market: stale research", {"priority": 80})
        self.memory.remember("outcome", "research_market: completed", {"success": True})
        self.memory.remember("outcome", "research_market: failed", {"success": False})
        self.memory.remember("decision", "create_product: new opportunity", {"priority": 70})
        snapshot = self.deep.analyze()
        row = next(item for item in snapshot["actions"] if item["action"] == "research_market")
        self.assertEqual(row["observed_outcomes"], 2)
        self.assertEqual(row["success_rate"], 0.5)
        self.assertEqual(snapshot["successes"], 1)
        self.assertEqual(snapshot["failures"], 1)

    def test_execution_authority_is_none(self):
        snapshot = self.deep.analyze()
        self.assertEqual(snapshot["execution_authority"], "none")

    def test_limit_is_bounded(self):
        with self.assertRaises(ValueError):
            self.deep.analyze(0)
        with self.assertRaises(ValueError):
            self.deep.analyze(201)


if __name__ == "__main__":
    unittest.main()
