"""Parity between the pure-Python scorer and CatBoost-generated probabilities."""

from __future__ import annotations

import csv
import importlib.util
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "model" / "catboost_model_pure.py"
FIXTURE = ROOT / "tests" / "fixtures" / "model_expected.csv"


def load_model():
    spec = importlib.util.spec_from_file_location("catboost_model_pure", MODEL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModelParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_model()
        with FIXTURE.open(newline="", encoding="utf-8") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_fixture_is_nonempty(self):
        self.assertEqual(len(self.rows), 48)

    def test_probabilities_match_catboost(self):
        for row in self.rows:
            got = self.model.predict_proba(row["PAS_Macrophages"], row["MUM1"])
            expected = float(row["expected_probability"])
            self.assertAlmostEqual(
                got,
                expected,
                delta=1e-6,
                msg=f"PAS={row['PAS_Macrophages']} MUM1={row['MUM1']}",
            )

    def test_probabilities_are_in_unit_interval(self):
        for pas in (0, 1, 2):
            for mum1 in (1, 10, 50, 100, 200, 700):
                value = self.model.predict_proba(pas, mum1)
                self.assertGreater(value, 0.0)
                self.assertLess(value, 1.0)
                self.assertTrue(math.isfinite(value))

    def test_invalid_category_is_rejected(self):
        with self.assertRaises(ValueError):
            self.model.predict_proba(3, 100)

    def test_missing_mum1_is_rejected(self):
        with self.assertRaises((ValueError, TypeError)):
            self.model.predict_proba(1, None)


if __name__ == "__main__":
    unittest.main()
