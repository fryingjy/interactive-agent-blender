import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from knowledge_engine.gemini_reference_critic import (
    analyze_reference_candidate,
    build_critic_parts,
    critic_to_repair_tickets,
    derive_correction_directive,
    load_critic_manifest,
    validate_critic_analysis,
    validate_critic_record,
)


def valid_analysis(decision="CORRECT_PRIMARY_FORM"):
    return {
        "target_identity_matches": True,
        "view_reviews": [{
            "view": "front",
            "reference_observation": "A narrow body with a hooked end.",
            "candidate_observation": "The candidate body is too wide and the hook is absent.",
            "semantic_match_score": 0.45,
            "silhouette_match_score": 0.60,
            "component_relationship_score": 0.50,
            "depth_plausibility_score": 0.55,
            "mismatches": [{
                "category": "REPRESENTATION",
                "root_cause": "REPRESENTATION_FAILURE",
                "repair_scope": "REBUILD_COMPONENT",
                "component_id": "body",
                "evidence": "The reference hook overhang is missing.",
                "reference_box_2d": [100, 100, 500, 400],
                "candidate_box_2d": [120, 120, 480, 380],
                "severity": 0.8,
                "confidence": 0.9,
                "correction_goal": "Rebuild the end as an overhanging hook.",
            }],
        }],
        "cross_view_contradictions": [],
        "decision": decision,
        "decision_reason": "Primary representation is wrong.",
        "limitations": ["Only one view was supplied."],
    }


class GeminiReferenceCriticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        Image.new("RGB", (8, 8), "red").save(root / "reference.png")
        Image.new("RGB", (8, 8), "blue").save(root / "candidate.png")
        (root / "manifest.json").write_text(json.dumps({
            "target_id": "test_prop",
            "component_ids": ["body"],
            "views": [{
                "view": "front",
                "reference": "reference.png",
                "candidate": "candidate.png",
            }],
        }), encoding="utf-8")
        self.root = root
        self.manifest = load_critic_manifest(root / "manifest.json")

    def tearDown(self):
        self.temp.cleanup()

    def test_manifest_resolves_and_hashes_distinct_images(self):
        view = self.manifest["views"][0]
        self.assertTrue(Path(view["reference"]).is_absolute())
        self.assertEqual(len(view["reference_sha256"]), 64)
        self.assertNotEqual(view["reference_sha256"], view["candidate_sha256"])

    def test_manifest_rejects_self_comparison(self):
        payload = json.loads((self.root / "manifest.json").read_text())
        payload["views"][0]["candidate"] = "reference.png"
        (self.root / "same.json").write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "cannot compare an image with itself"):
            load_critic_manifest(self.root / "same.json")

    def test_parts_label_every_image_role(self):
        parts = build_critic_parts(self.manifest)
        labels = [part.text for part in parts if part.text]
        self.assertIn("VIEW front — REFERENCE", labels)
        self.assertIn("VIEW front — CANDIDATE", labels)

    def test_valid_localized_rejection_passes_validation(self):
        validate_critic_analysis(valid_analysis(), self.manifest)

    def test_undeclared_component_and_bad_box_fail(self):
        analysis = valid_analysis()
        mismatch = analysis["view_reviews"][0]["mismatches"][0]
        mismatch["component_id"] = "invented"
        mismatch["reference_box_2d"] = [0, 0, 1001, 5]
        with self.assertRaises(ValueError):
            validate_critic_analysis(analysis, self.manifest)

    def test_contradictory_advance_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "advance decision contradicts"):
            validate_critic_analysis(valid_analysis("ADVANCE_TO_SURFACE_CANDIDATE"), self.manifest)

    def test_mocked_call_returns_hash_bound_provenance_without_key(self):
        def generate(**kwargs):
            self.assertEqual(kwargs["model"], "test-model")
            return SimpleNamespace(text=json.dumps(valid_analysis()))

        result = analyze_reference_candidate(
            self.manifest, model="test-model", generate=generate
        )
        self.assertEqual(result["record_type"], "GEMINI_REFERENCE_CRITIC")
        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(result["provenance"]["model"], "test-model")
        self.assertEqual(
            result["provenance"]["view_artifacts"][0]["reference_sha256"],
            self.manifest["views"][0]["reference_sha256"],
        )

    def test_retained_record_revalidates_and_binds_exact_candidate(self):
        def generate(**_kwargs):
            return SimpleNamespace(text=json.dumps(valid_analysis()))

        result = analyze_reference_candidate(self.manifest, model="test-model", generate=generate)
        validated = validate_critic_record(
            result,
            expected_target_id="test_prop",
            expected_views={"front": self.manifest["views"][0]["candidate_sha256"]},
            authorized_reference_hashes={self.manifest["views"][0]["reference_sha256"]},
        )
        self.assertIs(validated, result)

    def test_record_for_different_candidate_or_reference_is_rejected(self):
        def generate(**_kwargs):
            return SimpleNamespace(text=json.dumps(valid_analysis()))

        result = analyze_reference_candidate(self.manifest, model="test-model", generate=generate)
        with self.assertRaisesRegex(ValueError, "candidate views"):
            validate_critic_record(result, expected_views={"front": "0" * 64})
        with self.assertRaisesRegex(ValueError, "authorized evidence"):
            validate_critic_record(result, authorized_reference_hashes={"0" * 64})

    def test_tampered_request_fingerprint_is_rejected(self):
        def generate(**_kwargs):
            return SimpleNamespace(text=json.dumps(valid_analysis()))

        result = analyze_reference_candidate(self.manifest, model="test-model", generate=generate)
        result["provenance"]["request_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "request fingerprint"):
            validate_critic_record(result)

    def test_root_cause_drives_rebuild_and_blocks_polish(self):
        directive = derive_correction_directive(valid_analysis())
        self.assertEqual(directive["disposition"], "REBUILD_COMPONENT")
        self.assertIn("Do not add bevel", directive["prohibited_shortcut"])

    def test_rejection_becomes_root_cause_planner_tickets(self):
        def generate(**_kwargs):
            return SimpleNamespace(text=json.dumps(valid_analysis()))

        result = analyze_reference_candidate(self.manifest, model="test-model", generate=generate)
        tickets = critic_to_repair_tickets(result, current_scene_revision=7)
        self.assertEqual(tickets[0]["root_cause"], "REPRESENTATION_FAILURE")
        self.assertEqual(tickets[0]["repair_scope"], "REBUILD_COMPONENT")
        self.assertEqual(tickets[0]["scene_revision"], 7)
        self.assertEqual(tickets[0]["source"], "GEMINI_REFERENCE_CRITIC")


if __name__ == "__main__":
    unittest.main()
