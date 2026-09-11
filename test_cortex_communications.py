import unittest

from cortex_communications import CommunicationPolicy, CortexCommunications


class TestCortexCommunications(unittest.TestCase):
    def test_channels_default_to_disabled(self):
        comms = CortexCommunications()
        status = comms.status()
        self.assertEqual(status["supported_channels"], ["gmail", "whatsapp"])
        self.assertFalse(status["policies"][0]["allow_outbound"])
        self.assertFalse(status["credentials_exposed_to_ai"])

    def test_draft_requires_enabled_outbound_policy(self):
        comms = CortexCommunications([
            CommunicationPolicy(
                channel="gmail",
                mode="approved_send",
                require_approval=True,
                allow_outbound=True,
                daily_send_limit=25,
            )
        ])
        draft = comms.prepare_draft("gmail", "customer:123", "Thanks for your message.", "Customer support follow-up")
        self.assertTrue(draft.requires_approval)

    def test_disabled_channel_rejects_outbound(self):
        comms = CortexCommunications()
        with self.assertRaises(PermissionError):
            comms.prepare_draft("whatsapp", "customer:123", "Hello", "Follow-up")

    def test_invalid_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            CommunicationPolicy("gmail", mode="approved_send", require_approval=False)

    def test_autonomous_mode_must_still_be_guarded(self):
        with self.assertRaises(ValueError):
            CommunicationPolicy("whatsapp", mode="autonomous_guarded", require_approval=True, allow_outbound=True)

    def test_draft_is_bounded(self):
        comms = CortexCommunications([
            CommunicationPolicy("gmail", mode="approved_send", require_approval=True, allow_outbound=True, daily_send_limit=10)
        ])
        with self.assertRaises(ValueError):
            comms.prepare_draft("gmail", "customer:1", "x" * 10001, "reason")


if __name__ == "__main__":
    unittest.main()
