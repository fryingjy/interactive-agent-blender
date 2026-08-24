import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from knowledge_engine.gemini_reference_critic import analyze_reference_candidate, load_critic_manifest

from knowledge_engine.tutorial_reproduction import (
    asset_surface_gate_required,
    asset_mutation_gate_required,
    procedural_fixture_sequence,
    reference_modeling_gate_required,
    tutorial_modeling_gate_required,
    tutorial_surface_gate_required,
    validate_tutorial_blockout_review,
    validate_tutorial_premodeling_evidence,
)


def valid_payload():
    fixture_path = Path(__file__).resolve()
    fixture_digest = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    return {
        "target_id": "lesson_sword",
        "target_variant": "creator_final",
        "source_identity": {"url": "https://youtube.test/watch?v=x", "title": "Lesson", "creator": "Artist", "duration_verified": True},
        "video_access": {"video_inspected": True, "audio_inspected": True},
        "target_frames": [
            {"id": "final", "role": "final_result", "view": "perspective", "projection": "perspective", "source_kind": "video_frame", "independently_inspected": True, "usable_for_geometry": False, "local_path": str(fixture_path), "sha256": fixture_digest},
            {"id": "front", "role": "orthographic_reference", "view": "front", "projection": "orthographic", "source_kind": "video_frame", "independently_inspected": True, "usable_for_geometry": True, "local_path": str(fixture_path), "sha256": fixture_digest},
        ],
        "constraints": [
            {"name": "length_ratio", "high_salience": True, "measurement_status": "MEASURED", "evidence_frame_id": "front", "value_normalized": 0.8},
            {"name": "height_ratio", "high_salience": True, "measurement_status": "MEASURED", "evidence_frame_id": "front", "value_normalized": 0.2},
            {"name": "tip_position", "high_salience": True, "measurement_status": "MEASURED", "evidence_frame_id": "front", "value_normalized": 0.05},
        ],
        "component_plan": [{"component": "blade", "construction_strategy": "connected quad shell", "evidence_frame_ids": ["front"]}],
        "unresolved_high_salience": [],
    }


class TutorialPremodelingGateTests(unittest.TestCase):
    def test_valid_orthographic_evidence_passes(self):
        result = validate_tutorial_premodeling_evidence(valid_payload())
        self.assertTrue(result["pass"], result["issues"])

    def test_promotional_thumbnail_alone_fails_closed(self):
        payload = valid_payload()
        retained = payload["target_frames"][0]
        payload["target_frames"] = [{"id": "thumb", "role": "final_result", "view": "perspective", "projection": "perspective", "source_kind": "thumbnail", "independently_inspected": True, "usable_for_geometry": True, "local_path": retained["local_path"], "sha256": retained["sha256"]}]
        for constraint in payload["constraints"]:
            constraint["evidence_frame_id"] = "thumb"
        payload["component_plan"][0]["evidence_frame_ids"] = ["thumb"]
        result = validate_tutorial_premodeling_evidence(payload)
        self.assertFalse(result["pass"])
        self.assertFalse(result["checks"]["thumbnail_not_used_as_geometry_pass"])
        self.assertFalse(result["checks"]["geometry_reference_pass"])

    def test_unresolved_major_form_blocks(self):
        payload = valid_payload()
        payload["unresolved_high_salience"] = ["blade depth unknown"]
        self.assertFalse(validate_tutorial_premodeling_evidence(payload)["pass"])

    def test_three_measured_constraints_are_required(self):
        payload = valid_payload()
        payload["constraints"] = payload["constraints"][:2]
        self.assertFalse(validate_tutorial_premodeling_evidence(payload)["checks"]["measured_constraints_pass"])

    def test_missing_or_changed_frame_file_fails_closed(self):
        payload = valid_payload()
        payload["target_frames"][0]["local_path"] = str(Path(__file__).with_name("missing-frame.png"))
        payload["target_frames"][1]["sha256"] = "0" * 64
        result = validate_tutorial_premodeling_evidence(payload)
        self.assertFalse(result["pass"])
        self.assertFalse(result["checks"]["retained_frame_files_pass"])

    def test_duplicate_or_out_of_range_constraints_fail_closed(self):
        payload = valid_payload()
        payload["constraints"][1]["name"] = payload["constraints"][0]["name"]
        payload["constraints"][2]["value_normalized"] = 1.2
        self.assertFalse(validate_tutorial_premodeling_evidence(payload)["checks"]["measured_constraints_pass"])

    def test_only_tutorial_construction_sequences_require_gate(self):
        construction = [{"command": "create_quad_shell_grid", "params": {}}]
        read_only = [{"command": "get_full_state", "params": {}}]
        self.assertTrue(tutorial_modeling_gate_required("runs/2026_tutorial-knife/sequence.json", construction))
        self.assertFalse(tutorial_modeling_gate_required("runs/2026_tutorial-knife/verify.json", read_only))
        self.assertFalse(tutorial_modeling_gate_required("runs/2026_heldout-knife/sequence.json", construction))
        self.assertTrue(reference_modeling_gate_required("runs/2026_heldout-knife/sequence.json", construction))
        self.assertFalse(reference_modeling_gate_required("runs/2026_profile-lab/sequence.json", construction))
        self.assertTrue(procedural_fixture_sequence("runs/2026_profile-lab/sequence.json"))

    def test_transaction_encoding_cannot_bypass_construction_gate(self):
        construction = [{"transaction": {"operation": "create_authored_quad_mesh"}}]
        self.assertTrue(tutorial_modeling_gate_required("runs/2026_tutorial-knife/sequence.json", construction))

    def test_surface_operations_require_separate_blockout_review(self):
        surface = [{"transaction": {"operation": "add_modifier"}}]
        correction = [{"transaction": {"operation": "move_selection"}}]
        self.assertTrue(tutorial_surface_gate_required("runs/2026_tutorial-knife/surface.json", surface))
        self.assertFalse(tutorial_surface_gate_required("runs/2026_tutorial-knife/correct.json", correction))
        self.assertTrue(asset_surface_gate_required("runs/2026_heldout-knife/surface.json", surface))
        self.assertFalse(asset_surface_gate_required("runs/2026_modifier-lab/surface.json", surface))
        self.assertTrue(asset_mutation_gate_required("runs/2026_heldout-knife/correct.json", correction))
        self.assertFalse(asset_mutation_gate_required(
            "runs/2026_heldout-knife/review.json", [{"command": "get_full_state"}]
        ))

    def test_direct_command_cannot_bypass_surface_gate(self):
        surface = [{"command": "set_shading"}]
        self.assertTrue(tutorial_surface_gate_required("runs/2026_tutorial-knife/surface.json", surface))

    def test_blockout_review_passes_only_after_measured_clean_cage(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = self._valid_blockout_payload(Path(directory), advance=True)
            self.assertTrue(validate_tutorial_blockout_review(payload)["pass"])
            payload["primary_mismatch_tickets"] = ["generic silhouette"]
            self.assertFalse(validate_tutorial_blockout_review(payload)["pass"])

    def test_semantic_rejection_blocks_surface_even_when_metrics_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = self._valid_blockout_payload(Path(directory), advance=False)
            result = validate_tutorial_blockout_review(payload)
            self.assertFalse(result["pass"])
            self.assertFalse(result["checks"]["semantic_critic_pass"])

    def test_semantic_review_for_different_render_cannot_be_replayed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self._valid_blockout_payload(root, advance=True)
            replacement = root / "replacement.png"
            Image.new("RGB", (8, 8), "green").save(replacement)
            front = next(item for item in payload["renders"] if item["view"] == "front")
            front["local_path"] = str(replacement)
            front["sha256"] = hashlib.sha256(replacement.read_bytes()).hexdigest()
            result = validate_tutorial_blockout_review(payload)
            self.assertFalse(result["pass"])
            self.assertFalse(result["checks"]["semantic_critic_pass"])

    def test_negative_or_duplicate_measurements_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = self._valid_blockout_payload(Path(directory), advance=True)
            payload["constraint_comparisons"][1]["name"] = payload["constraint_comparisons"][0]["name"]
            payload["constraint_comparisons"][2]["measured_error"] = -1.0
            self.assertFalse(validate_tutorial_blockout_review(payload)["checks"]["high_salience_constraints_pass"])

    @staticmethod
    def _valid_blockout_payload(root: Path, *, advance: bool) -> dict:
        reference = root / "reference.png"
        candidate = root / "front.png"
        isometric = root / "isometric.png"
        wireframe = root / "wireframe.png"
        Image.new("RGB", (8, 8), "red").save(reference)
        Image.new("RGB", (8, 8), "blue").save(candidate)
        Image.new("RGB", (8, 8), "yellow").save(isometric)
        Image.new("RGB", (8, 8), "white").save(wireframe)
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps({
            "target_id": "lesson_sword",
            "component_ids": ["blade"],
            "views": [{"view": "front", "reference": "reference.png", "candidate": "front.png"}],
        }), encoding="utf-8")
        manifest = load_critic_manifest(manifest_path)
        analysis = {
            "target_identity_matches": advance,
            "view_reviews": [{
                "view": "front",
                "reference_observation": "A long curved blade.",
                "candidate_observation": "A long curved blade." if advance else "A short straight block.",
                "semantic_match_score": 0.95 if advance else 0.3,
                "silhouette_match_score": 0.95 if advance else 0.3,
                "component_relationship_score": 0.95 if advance else 0.4,
                "depth_plausibility_score": 0.95 if advance else 0.5,
                "mismatches": [] if advance else [{
                    "category": "REPRESENTATION",
                    "root_cause": "REPRESENTATION_FAILURE",
                    "repair_scope": "REBUILD_COMPONENT",
                    "component_id": "blade",
                    "evidence": "The blade uses the wrong shape family.",
                    "reference_box_2d": [0, 0, 1000, 1000],
                    "candidate_box_2d": [0, 0, 1000, 1000],
                    "severity": 0.9,
                    "confidence": 0.95,
                    "correction_goal": "Rebuild the primary blade cage.",
                }],
            }],
            "cross_view_contradictions": [],
            "decision": "ADVANCE_TO_SURFACE_CANDIDATE" if advance else "REJECT_REPRESENTATION",
            "decision_reason": "The base cage matches." if advance else "The shape family is wrong.",
            "limitations": ["Synthetic test fixture."],
        }

        def generate(**_kwargs):
            from types import SimpleNamespace
            return SimpleNamespace(text=json.dumps(analysis))

        critic = analyze_reference_candidate(manifest, model="test-model", generate=generate)
        render_paths = {"front": candidate, "isometric": isometric, "wireframe": wireframe}
        return {
            "target_id": "lesson_sword",
            "component_ids": ["blade"],
            "scene_revision": 4,
            "authorized_reference_sha256": [manifest["views"][0]["reference_sha256"]],
            "renders": [{
                "view": view,
                "local_path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "scene_revision": 4,
                "independently_inspected": True,
                "base_cage_only": True,
                "semantic_candidate": view == "front",
            } for view, path in render_paths.items()],
            "constraint_comparisons": [{
                "name": name,
                "candidate_view": "front",
                "high_salience": True,
                "status": "PASS",
                "measured_error": 0.01,
                "tolerance": 0.02,
            } for name in ("length", "height", "tip")],
            "primary_mismatch_tickets": [],
            "decision": "ADVANCE_TO_SURFACE",
            "semantic_critic": critic,
        }


if __name__ == "__main__":
    unittest.main()
