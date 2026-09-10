import json
import os
import tempfile
import unittest

from cortex_guard import CortexGuard


class CortexGuardTests(unittest.TestCase):
    def make_guard(self, ttl=3600):
        self.directory = tempfile.TemporaryDirectory()
        return CortexGuard(os.path.join(self.directory.name, "approvals.json"), approval_ttl_seconds=ttl)

    def tearDown(self):
        if hasattr(self, "directory"):
            self.directory.cleanup()

    def test_request_approve_consume_once(self):
        guard = self.make_guard()
        request = guard.request("follow_up", "customer asked for details", 72)
        approved = guard.approve(request["id"])
        self.assertEqual(approved["status"], "approved")
        consumed = guard.consume(request["id"], "follow_up")
        self.assertEqual(consumed["status"], "consumed")
        with self.assertRaises(ValueError):
            guard.consume(request["id"], "follow_up")

    def test_action_mismatch_is_rejected(self):
        guard = self.make_guard()
        request = guard.request("follow_up", "reason")
        guard.approve(request["id"])
        with self.assertRaises(ValueError):
            guard.consume(request["id"], "move_money")

    def test_reject_prevents_execution(self):
        guard = self.make_guard()
        request = guard.request("follow_up", "reason")
        guard.reject(request["id"])
        with self.assertRaises(ValueError):
            guard.consume(request["id"], "follow_up")

    def test_expired_request_cannot_be_approved(self):
        guard = self.make_guard(ttl=1)
        request = guard.request("follow_up", "reason")
        import cortex_guard
        original_time = cortex_guard.time.time
        cortex_guard.time.time = lambda: request["expires_at"]
        try:
            with self.assertRaises(ValueError):
                guard.approve(request["id"])
        finally:
            cortex_guard.time.time = original_time

    def test_corrupt_store_fails_closed(self):
        guard = self.make_guard()
        with open(guard.path, "w", encoding="utf-8") as handle:
            json.dump({"unexpected": True}, handle)
        with self.assertRaises(ValueError):
            guard.pending()

    def test_bounded_queue(self):
        self.directory = tempfile.TemporaryDirectory()
        guard = CortexGuard(os.path.join(self.directory.name, "approvals.json"), max_entries=2)
        guard.request("a", "one")
        guard.request("b", "two")
        guard.request("c", "three")
        self.assertEqual(len(guard._load()), 2)
        self.assertEqual(guard._load()[-1]["action"], "c")


if __name__ == "__main__":
    unittest.main()
