from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cortex_outcome_ledger import CortexOutcomeLedger


class TestCortexOutcomeLedger(unittest.TestCase):
    def test_records_are_bounded_and_not_revenue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = CortexOutcomeLedger(str(Path(directory) / "outcomes.json"))
            item = ledger.record(cycle_id="V19-TEST", action="research_market", success=True, outcome={"success": True}, verified=True)
            self.assertEqual(item["cycle_id"], "V19-TEST")
            self.assertEqual(len(ledger.recent()), 1)
            self.assertEqual(ledger.status()["revenue_policy"], "never_derived_from_outcomes")


if __name__ == "__main__":
    unittest.main()
