import copy

from modeling_core import propose_assembly_hypotheses, resolve_assembly_hypotheses


def _component_record(view_id):
    def observation(aspect):
        return {
            "measurements": {
                "aspect_ratio_width_over_height": aspect,
                "enclosed_negative_space_count": 0,
            }
        }

    return {
        "record_type": "REFERENCE_COMPONENT_EVIDENCE",
        "observations": {"body": observation(1.4), "handle": observation(0.35)},
        "visible_adjacency": [["body", "handle"]],
        "view_id": view_id,
    }


def _bundle():
    return {
        "record_type": "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE",
        "target_id": "fixture",
        "target_variant": "v1",
        "accepted_for_shape_solving": True,
        "component_support": {"body": ["front", "side"], "handle": ["front", "side"]},
        "views": [
            {
                "view_id": "front", "source_path": "front.png", "source_sha256": "front-source-sha",
                "mask_path": "front-mask.png", "mask_sha256": "front-mask-sha",
                "component_evidence": _component_record("front"),
            },
            {
                "view_id": "side", "source_path": "side.png", "source_sha256": "side-source-sha",
                "mask_path": "side-mask.png", "mask_sha256": "side-mask-sha",
                "component_evidence": _component_record("side"),
            },
        ],
    }


def _hypotheses():
    return propose_assembly_hypotheses(
        _bundle(),
        [
            {"id": "body", "role": "primary", "candidate_families": ["box_poly", "section_loft"]},
            {"id": "handle", "role": "secondary", "candidate_families": ["profile_extrusion", "curve_sweep"]},
        ],
    )


def _observation(view, **evidence):
    return {
        "pair_id": "body::handle",
        "view_id": view,
        "method": "registered reference inspection",
        "evidence_path": f"{view}.png",
        "evidence_sha256": f"{view}-source-sha",
        **evidence,
    }


def test_proposer_brackets_continuous_and_separate_without_auto_selecting():
    result = _hypotheses()
    assert result["disposition"] == "REQUIRES_DISCRIMINATING_EVIDENCE"
    relation = result["relationship_hypotheses"][0]
    assert relation["visible_adjacency_views"] == ["front", "side"]
    assert relation["selected_hypothesis_id"] is None
    assert {item["construction_policy"] for item in relation["hypotheses"]} == {
        "CONTINUOUS_MESH", "SEPARATE_COMPONENTS"
    }
    assert len(result["components"][0]["representation_candidates"]) == 2
    assert {item["graph_candidate_id"] for item in result["graph_candidates"]} == {
        "continuous-bracket", "separate-bracket"
    }
    assert result["ready_for_construction"] is False


def test_two_view_surface_continuity_selects_shared_cage():
    result = resolve_assembly_hypotheses(
        _hypotheses(),
        [
            _observation("front", seam_visible=False, surface_transition_continuous=True),
            _observation("side", seam_visible=False, surface_transition_continuous=True),
        ],
    )
    assert result["ready_for_component_graph"] is True
    assert result["selected_relationships"][0]["construction_policy"] == "CONTINUOUS_MESH"
    assert result["selected_graph"]["graph_candidate_id"] == "evidence-resolved-mixed-graph"
    assert result["ready_for_construction"] is False


def test_verified_independent_motion_selects_separate_assembly():
    result = resolve_assembly_hypotheses(
        _hypotheses(),
        [_observation("front", independent_motion_verified=True)],
    )
    assert result["ready_for_component_graph"] is True
    assert result["selected_relationships"][0]["construction_policy"] == "SEPARATE_COMPONENTS"


def test_one_ambiguous_view_cannot_choose_topology():
    result = resolve_assembly_hypotheses(
        _hypotheses(),
        [_observation("front", surface_transition_continuous=True)],
    )
    assert result["ready_for_component_graph"] is False
    assert result["unresolved_pair_ids"] == ["body::handle"]


def test_conflicting_multiview_evidence_remains_unresolved():
    observations = [
        _observation("front", seam_visible=False, surface_transition_continuous=True),
        _observation("side", seam_visible=False, surface_transition_continuous=True),
        _observation("front", seam_visible=True),
        _observation("side", seam_visible=True),
    ]
    result = resolve_assembly_hypotheses(_hypotheses(), observations)
    assert result["ready_for_component_graph"] is False
    assert result["relationships"][0]["disposition"] == "CONTRADICTORY_EVIDENCE"


def test_free_floating_observation_cannot_resolve_topology():
    observation = _observation("front", independent_motion_verified=True)
    observation["evidence_sha256"] = "unrelated-artifact"
    try:
        resolve_assembly_hypotheses(_hypotheses(), [observation])
    except ValueError as error:
        assert "bound to the cited source view" in str(error)
    else:
        raise AssertionError("unbound observation was accepted")


def test_proposer_rejects_single_target_specific_family():
    specs = [
        {"id": "body", "candidate_families": ["box_poly", "section_loft"]},
        {"id": "handle", "candidate_families": ["magic_fixture_builder"]},
    ]
    try:
        propose_assembly_hypotheses(copy.deepcopy(_bundle()), specs)
    except ValueError as error:
        assert "at least two unique generic" in str(error)
    else:
        raise AssertionError("target-specific representation family was accepted")
