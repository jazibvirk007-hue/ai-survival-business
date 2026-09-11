import unittest

from ai_ceo import Decision
from cortex_learned_priority import apply_learned_priorities, learned_priority_adjustment


class LearnedPriorityTests(unittest.TestCase):
    def test_insufficient_observations_are_neutral(self):
        self.assertEqual(learned_priority_adjustment("find_prospects", [{"action": "find_prospects", "successes": 1, "failures": 0}]), 0.0)

    def test_successful_action_gets_bounded_boost(self):
        observations = [{"action": "find_prospects", "successes": 4, "failures": 0}]
        self.assertEqual(learned_priority_adjustment("find_prospects", observations), 10.0)

    def test_failed_action_gets_bounded_penalty(self):
        observations = [{"action": "find_prospects", "successes": 0, "failures": 4}]
        self.assertEqual(learned_priority_adjustment("find_prospects", observations), -10.0)

    def test_apply_preserves_approval_policy(self):
        candidates = [Decision("follow_up", 70, "x", "y", True)]
        result = apply_learned_priorities(candidates, [{"action": "follow_up", "successes": 4, "failures": 0}])
        self.assertEqual(result[0].priority, 80.0)
        self.assertTrue(result[0].requires_approval)


if __name__ == "__main__":
    unittest.main()
