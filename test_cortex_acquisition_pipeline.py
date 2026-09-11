import unittest

from cortex_acquisition_pipeline import CortexAcquisitionPipeline


class AcquisitionPipelineTests(unittest.TestCase):
    def setUp(self):
        self.pipeline = CortexAcquisitionPipeline()

    def test_strong_authorized_candidate_is_eligible(self):
        result = self.pipeline.plan([{
            "name": "Example Business",
            "source": "authorized_test_source",
            "problem_signal": "needs workflow automation",
            "fit_score": 90,
            "intent_score": 85,
            "contactability": 80,
            "consent_or_basis": "public_business_contact",
        }])
        self.assertTrue(result["success"])
        self.assertEqual(result["eligible_count"], 1)
        self.assertEqual(result["candidates"][0]["name"], "Example Business")
        self.assertTrue(result["candidates"][0]["requires_guard"])

    def test_missing_need_is_not_promoted(self):
        result = self.pipeline.plan([{
            "name": "Example Business",
            "source": "authorized_test_source",
            "fit_score": 90,
            "intent_score": 85,
            "contactability": 80,
            "consent_or_basis": "public_business_contact",
        }])
        self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(result["reviewed"][0]["next_action"], "qualify")

    def test_weak_contactability_stays_out_of_outbound_queue(self):
        result = self.pipeline.plan([{
            "name": "Example Business",
            "source": "authorized_test_source",
            "problem_signal": "needs workflow automation",
            "fit_score": 90,
            "intent_score": 85,
            "contactability": 20,
            "consent_or_basis": "public_business_contact",
        }])
        self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(result["reviewed"][0]["next_action"], "research_more")

    def test_missing_authorization_basis_stays_out_of_outbound_queue(self):
        result = self.pipeline.plan([{
            "name": "Example Business",
            "source": "authorized_test_source",
            "problem_signal": "needs workflow automation",
            "fit_score": 90,
            "intent_score": 85,
            "contactability": 90,
            "consent_or_basis": "",
        }])
        self.assertEqual(result["eligible_count"], 0)

    def test_malformed_record_fails_closed(self):
        with self.assertRaises(ValueError):
            self.pipeline.plan(["not-a-record"])

    def test_record_limit_is_bounded(self):
        records = [{
            "name": str(i),
            "source": "authorized_test_source",
            "problem_signal": "need",
            "fit_score": 1,
        } for i in range(51)]
        with self.assertRaises(ValueError):
            self.pipeline.plan(records)

    def test_result_limit_is_bounded(self):
        with self.assertRaises(ValueError):
            self.pipeline.plan([], limit=21)


if __name__ == "__main__":
    unittest.main()
