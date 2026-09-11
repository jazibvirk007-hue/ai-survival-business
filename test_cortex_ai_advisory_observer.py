import unittest

from cortex_ai_advisor import CortexAIAdvisor
from cortex_ai_advisory_observer import CortexAIAdvisoryObserver
from cortex_ai_runtime import AISelection, CortexAIRuntime


class FakeRuntime(CortexAIRuntime):
    def __init__(self):
        self.timeout_seconds = 30.0

    def generate(self, selection, messages, *, temperature=0.2):
        return '{"action":"find_prospects","score":90,"reason":"growth"}'

    def status(self, selection):
        return {"configured": True}


class ObserverTests(unittest.TestCase):
    def test_records_bounded_advisory(self):
        advisor = CortexAIAdvisor(FakeRuntime(), AISelection("local_ollama", "test-model"))
        observer = CortexAIAdvisoryObserver(advisor, communication_path="/tmp/cortex-test-communications.json")
        result = observer.evaluate([{"action": "find_prospects", "priority": 70, "reason": "growth"}])
        self.assertTrue(result["accepted"])
        self.assertEqual(result["action"], "find_prospects")
        self.assertEqual(result["score"], 90)
        self.assertIn("correlation_id", result)


if __name__ == "__main__":
    unittest.main()
