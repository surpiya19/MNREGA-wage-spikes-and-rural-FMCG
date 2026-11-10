"""Run with python -m unittest discover -s tests -v."""
import unittest
import csv
from pathlib import Path
import pandas as pd
import config as C
from quality_core import classification_metrics, market_consensus


class QualityTests(unittest.TestCase):
    def test_misaligned_predictions_fail(self):
        with self.assertRaises(ValueError):
            classification_metrics(["Steady", "Slowing"], ["Steady"])

    def test_three_month_delay_at_month_and_leap_boundaries(self):
        self.assertEqual(C.last_usable_month(pd.Timestamp("2024-05-30"), 3), pd.Timestamp("2024-02-29"))
        self.assertEqual(C.last_usable_month(pd.Timestamp("2026-07-07"), 3), pd.Timestamp("2026-03-31"))

    def test_restored_dates_match_both_source_readers(self):
        root = Path(__file__).resolve().parents[1]
        for company in ("Marico", "Emami"):
            def rows(path):
                with path.open(encoding="utf-8") as stream:
                    return {r["quarter"]: r for r in csv.DictReader(stream)}
            evidence = rows(root / "data/raw" / f"evidence_{company}.csv")
            readers = [rows(root / "labels" / company.lower() / f"labels_{x}.csv") for x in ("A", "B")]
            for q, row in evidence.items():
                self.assertTrue(row["results_date"])
                self.assertEqual(row["results_date"], readers[0][q]["results_date"])
                self.assertEqual(row["results_date"], readers[1][q]["results_date"])

    def test_abstentions_do_not_count_as_misses(self):
        result = classification_metrics(["Steady", "Insufficient", "Slowing"], ["Steady", "Steady", None])
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["accuracy"], 1)

    def test_steady_accuracy_does_not_hide_missed_turns(self):
        result = classification_metrics(["Steady"] * 8 + ["Accelerating", "Slowing"], ["Steady"] * 10)
        self.assertEqual(result["accuracy"], .8)
        self.assertAlmostEqual(result["balanced_accuracy"], 1 / 3)
        self.assertEqual(result["details"][0]["recall"], 0)

    def test_absent_classes_are_undefined(self):
        result = classification_metrics(["Steady"], ["Steady"])
        self.assertEqual(result["classes_present"], 1)
        self.assertIsNone(result["details"][0]["recall"])

    def test_consensus_ties_are_insufficient(self):
        self.assertEqual(market_consensus(["Accelerating", "Slowing"]), ("Insufficient", "no consensus (tie)"))
        self.assertEqual(market_consensus(["Accelerating", "Steady"])[0], "Insufficient")

    def test_consensus_ties_steady_option(self):
        self.assertEqual(market_consensus(["Accelerating", "Slowing"], tie="Steady")[0], "Steady")
        self.assertEqual(market_consensus(["Accelerating", "Steady"], tie="Steady")[0], "Steady")

    def test_consensus_missing_and_confidence(self):
        self.assertEqual(market_consensus(["Insufficient", ""]), ("Insufficient", ""))
        self.assertEqual(market_consensus(["Accelerating"] * 3 + ["Steady"]), ("Accelerating", "high"))


if __name__ == "__main__":
    unittest.main()
