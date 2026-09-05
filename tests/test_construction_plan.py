import copy

import pytest

from modeling_core import selection_sha256, validate_editable_construction_plan
from modeling_core.construction import propose_feature_edges


def test_edge_proposal_excludes_coplanar_loops_and_preserves_explicit_intent():
    edges = [
        {"agent_id": 1, "face_angle_radians": 0.0, "is_boundary": False},
        {"agent_id": 2, "face_angle_radians": 1.5708, "is_boundary": False},
        {"agent_id": 3, "face_angle_radians": 0.2, "is_boundary": False},
    ]
    result = propose_feature_edges(edges, angle_degrees=30, rationale="Keep housing corners; preserve the shallow ridge.", preserve_ids=[3])
    assert result["candidate_edge_ids"] == [2, 3]
    assert not result["mutation_authorized"]
    assert propose_feature_edges(edges, angle_degrees=30, rationale="Round this corner", smooth_ids=[2])["candidate_edge_ids"] == []


def test_edge_proposal_does_not_hide_invalid_topology_with_an_override():
    edges = [{"agent_id": 1, "face_angle_radians": None, "is_boundary": True}]
    result = propose_feature_edges(edges, angle_degrees=30, rationale="Inspect open rim", preserve_ids=[1])
    assert result["unresolved_edge_ids"] == [1]
    assert result["candidate_edge_ids"] == []


def test_edge_proposal_rejects_stale_conflicting_and_duplicate_ids():
    edges = [{"agent_id": 1, "face_angle_radians": 0.0, "is_boundary": False}]
    for kwargs in ({"preserve_ids": [2]}, {"preserve_ids": [1], "smooth_ids": [1]}):
        with pytest.raises(ValueError):
            propose_feature_edges(edges, angle_degrees=30, rationale="Test intent", **kwargs)
    with pytest.raises(ValueError):
        propose_feature_edges(edges * 2, angle_degrees=30, rationale="Duplicate IDs")


def _selection():
    return {
        "schema_version": 1,
        "record_type": "COMPONENT_FAMILY_SELECTION_SET",
        "target_id": "construction-fixture",
        "target_variant": "v1",
        "ready_for_compilation": True,
        "components": {
            "body": {
                "selection": {
                    "selected_result": {
                        "family_compatible": True,
                        "hypothesis": {"shape": {"family": "profile_extrusion"}},
                    }
                }
            }
        },
    }


def _plan(selection):
    return {
        "schema_version": 1,
        "record_type": "EDITABLE_CONSTRUCTION_PLAN",
        "target_id": "construction-fixture",
        "target_variant": "v1",
        "source_selection_sha256": selection_sha256(selection),
        "components": [{
            "component_id": "body",
            "source_proxy_family": "profile_extrusion",
            "construction_method": "CONNECTED_PROFILE_CAGE",
            "object_policy": "CONNECTED_CAGE",
            "feature_sequence": [{
                "feature_id": "establish-outline",
                "operation": "EXTRUDE",
                "rationale": "The body is one continuous manufactured shell.",
                "expected_visual_effect": "Match the measured front silhouette and depth envelope.",
                "rollback_trigger": "Rollback if either registered silhouette regresses.",
                "evidence_basis": [{
                    "status": "OBSERVED",
                    "view_id": "front",
                    "basis": "Hash-bound outer contour and depth landmarks.",
                }],
            }],
            "surface_strategy": {
                "shading": "SUBD",
                "edge_control": "CREASE",
                "rationale": "The reference requires sharp ridges with broad controlled faces.",
                "live_modifiers": [{"type": "SUBSURF", "apply": False}],
            },
            "review_criteria": [
                "reference_fidelity",
                "major_form_and_proportion",
                "depth_and_negative_space",
                "base_cage_editability",
                "evaluated_surface_and_highlight_flow",
                "edge_and_shading_intent",
            ],
            "unresolved_decisions": [],
        }],
    }


def test_construction_plan_separates_proxy_fit_from_editable_realization():
    selection = _selection()
    result = validate_editable_construction_plan(_plan(selection), selection)
    assert result["status"] == "READY"
    assert result["ready_for_blender_realization"] is True
    assert "does not prove" in result["claim_boundary"]


def test_construction_plan_fails_stale_proxy_binding():
    selection = _selection()
    plan = _plan(selection)
    plan["source_selection_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash-bound"):
        validate_editable_construction_plan(plan, selection)


def test_construction_plan_preserves_unresolved_decisions_as_a_gate():
    selection = _selection()
    plan = _plan(selection)
    plan["components"][0]["unresolved_decisions"] = ["support-loop count needs a highlight test"]
    result = validate_editable_construction_plan(plan, selection)
    assert result["status"] == "REQUIRES_DECISIONS"
    assert result["ready_for_blender_realization"] is False


def test_construction_plan_rejects_unapplied_modifier_ambiguity():
    selection = _selection()
    plan = copy.deepcopy(_plan(selection))
    plan["components"][0]["surface_strategy"]["live_modifiers"][0]["apply"] = True
    with pytest.raises(ValueError, match="remain live"):
        validate_editable_construction_plan(plan, selection)
