import unittest

from cortex_acquisition_policy import score_candidate


class AcquisitionPolicyTests(unittest.TestCase):
    def test_missing_source_is_rejected(self):
        result = score_candidate({"need": "automation", "fit": 40, "contactable": True})
        self.assertFalse(result.eligible)
        self.assertEqual(result.next_action, "discard")

    def test_missing_need_never_becomes_a_prospect(self):
        result = score_candidate({"source": "public", "fit": 40, "contactable": True})
        self.assertFalse(result.eligible)
        self.assertEqual(result.next_action, "qualify")

    def test_strong_factual_candidate_is_eligible(self):
        result = score_candidate({"source": "public", "need": "workflow automation", "fit": 40, "contactable": True})
        self.assertTrue(result.eligible)
        self.assertEqual(result.score, 80)
        self.assertEqual(result.next_action, "qualify")

    def test_unknown_contactability_stays_conservative(self):
        result = score_candidate({"source": "public", "need": "workflow automation", "fit": 40})
        self.assertFalse(result.eligible)
        self.assertEqual(result.next_action, "research_more")

    def test_score_is_bounded(self):
        result = score_candidate({"source": "public", "need": "x", "fit": 9999, "contactable": True})
        self.assertEqual(result.score, 100)


if __name__ == "__main__":
    unittest.main()
