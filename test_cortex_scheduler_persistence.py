import os
import tempfile
import unittest

from cortex_scheduler_persistence import load_scheduler_state, save_scheduler_state


class SchedulerPersistenceTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "state.json")
            state = {"consecutive_failures": 2, "paused": False, "last_run": "2026-09-11T12:00:00+00:00"}
            save_scheduler_state(state, path)
            self.assertEqual(load_scheduler_state(path), state)

    def test_missing_state_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_scheduler_state(os.path.join(directory, "missing.json")), {})

    def test_corrupt_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "state.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("not-json")
            with self.assertRaises(ValueError):
                load_scheduler_state(path)

    def test_oversized_text_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                save_scheduler_state({"note": "x" * 501}, os.path.join(directory, "state.json"))


if __name__ == "__main__":
    unittest.main()
