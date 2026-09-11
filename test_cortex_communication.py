import os
import tempfile
import unittest

from cortex_communication import CortexCommunicationError, communication_status, record_message, recent_messages


class CortexCommunicationTests(unittest.TestCase):
    def test_records_and_returns_newest_first(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "events.json")
            first = record_message("Research", "Product", "handoff", "Demand signal ready", path=path)
            second = record_message("Product", "CEO", "report", "Product draft ready", path=path)
            messages = recent_messages(path=path)
            self.assertEqual(messages[0]["id"], second["id"])
            self.assertEqual(messages[1]["id"], first["id"])
            self.assertEqual(messages[0]["sender"], "Product")

    def test_metadata_is_bounded_and_scalar_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "events.json")
            event = record_message(
                "A", "B", "task", "hello",
                metadata={"ok": True, "number": 3, "nested": {"secret": "no"}, "long": "x" * 1000},
                path=path,
            )
            self.assertEqual(event["metadata"]["ok"], True)
            self.assertNotIn("nested", event["metadata"])
            self.assertEqual(len(event["metadata"]["long"]), 500)

    def test_invalid_store_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "events.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("not-json")
            with self.assertRaises(CortexCommunicationError):
                communication_status(path)

    def test_limit_is_bounded(self):
        with self.assertRaises(ValueError):
            recent_messages(0, "/tmp/nonexistent-cortex-events.json")


if __name__ == "__main__":
    unittest.main()
