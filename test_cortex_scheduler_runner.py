import unittest
from unittest.mock import Mock

from cortex_scheduler_runner import CortexSchedulerRunner


class RunnerTests(unittest.TestCase):
    def test_run_once_is_decision_only(self):
        scheduler = Mock()
        scheduler.tick.return_value = {"ok": True, "scheduler": {"recovery": "normal"}}
        runner = CortexSchedulerRunner(scheduler, interval_seconds=0.1)
        result = runner.run_once()
        scheduler.tick.assert_called_once_with(execute=False)
        self.assertTrue(result["ok"])

    def test_run_is_bounded(self):
        scheduler = Mock()
        scheduler.tick.return_value = {"ok": True, "scheduler": {"recovery": "normal"}}
        scheduler.snapshot.return_value = {"status": "READY"}
        runner = CortexSchedulerRunner(scheduler, interval_seconds=0.1)
        result = runner.run(max_cycles=3)
        self.assertEqual(result["cycles_completed"], 3)
        self.assertFalse(result["stopped"])
        self.assertEqual(scheduler.tick.call_count, 3)
        for call in scheduler.tick.call_args_list:
            self.assertEqual(call.kwargs, {"execute": False})

    def test_runner_stops_on_scheduler_safety_pause(self):
        scheduler = Mock()
        scheduler.tick.side_effect = [
            {"ok": False, "scheduler": {"recovery": "automatic_safety_pause"}},
        ]
        scheduler.snapshot.return_value = {"status": "PAUSED"}
        runner = CortexSchedulerRunner(scheduler, interval_seconds=0.1)
        result = runner.run(max_cycles=10)
        self.assertEqual(result["cycles_completed"], 1)
        self.assertEqual(scheduler.tick.call_count, 1)

    def test_invalid_bounds_are_rejected(self):
        scheduler = Mock()
        with self.assertRaises(ValueError):
            CortexSchedulerRunner(scheduler, interval_seconds=0)
        runner = CortexSchedulerRunner(scheduler, interval_seconds=0.1)
        with self.assertRaises(ValueError):
            runner.run(max_cycles=0)
        with self.assertRaises(ValueError):
            runner.run(max_cycles=1001)


if __name__ == "__main__":
    unittest.main()
