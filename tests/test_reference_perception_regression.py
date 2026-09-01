import unittest

from tools.evaluate_reference_perception_regression import evaluate


class ReferencePerceptionRegressionTests(unittest.TestCase):
    def test_each_rule_is_strict_and_cannot_be_averaged(self):
        anchor = {
            "record_type": "REFERENCE_PERCEPTION_REGRESSION_ANCHOR",
            "frozen_at": "test",
            "rules": [
                {"id": "a", "path": "metrics.a", "operator": "min", "threshold": 0.9},
                {"id": "b", "path": "metrics.b", "operator": "max", "threshold": 0.2},
            ],
        }
        self.assertTrue(evaluate(anchor, {"record_type": "REFERENCE_PERCEPTION_VALIDATION_LAB", "metrics": {"a": 0.9, "b": 0.2}})["pass"])
        result = evaluate(anchor, {"record_type": "REFERENCE_PERCEPTION_VALIDATION_LAB", "metrics": {"a": 1.0, "b": 0.21}})
        self.assertFalse(result["pass"])
        self.assertTrue(result["results"][0]["pass"])
        self.assertFalse(result["results"][1]["pass"])


if __name__ == "__main__":
    unittest.main()
