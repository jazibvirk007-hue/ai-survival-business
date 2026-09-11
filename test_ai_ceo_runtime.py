import json
import unittest

from ai_ceo import AICEO
from cortex_ai_runtime import AISelection


class FakeRuntime:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def generate(self, selection, messages, *, temperature=0.2):
        self.calls += 1
        return self.text

    def status(self, selection):
        return {"configured": True, "provider_id": selection.provider_id, "model": selection.model}


class AICEOAIAdvisoryTests(unittest.TestCase):
    def state(self):
        return {
            "market_researched": True,
            "products_available": 1,
            "qualified_prospects": 2,
            "outreach_drafts": 0,
            "approved_outreach": 0,
            "pending_orders": 1,
            "verified_revenue": 100,
            "cash": 100,
        }

    def test_ai_can_rank_only_existing_candidates(self):
        runtime = FakeRuntime(json.dumps({"ranking": [
            {"action": "review_financials", "score": 100},
            {"action": "qualify_prospects", "score": 1},
        ]}))
        ceo = AICEO(ai_runtime=runtime, ai_selection=AISelection("local_ollama", "local-model"), ai_enabled=True)
        decision = ceo.decide(self.state())
        self.assertEqual(decision.action, "review_financials")
        self.assertEqual(runtime.calls, 1)

    def test_ai_cannot_invent_an_action(self):
        runtime = FakeRuntime(json.dumps({"ranking": [
            {"action": "send_money_to_me", "score": 100},
            {"action": "qualify_prospects", "score": 1},
        ]}))
        ceo = AICEO(ai_runtime=runtime, ai_selection=AISelection("local_ollama", "local-model"), ai_enabled=True)
        candidates = ceo.evaluate(self.state())
        self.assertIn(candidates[0].action, {"qualify_prospects", "review_financials"})
        self.assertNotEqual(candidates[0].action, "send_money_to_me")

    def test_malformed_ai_output_falls_back_to_deterministic_ranking(self):
        runtime = FakeRuntime("not-json")
        ceo = AICEO(ai_runtime=runtime, ai_selection=AISelection("local_ollama", "local-model"), ai_enabled=True)
        expected = AICEO().decide(self.state()).action
        decision = ceo.decide(self.state())
        self.assertEqual(decision.action, expected)
        self.assertEqual(runtime.calls, 1)

    def test_ai_disabled_does_not_call_runtime(self):
        runtime = FakeRuntime("{}")
        ceo = AICEO(ai_runtime=runtime, ai_selection=AISelection("local_ollama", "local-model"), ai_enabled=False)
        ceo.decide(self.state())
        self.assertEqual(runtime.calls, 0)

    def test_status_exposes_selection_but_no_secret(self):
        runtime = FakeRuntime("{}")
        ceo = AICEO(ai_runtime=runtime, ai_selection=AISelection("local_ollama", "local-model"), ai_enabled=True)
        status = ceo.status()
        self.assertEqual(status["ai_advisory"]["provider_id"], "local_ollama")
        self.assertNotIn("api_key", json.dumps(status).lower())


if __name__ == "__main__":
    unittest.main()