import unittest

from knowledge_engine.reference_constraints import evaluate_reference_constraints


class ReferenceConstraintTests(unittest.TestCase):
    def setUp(self):
        self.contract = {
            "target_id": "radio_fixture",
            "constraints": [
                {"id": "handle_box", "kind": "box", "target": {"left": 0.1, "top": 0.05, "right": 0.9, "bottom": 0.3}, "tolerance": 0.03, "importance": "high"},
                {"id": "knob_center", "kind": "point", "target": [0.96, 0.55], "tolerance": 0.04, "importance": "high"},
                {"id": "speaker_ratio", "kind": "scalar", "target": 0.58, "tolerance": 0.05, "importance": "medium"},
            ],
        }

    def test_local_fail_blocks_even_when_other_constraints_pass(self):
        report = evaluate_reference_constraints(self.contract, {"observations": {
            "handle_box": {"left": 0.1, "top": 0.05, "right": 0.9, "bottom": 0.3},
            "knob_center": [0.84, 0.55],
            "speaker_ratio": 0.59,
        }})
        self.assertFalse(report["pass"])
        self.assertEqual(report["blocking_constraint_ids"], ["knob_center"])
        self.assertEqual(report["tickets"][0]["constraint_id"], "knob_center")

    def test_missing_high_constraint_blocks_and_is_explicit(self):
        report = evaluate_reference_constraints(self.contract, {"observations": {
            "knob_center": [0.96, 0.55], "speaker_ratio": 0.58,
        }})
        self.assertFalse(report["pass"])
        self.assertEqual(report["missing_constraint_ids"], ["handle_box"])
        self.assertEqual(report["tickets"][0]["status"], "MISSING")

    def test_low_or_medium_failure_is_a_ticket_but_not_a_blocker(self):
        contract = {**self.contract, "constraints": [
            {"id": "outline", "kind": "scalar", "target": 1.0, "tolerance": 0.01, "importance": "high"},
            {"id": "speaker_ratio", "kind": "scalar", "target": 0.58, "tolerance": 0.01, "importance": "medium"},
        ]}
        report = evaluate_reference_constraints(contract, {"observations": {"outline": 1.0, "speaker_ratio": 0.7}})
        self.assertTrue(report["pass"])
        self.assertEqual(report["failed_constraint_ids"], ["speaker_ratio"])

    def test_invalid_contract_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            evaluate_reference_constraints({"constraints": [
                {"id": "x", "kind": "scalar", "target": 1, "tolerance": 0},
                {"id": "x", "kind": "scalar", "target": 1, "tolerance": 0},
            ]}, {"observations": {"x": 1}})


if __name__ == "__main__":
    unittest.main()
