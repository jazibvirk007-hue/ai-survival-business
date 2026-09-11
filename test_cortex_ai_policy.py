import unittest

from cortex_ai_policy import advisory_prompt, validate_advisory


class CortexAIPolicyTests(unittest.TestCase):
    def test_accepts_only_candidate_action(self):
        result = validate_advisory({"action": "research_market", "score": 88, "reason": "fresh research"}, ["research_market", "rest_and_observe"])
        self.assertTrue(result.accepted)
        self.assertEqual(result.action, "research_market")
        self.assertEqual(result.score, 88)

    def test_rejects_invented_action(self):
        result = validate_advisory({"action": "transfer_money", "score": 100}, ["review_financials"])
        self.assertFalse(result.accepted)

    def test_score_is_bounded(self):
        result = validate_advisory({"action": "rest_and_observe", "score": 999}, ["rest_and_observe"])
        self.assertEqual(result.score, 100)

    def test_prompt_contains_deterministic_candidates(self):
        prompt = advisory_prompt([{"action": "find_prospects", "priority": 72, "reason": "growth opportunity"}])
        self.assertIn("find_prospects", prompt)
        self.assertIn("Do not invent an action", prompt)


if __name__ == "__main__":
    unittest.main()
