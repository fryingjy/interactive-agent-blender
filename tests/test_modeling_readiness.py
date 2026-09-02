import copy
import json
import unittest
from pathlib import Path

from knowledge_engine.modeling_readiness import (
    evaluate_modeling_scope,
    validate_modeling_readiness_policy,
)


def policy():
    return {
        "schema_version": 1,
        "record_type": "REFERENCE_MODELING_READINESS",
        "status": "ACTIVE",
        "allowed_scopes": ["SYSTEM_VALIDATION_FIXTURE"],
        "clearance_gates": [
            {"id": "registration", "status": "PASS"},
            {"id": "segmentation", "status": "NOT_RUN"},
        ],
    }


class ModelingReadinessTests(unittest.TestCase):
    def test_active_hold_blocks_new_props(self):
        result = evaluate_modeling_scope(policy(), "NEW_REFERENCE_PROP")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["open_clearance_gates"], ["segmentation"])

    def test_active_hold_allows_only_system_fixture(self):
        self.assertTrue(evaluate_modeling_scope(policy(), "SYSTEM_VALIDATION_FIXTURE")["allowed"])
        self.assertFalse(evaluate_modeling_scope(policy(), "REPLAY_EXISTING_TARGET")["allowed"])

    def test_cleared_requires_every_gate_to_pass(self):
        invalid = copy.deepcopy(policy())
        invalid["status"] = "CLEARED"
        with self.assertRaisesRegex(ValueError, "every clearance gate"):
            validate_modeling_readiness_policy(invalid)
        invalid["clearance_gates"][1]["status"] = "PASS"
        validate_modeling_readiness_policy(invalid)
        self.assertTrue(evaluate_modeling_scope(invalid, "NEW_REFERENCE_PROP")["allowed"])

    def test_repository_policy_is_cleared_by_retained_human_calibration(self):
        root = Path(__file__).resolve().parents[1]
        repository_policy = json.loads(
            (root / "knowledge/foundation/reference_modeling_readiness.json").read_text(
                encoding="utf-8"
            )
        )
        validate_modeling_readiness_policy(repository_policy)
        calibration = next(
            gate
            for gate in repository_policy["clearance_gates"]
            if gate["id"] == "held_out_human_visual_calibration"
        )
        result = json.loads(
            (root / "runs/2026-09-01_human-calibration/result.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(repository_policy["status"], "CLEARED")
        self.assertEqual(calibration["status"], "PASS")
        self.assertTrue(result["pass"])
        self.assertEqual(result["agreement_count"], result["case_count"])
        self.assertTrue(evaluate_modeling_scope(repository_policy, "NEW_REFERENCE_PROP")["allowed"])


if __name__ == "__main__":
    unittest.main()
