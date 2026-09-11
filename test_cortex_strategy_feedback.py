import tempfile
import unittest

from cortex_deep_memory import CortexDeepMemory
from cortex_memory import CortexMemory
from cortex_strategy_feedback import CortexStrategyFeedback, enrich_ceo_state


class StrategyFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        memory = CortexMemory(self.tmp.name)
        memory.remember("decision", "find_prospects: test", {"priority": 80})
        memory.remember("outcome", "find_prospects: success", {"success": True})
        memory.remember("outcome", "find_prospects: success", {"success": True})
        self.feedback = CortexStrategyFeedback(CortexDeepMemory(memory))

    def test_build_produces_favor_signal(self):
        result = self.feedback.build()
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["recommendations"][0]["signal"], "favor")

    def test_enrich_does_not_mutate_original(self):
        state = {"products_available": 1}
        enriched = enrich_ceo_state(state, self.feedback)
        self.assertNotIn("memory_strategy", state)
        self.assertIn("memory_strategy", enriched)

    def test_context_is_bounded(self):
        with self.assertRaises(ValueError):
            self.feedback.build(11)


if __name__ == "__main__":
    unittest.main()
