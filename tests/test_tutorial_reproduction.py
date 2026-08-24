import unittest

from knowledge_engine.tutorial_reproduction import (
    tutorial_modeling_gate_required,
    tutorial_surface_gate_required,
    validate_tutorial_blockout_review,
    validate_tutorial_premodeling_evidence,
)


def valid_payload():
    return {
        "source_identity": {"url": "https://youtube.test/watch?v=x", "title": "Lesson", "creator": "Artist", "duration_verified": True},
        "video_access": {"video_inspected": True, "audio_inspected": True},
        "target_frames": [
            {"id": "final", "role": "final_result", "view": "perspective", "projection": "perspective", "source_kind": "video_frame", "independently_inspected": True, "usable_for_geometry": False},
            {"id": "front", "role": "orthographic_reference", "view": "front", "projection": "orthographic", "source_kind": "video_frame", "independently_inspected": True, "usable_for_geometry": True},
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
        payload["target_frames"] = [{"id": "thumb", "role": "final_result", "view": "perspective", "projection": "perspective", "source_kind": "thumbnail", "independently_inspected": True, "usable_for_geometry": True}]
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

    def test_only_tutorial_construction_sequences_require_gate(self):
        construction = [{"command": "create_quad_shell_grid", "params": {}}]
        read_only = [{"command": "get_full_state", "params": {}}]
        self.assertTrue(tutorial_modeling_gate_required("runs/2026_tutorial-knife/sequence.json", construction))
        self.assertFalse(tutorial_modeling_gate_required("runs/2026_tutorial-knife/verify.json", read_only))
        self.assertFalse(tutorial_modeling_gate_required("runs/2026_heldout-knife/sequence.json", construction))

    def test_transaction_encoding_cannot_bypass_construction_gate(self):
        construction = [{"transaction": {"operation": "create_authored_quad_mesh"}}]
        self.assertTrue(tutorial_modeling_gate_required("runs/2026_tutorial-knife/sequence.json", construction))

    def test_surface_operations_require_separate_blockout_review(self):
        surface = [{"transaction": {"operation": "add_modifier"}}]
        correction = [{"transaction": {"operation": "move_selection"}}]
        self.assertTrue(tutorial_surface_gate_required("runs/2026_tutorial-knife/surface.json", surface))
        self.assertFalse(tutorial_surface_gate_required("runs/2026_tutorial-knife/correct.json", correction))

    def test_direct_command_cannot_bypass_surface_gate(self):
        surface = [{"command": "set_shading"}]
        self.assertTrue(tutorial_surface_gate_required("runs/2026_tutorial-knife/surface.json", surface))

    def test_blockout_review_passes_only_after_measured_clean_cage(self):
        payload = {
            "renders": [
                {"view": "front", "independently_inspected": True, "base_cage_only": True},
                {"view": "isometric", "independently_inspected": True, "base_cage_only": True},
                {"view": "wireframe", "independently_inspected": True, "base_cage_only": True},
            ],
            "constraint_comparisons": [
                {"name": name, "high_salience": True, "status": "PASS", "measured_error": 0.02, "tolerance": 0.03}
                for name in ("length", "height", "tip")
            ],
            "primary_mismatch_tickets": [],
            "decision": "ADVANCE_TO_SURFACE",
        }
        self.assertTrue(validate_tutorial_blockout_review(payload)["pass"])
        payload["primary_mismatch_tickets"] = ["generic silhouette"]
        self.assertFalse(validate_tutorial_blockout_review(payload)["pass"])


if __name__ == "__main__":
    unittest.main()
