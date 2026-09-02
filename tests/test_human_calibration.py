import json
import unittest
from pathlib import Path

from knowledge_engine.human_calibration import score_human_calibration, validate_calibration_package


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class HumanCalibrationTests(unittest.TestCase):
    def test_frozen_package_is_complete_and_hash_bound(self):
        result = validate_calibration_package(
            load("runs/2026-09-01_human-calibration/public_manifest.json"),
            load("knowledge/foundation/held_out_human_calibration_anchor.json"),
            root=ROOT,
        )
        self.assertTrue(result["pass"])
        self.assertEqual(result["real_target_count"], 3)

    def test_non_human_response_is_rejected(self):
        response = load("runs/2026-09-01_human-calibration/human_response_template.json")
        response["reviewer_type"] = "agent"
        with self.assertRaisesRegex(ValueError, "human reviewer"):
            score_human_calibration(
                load("runs/2026-09-01_human-calibration/public_manifest.json"),
                load("knowledge/foundation/held_out_human_calibration_anchor.json"),
                response,
                root=ROOT,
            )

    def test_non_retained_reference_can_be_validated_from_frozen_critic_hash(self):
        manifest = load("runs/2026-09-01_human-calibration/public_manifest.json")
        manifest["cases"][0]["reference"] = "runs/non-retained/calibration-source.jpg"
        result = validate_calibration_package(
            manifest,
            load("knowledge/foundation/held_out_human_calibration_anchor.json"),
            root=ROOT,
        )
        self.assertTrue(result["pass"])
        self.assertEqual(
            result["results"][0]["artifact_checks"][0]["availability"],
            "NON_RETAINED_HASH_BOUND",
        )

    def test_reject_everything_cannot_pass_positive_control(self):
        response = {
            "reviewer_type": "human",
            "reviewer_id": "fixture",
            "cases": [
                {"case_id": case_id, "verdict": "REJECT_MAJOR_FORM", "notes": "fixture rejection"}
                for case_id in ("HC-A", "HC-B", "HC-C", "HC-D")
            ],
        }
        result = score_human_calibration(
            load("runs/2026-09-01_human-calibration/public_manifest.json"),
            load("knowledge/foundation/held_out_human_calibration_anchor.json"),
            response,
            root=ROOT,
        )
        self.assertFalse(result["pass"])
        self.assertEqual(result["decision"], "EVALUATOR_HUMAN_DISAGREEMENT")

    def test_full_frozen_agreement_passes_calibration_only(self):
        response = {
            "reviewer_type": "human",
            "reviewer_id": "fixture",
            "cases": [
                {
                    "case_id": "HC-A",
                    "verdict": "REJECT_MAJOR_FORM",
                    "notes": "fixture major-form mismatch",
                },
                {
                    "case_id": "HC-B",
                    "verdict": "REJECT_MAJOR_FORM",
                    "notes": "fixture major-form mismatch",
                },
                {
                    "case_id": "HC-C",
                    "verdict": "REJECT_MAJOR_FORM",
                    "notes": "fixture major-form mismatch",
                },
                {"case_id": "HC-D", "verdict": "ACCEPT_VISIBLE_MATCH", "notes": ""},
            ],
        }
        result = score_human_calibration(
            load("runs/2026-09-01_human-calibration/public_manifest.json"),
            load("knowledge/foundation/held_out_human_calibration_anchor.json"),
            response,
            root=ROOT,
        )
        self.assertTrue(result["pass"])
        self.assertEqual(result["decision"], "PASS")
        self.assertIn("does not establish professional modeling skill", result["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
