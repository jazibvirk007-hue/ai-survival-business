import json
import unittest

from cortex_ai_advisor import CortexAIAdvisor
from cortex_ai_runtime import AISelection, CortexAIRuntime


class FakeRuntime(CortexAIRuntime):
    def __init__(self, response):
        self.response = response
        self.timeout_seconds = 30.0

    def generate(self, selection, messages, *, temperature=0.2):
        return self.response

    def status(self, selection):
        return {"provider_id": selection.provider_id, "model": selection.model, "configured": True, "credential_env": "SECRET_ENV"}


class CortexAIAdvisorTests(unittest.TestCase):
    def test_accepts_only_deterministic_candidate(self):
        runtime = FakeRuntime(json.dumps({"action": "find_prospects", "score": 91, "reason": "growth"}))
        advisor = CortexAIAdvisor(runtime, AISelection("local_ollama", "test-model"))
        result = advisor.advise([
            {"action": "find_prospects", "priority": 70, "reason": "growth"},
            {"action": "rest_and_observe", "priority": 20, "reason": "wait"},
        ])
        self.assertTrue(result.accepted)
        self.assertEqual(result.action, "find_prospects")
        self.assertEqual(result.score, 91)

    def test_rejects_invented_action(self):
        runtime = FakeRuntime(json.dumps({"action": "transfer_money", "score": 100}))
        advisor = CortexAIAdvisor(runtime, AISelection("local_ollama", "test-model"))
        result = advisor.advise([{ "action": "review_financials", "priority": 75, "reason": "pending" }])
        self.assertFalse(result.accepted)

    def test_provider_failure_fails_closed(self):
        runtime = FakeRuntime("not-json")
        advisor = CortexAIAdvisor(runtime, AISelection("local_ollama", "test-model"))
        result = advisor.advise([{ "action": "rest_and_observe", "priority": 20, "reason": "wait" }])
        self.assertFalse(result.accepted)
        self.assertEqual(result.score, 0)

    def test_safe_status_does_not_expose_credential_env(self):
        runtime = FakeRuntime("{}")
        advisor = CortexAIAdvisor(runtime, AISelection("local_ollama", "test-model"))
        status = advisor.safe_status()
        self.assertNotIn("credential_env", status)
        self.assertNotIn("SECRET_ENV", json.dumps(status))


if __name__ == "__main__":
    unittest.main()
