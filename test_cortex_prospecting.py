import unittest

from cortex_prospecting import CortexProspecting, Prospect


class CortexProspectingTests(unittest.TestCase):
    def test_discover_and_rank(self):
        prospects = CortexProspecting.discover([
            {
                "name": "Acme Support Team",
                "source": "authorized_business_directory",
                "problem_signal": "slow customer support",
                "fit_score": 90,
                "intent_score": 80,
                "contactability": 70,
            },
            {
                "name": "Low Intent Lead",
                "source": "customer_request_feed",
                "problem_signal": "general interest",
                "fit_score": 40,
                "intent_score": 20,
                "contactability": 90,
            },
        ])
        ranked = CortexProspecting.rank(prospects)
        self.assertEqual(ranked[0]["name"], "Acme Support Team")
        self.assertGreater(ranked[0]["priority_score"], ranked[1]["priority_score"])

    def test_high_score_requires_guard(self):
        prospect = Prospect("A", "source", "need", 100, 100, 100)
        action = CortexProspecting.next_actions(CortexProspecting.rank([prospect]))[0]
        self.assertEqual(action["action"], "prepare_personalized_outreach")
        self.assertTrue(action["requires_approval"])

    def test_invalid_score_rejected(self):
        with self.assertRaises(ValueError):
            Prospect("A", "source", "need", 101)

    def test_invalid_records_rejected(self):
        with self.assertRaises(ValueError):
            CortexProspecting.discover(["not-a-record"])


if __name__ == "__main__":
    unittest.main()
