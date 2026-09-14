import unittest
from yt_autopilot.core import (
    Asset, RightsRecord, RightsStatus, TopicScore,
    originality_score, reused_content_risk, rights_gate,
)
from yt_autopilot.state_machine import Pipeline
from yt_autopilot.core import PipelineState


class CoreTests(unittest.TestCase):
    def asset(self, status=RightsStatus.VERIFIED_REUSABLE, evidence=("https://example.test/license",)):
        rights = RightsRecord(
            source_url="https://example.test/a",
            source_name="Test Archive",
            license="Public Domain",
            commercial_use_allowed=True,
            modification_allowed=True,
            verification_status=status,
            evidence=evidence,
        )
        return Asset("https://example.test/a", "Test Archive", rights)

    def test_rights_gate_accepts_verified_assets_with_evidence(self):
        self.assertEqual(rights_gate([self.asset()]), (True, []))

    def test_rights_gate_rejects_unknown_assets(self):
        ok, failures = rights_gate([self.asset(RightsStatus.UNKNOWN)])
        self.assertFalse(ok)
        self.assertTrue(failures)

    def test_rights_gate_rejects_missing_evidence(self):
        ok, failures = rights_gate([self.asset(evidence=())])
        self.assertFalse(ok)
        self.assertIn("rights evidence is missing", failures[0])

    def test_topic_score_bounds_and_footage_weight(self):
        score = TopicScore(90, 80, 20, 80, 60, 90, 100, 20, 70).final()
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_originality_and_risk_move_in_expected_direction(self):
        high = originality_score(100, 100, 100, 80, 100)
        low_risk = reused_content_risk(10, 100, 100, 100, 100, 100)
        self.assertEqual(high, 98.0)
        self.assertLess(low_risk, 20)

    def test_state_machine_is_fail_closed(self):
        p = Pipeline()
        p.transition(PipelineState.RESEARCH)
        with self.assertRaises(ValueError):
            p.transition(PipelineState.PUBLISHED)


if __name__ == "__main__":
    unittest.main()
