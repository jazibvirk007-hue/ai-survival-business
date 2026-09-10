import os
import tempfile
import unittest

from cortex_learning import CortexLearning
from cortex_memory import CortexMemory


class LearningTests(unittest.TestCase):
    def test_records_decision_and_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = CortexMemory(os.path.join(directory, "memory.json"))
            learning = CortexLearning(memory)
            decision = learning.record_decision("research_market", "Demand data is stale", 90, False)
            outcome = learning.record_outcome("research_market", "Observed a fresh market snapshot", True)
            self.assertEqual(decision["kind"], "decision")
            self.assertEqual(outcome["kind"], "outcome")
            self.assertEqual(len(learning.context()), 2)

    def test_context_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            learning = CortexLearning(CortexMemory(os.path.join(directory, "memory.json")))
            for index in range(5):
                learning.record_outcome("test", f"result-{index}", True)
            self.assertEqual(len(learning.context(2)), 2)

    def test_invalid_inputs_rejected(self):
        learning = CortexLearning(CortexMemory(os.path.join(tempfile.gettempdir(), "unused-cortex-memory.json")))
        with self.assertRaises(ValueError):
            learning.record_decision("", "reason", 1, False)
        with self.assertRaises(ValueError):
            learning.record_outcome("action", "", True)
        with self.assertRaises(TypeError):
            learning.record_outcome("action", "result", "yes")


if __name__ == "__main__":
    unittest.main()
