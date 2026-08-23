import unittest

from knowledge_engine.visual_reconstruction import audit_visual_reconstruction


def fixture():
    references = {
        "front": {"reference_id": "front", "projection": "PERSPECTIVE"},
        "rear": {"reference_id": "rear", "projection": "PERSPECTIVE"},
    }
    observations = [
        {"observation_id": "a", "reference_id": "front", "view": "front", "property": "bridge", "value": True, "method": "pixel inspection", "evidence_path": "front.png"},
        {"observation_id": "b", "reference_id": "rear", "view": "rear", "property": "bridge", "value": True, "method": "pixel inspection", "evidence_path": "rear.png"},
    ]
    predictions = lambda value: [
        {"reference_id": "front", "observation_id": "a", "view": "front", "property": "bridge", "prediction_type": "boolean_state", "prediction": value},
        {"reference_id": "rear", "observation_id": "b", "view": "rear", "property": "bridge", "prediction_type": "boolean_state", "prediction": value},
    ]
    payload = {
        "target_id": "fixture",
        "target_variant": "fixture v1",
        "observations": observations,
        "property_authority": [
            {"reference_id": "front", "property": "bridge", "fit_for_property": True},
            {"reference_id": "rear", "property": "bridge", "fit_for_property": True},
        ],
        "passes": {name: {"status": "PASS", "evidence_ids": ["a"]} for name in (
            "identity", "silhouette", "massing", "components", "depth", "negative_space",
            "cross_sections", "representation_hypotheses", "cross_view_prediction",
            "uncertainty", "construction_plan",
        )},
        "regions": [{
            "region_id": "shell",
            "minimum_confirmed_views": 2,
            "selected_hypothesis_id": "connected",
            "hypotheses": [
                {"hypothesis_id": "connected", "interpretation": {"structure_type": "bridged_transition", "summary": "connected"}, "construction": {"family": "quad_shell_grid"}, "predicted_consequences": predictions(True)},
                {"hypothesis_id": "separate", "interpretation": {"structure_type": "floating_separate_assembly", "summary": "separate"}, "construction": {"family": "box_poly"}, "predicted_consequences": predictions(False)},
            ],
        }],
        "construction_plan": {"selected_hypothesis_ids": ["connected"], "generic_operations": ["create_quad_shell_grid"], "reversible_assumptions": []},
    }
    return payload, references


class VisualReconstructionTests(unittest.TestCase):
    def test_valid_cross_view_chain_passes(self):
        payload, references = fixture()
        result = audit_visual_reconstruction(payload, references)
        self.assertTrue(result["pass"], result["errors"])
        self.assertGreater(result["contradiction_count"], 0)

    def test_candidate_cannot_supply_its_own_observation(self):
        payload, references = fixture()
        payload["observations"] = []
        result = audit_visual_reconstruction(payload, references)
        self.assertFalse(result["pass"])

    def test_wrong_declared_winner_fails(self):
        payload, references = fixture()
        payload["regions"][0]["selected_hypothesis_id"] = "separate"
        payload["construction_plan"]["selected_hypothesis_ids"] = ["separate"]
        result = audit_visual_reconstruction(payload, references)
        self.assertFalse(result["pass"])
        self.assertTrue(any("evidence selects" in error for error in result["errors"]))

    def test_unresolved_region_must_remain_reversible(self):
        payload, references = fixture()
        region = payload["regions"][0]
        region["selected_hypothesis_id"] = None
        region["uncertainty"] = "views do not discriminate"
        payload["construction_plan"]["selected_hypothesis_ids"] = []
        result = audit_visual_reconstruction(payload, references)
        self.assertFalse(result["pass"])
        self.assertIn("every unresolved region must remain a reversible construction assumption", result["errors"])

    def test_uncontested_region_with_justification_passes(self):
        payload, references = fixture()
        payload["components"] = [{"id": "shell"}, {"id": "base_plate"}]
        payload["regions"][0]["component_id"] = "shell"
        payload["regions"].append({
            "region_id": "base_plate_construction",
            "component_id": "base_plate",
            "uncontested": True,
            "hypotheses": [{
                "hypothesis_id": "base_plate_extruded",
                "interpretation": {
                    "structure_type": "extruded_slab",
                    "summary": "flat plate",
                    "justification": "the reference shows a constant-thickness flat panel with no visible curvature in any view, consistent with a simple extrusion",
                },
                "construction": {"family": "profile_extrusion"},
            }],
        })
        payload["construction_plan"]["selected_hypothesis_ids"] = ["connected", "base_plate_extruded"]
        result = audit_visual_reconstruction(payload, references)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["checks"]["every_component_has_construction_justification"])

    def test_uncontested_region_without_justification_fails(self):
        payload, references = fixture()
        payload["components"] = [{"id": "shell"}, {"id": "base_plate"}]
        payload["regions"][0]["component_id"] = "shell"
        payload["regions"].append({
            "region_id": "base_plate_construction",
            "component_id": "base_plate",
            "uncontested": True,
            "hypotheses": [{
                "hypothesis_id": "base_plate_extruded",
                "interpretation": {"structure_type": "extruded_slab", "summary": "flat plate"},
                "construction": {"family": "profile_extrusion"},
            }],
        })
        payload["construction_plan"]["selected_hypothesis_ids"] = ["connected", "base_plate_extruded"]
        result = audit_visual_reconstruction(payload, references)
        self.assertFalse(result["pass"])
        self.assertTrue(any("construction justification" in error for error in result["errors"]))

    def test_component_with_no_matching_region_fails(self):
        payload, references = fixture()
        payload["components"] = [{"id": "shell"}, {"id": "orphan_component"}]
        payload["regions"][0]["component_id"] = "shell"
        result = audit_visual_reconstruction(payload, references)
        self.assertFalse(result["pass"])
        self.assertFalse(result["checks"]["every_component_has_construction_justification"])
        self.assertTrue(any("orphan_component" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
