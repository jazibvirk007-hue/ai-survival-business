import unittest

from cortex_v9_specialists import CortexV9Specialists


class V9AcquisitionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.specialists = CortexV9Specialists()

    def test_find_prospects_uses_governed_acquisition_queue(self):
        state = {
            "prospects": [{
                "name": "Automation Buyer",
                "source": "authorized_test_source",
                "problem_signal": "needs workflow automation",
                "fit_score": 90,
                "intent_score": 90,
                "contactability": 90,
                "consent_or_basis": "public_business_contact",
            }]
        }
        result = self.specialists._find_prospects(state)
        self.assertTrue(result["success"])
        self.assertEqual(result["eligible_count"], 1)
        self.assertEqual(len(result["acquisition_queue"]), 1)
        self.assertTrue(result["acquisition_queue"][0]["requires_guard"])
        self.assertEqual(result["state_patch"]["qualified_prospects"], 1)

    def test_find_prospects_rejects_malformed_records_without_inventing(self):
        state = {"prospects": [{"name": "Missing source"}]}
        result = self.specialists._find_prospects(state)
        self.assertFalse(result["success"])
        self.assertEqual(result["state_patch"]["qualified_prospects"], 0)

    def test_find_prospects_requires_authorization_basis_for_queue(self):
        state = {
            "prospects": [{
                "name": "Unverified Contact",
                "source": "authorized_test_source",
                "problem_signal": "needs workflow automation",
                "fit_score": 100,
                "intent_score": 100,
                "contactability": 100,
                "consent_or_basis": "",
            }]
        }
        result = self.specialists._find_prospects(state)
        self.assertTrue(result["success"])
        self.assertEqual(result["eligible_count"], 0)


if __name__ == "__main__":
    unittest.main()
