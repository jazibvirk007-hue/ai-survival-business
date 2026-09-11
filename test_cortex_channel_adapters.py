import unittest

from cortex_channel_adapters import (
    GmailChannelAdapter,
    OutboundEnvelope,
    WhatsAppChannelAdapter,
    channel_status,
)


class ChannelAdapterTests(unittest.TestCase):
    def test_prepare_is_governed_and_does_not_send(self):
        sent = []
        adapter = GmailChannelAdapter(lambda envelope: sent.append(envelope))
        result = adapter.prepare("customer@example.com", "Hello", subject="Cortex", approval_id="A1")
        self.assertTrue(result["prepared"])
        self.assertTrue(result["requires_guard"])
        self.assertEqual(sent, [])

    def test_send_requires_approval(self):
        adapter = WhatsAppChannelAdapter(lambda envelope: "sent")
        envelope = OutboundEnvelope("whatsapp", "+10000000000", "", "Hello")
        result = adapter.send(envelope)
        self.assertFalse(result["executed"])
        self.assertEqual(result["error"], "approval_required")

    def test_send_uses_injected_transport_after_approval(self):
        seen = []
        adapter = GmailChannelAdapter(lambda envelope: seen.append(envelope.recipient) or "provider-id")
        envelope = OutboundEnvelope("gmail", "customer@example.com", "Offer", "Hello", "A2")
        result = adapter.send(envelope)
        self.assertTrue(result["executed"])
        self.assertEqual(result["result"], "provider-id")
        self.assertEqual(seen, ["customer@example.com"])

    def test_status_never_exposes_credentials(self):
        status = channel_status()
        self.assertEqual(set(status["channels"]), {"gmail", "whatsapp"})
        self.assertNotIn("api_key", str(status))
        self.assertNotIn("token", str(status))
        self.assertEqual(status["credential_policy"], "credentials remain outside Cortex channel envelopes")


if __name__ == "__main__":
    unittest.main()
