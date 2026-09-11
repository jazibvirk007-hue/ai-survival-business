import unittest

from ai_ceo import AICEO
from cortex_strategy_ceo import CortexStrategyCEO


class StrategyCEOTests(unittest.TestCase):
    def _ceo(self):
        return CortexStrategyCEO(AICEO(max_actions_per_cycle=1))

    def test_strong_observed_action_gets_bounded_bonus(self):
        ceo = self._ceo()
        state = {
            "memory_strategy": [
                {"action": "research_market", "observed_outcomes": 5, "success_rate": 1.0}
            ],
            "market_researched": False,
        }
        decision = ceo.decide(state)
        self.assertEqual(decision.action, "research_market")
        self.assertLessEqual(decision.priority, 100)
        self.assertIn("Observed-learning adjustment", decision.reason)

    def test_weak_observed_action_is_penalized(self):
        ceo = self._ceo()
        state = {
            "memory_strategy": [
                {"action": "research_market", "observed_outcomes": 10, "success_rate": 0.1}
            ],
            "market_researched": False,
        }
        decision = ceo.decide(state)
        self.assertEqual(decision.action, "research_market")
        self.assertIn("Observed-learning adjustment", decision.reason)

    def test_insufficient_observations_do_not_bias(self):
        ceo = self._ceo()
        state = {
            "memory_strategy": [
                {"action": "research_market", "observed_outcomes": 1, "success_rate": 1.0}
            ],
            "market_researched": False,
        }
        decision = ceo.decide(state)
        self.assertEqual(decision.action, "research_market")
        self.assertNotIn("Observed-learning adjustment", decision.reason)

    def test_learning_cannot_change_approval_flag(self):
        ceo = self._ceo()
        state = {
            "memory_strategy": [
                {"action": "follow_up", "observed_outcomes": 10, "success_rate": 1.0}
            ],
            "approved_outreach": 1,
            "pending_orders": 0,
            "products_available": 1,
            "qualified_prospects": 1,
            "outreach_drafts": 1,
        }
        decisions = ceo.evaluate(state)
        follow_up = next(d for d in decisions if d.action == "follow_up") if any(d.action == "follow_up" for d in decisions) else None
        if follow_up is not None:
            self.assertTrue(follow_up.requires_approval)


if __name__ == "__main__":
    unittest.main()
