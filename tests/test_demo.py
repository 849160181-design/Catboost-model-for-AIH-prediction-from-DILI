"""End-to-end check of the five-minute demo."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "quickstart" / "run_demo.py"


class DemoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.proc = subprocess.run(
            [sys.executable, str(DEMO), "--outdir", str(cls.out), "--quiet"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        cls.table_path = cls.out / "performance_demo.csv"
        cls.rows = []
        if cls.table_path.exists():
            with cls.table_path.open(newline="", encoding="utf-8") as handle:
                cls.rows = list(csv.DictReader(handle))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_exit_code(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)

    def test_table_has_three_cohorts(self):
        self.assertEqual([r["cohort"] for r in self.rows], ["train", "internal_test", "external_test"])

    def test_aucs_are_in_valid_range(self):
        for row in self.rows:
            self.assertGreaterEqual(float(row["auc"]), 0.80)
            self.assertLessEqual(float(row["auc"]), 0.99)

    def test_ci_brackets_auc(self):
        for row in self.rows:
            self.assertLessEqual(float(row["ci_lower"]), float(row["auc"]))
            self.assertGreaterEqual(float(row["ci_upper"]), float(row["auc"]))

    def test_predictions_cover_every_row(self):
        with (self.out / "predictions_demo.csv").open(newline="", encoding="utf-8") as handle:
            predictions = list(csv.DictReader(handle))
        self.assertEqual(len(predictions), 180)
        self.assertEqual(len({r["sample_id"] for r in predictions}), 180)

    def test_markdown_warns_that_data_are_synthetic(self):
        text = (self.out / "performance_demo.md").read_text(encoding="utf-8")
        self.assertIn("SYNTHETIC DEMO", text)
        self.assertIn("NOT PATIENT DATA", text)
        self.assertIn("NOT FOR DIAGNOSIS", text)


if __name__ == "__main__":
    unittest.main()
