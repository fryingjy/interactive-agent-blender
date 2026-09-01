import json
import unittest
from pathlib import Path

from knowledge_engine.evaluator_regression import evaluate_anchor


ROOT = Path(__file__).resolve().parents[1]


class EvaluatorRegressionTests(unittest.TestCase):
    def test_frozen_real_reference_anchor_passes(self):
        anchor = json.loads(
            (ROOT / "knowledge/foundation/reference_evaluator_regression_anchor.json").read_text(encoding="utf-8")
        )
        result = evaluate_anchor(anchor, root=ROOT)
        self.assertTrue(result["pass"])
        self.assertEqual(result["target_count"], 3)

    def test_anchor_requires_three_target_families(self):
        with self.assertRaisesRegex(ValueError, "at least three cases"):
            evaluate_anchor({"cases": []}, root=ROOT)


if __name__ == "__main__":
    unittest.main()
