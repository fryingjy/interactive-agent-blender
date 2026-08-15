import unittest

from knowledge_engine.high_low_audit import HighLowEvidence, audit_production_high_low


def evidence(**overrides):
    values = {
        "high_object": "Housing_HIGH",
        "low_object": "Housing_LOW",
        "separate_collections": True,
        "independent_mesh_datablocks": True,
        "high_base_faces": 240,
        "low_base_faces": 48,
        "high_connected_components": 1,
        "low_connected_components": 1,
        "high_live_modifiers": ("Bevel", "Subdivision"),
        "low_live_modifiers": ("Bevel",),
        "low_uv_layer": "UVMap",
        "low_uv_loop_count": 192,
        "low_degenerate_uv_faces": 0,
        "low_uv_inside_unit_tile": True,
        "silhouette_iou_by_view": {"front": 0.97, "side": 0.96, "top": 0.95},
    }
    values.update(overrides)
    return HighLowEvidence(**values)


class HighLowAuditTests(unittest.TestCase):
    def test_purpose_authored_pair_passes(self):
        result = audit_production_high_low(evidence())
        self.assertEqual(result["disposition"], "PRODUCTION_LOW_AUDIT_PASS")
        self.assertTrue(result["pass"])
        self.assertAlmostEqual(result["face_ratio"], 0.2)

    def test_equal_cage_is_only_editable_variant(self):
        result = audit_production_high_low(evidence(high_base_faces=240, low_base_faces=240))
        self.assertEqual(result["disposition"], "EDITABLE_VARIANT_ONLY")
        self.assertFalse(result["checks"]["purpose_authored_lower_topology"])

    def test_separate_collections_are_required(self):
        result = audit_production_high_low(evidence(separate_collections=False))
        self.assertEqual(result["disposition"], "REVIEW_REQUIRED")
        self.assertIn("separate_collections", result["failures"])

    def test_uv_layer_name_without_valid_layout_fails(self):
        result = audit_production_high_low(evidence(low_degenerate_uv_faces=3))
        self.assertFalse(result["checks"]["low_uv_ready"])

    def test_one_view_cannot_establish_shape_preservation(self):
        result = audit_production_high_low(
            evidence(silhouette_iou_by_view={"front": 0.99})
        )
        self.assertFalse(result["checks"]["multiview_shape_preserved"])

    def test_live_modifier_requirement_preserves_manual_application_control(self):
        result = audit_production_high_low(evidence(low_live_modifiers=()))
        self.assertFalse(result["checks"]["current_modifier_stacks_live"])
        self.assertIn("does not prove", result["modifier_history_boundary"])

    def test_disconnected_joined_shells_fail(self):
        result = audit_production_high_low(evidence(low_connected_components=2))
        self.assertFalse(result["checks"]["single_connected_component_each"])


if __name__ == "__main__":
    unittest.main()
