import copy
import json
from pathlib import Path

import cv2
import numpy as np

from modeling_core import (
    build_multiview_evidence_bundle,
    extract_reference_evidence,
    materialize_confirmed_component_evidence,
    propose_component_regions,
    propose_cross_view_correspondences,
)


def _evidence(tmp_path: Path, name: str, *, swap=False, uniform=False):
    image = np.full((90, 120, 3), 245, dtype=np.uint8)
    if uniform:
        image[18:72, 24:96] = (40, 80, 180)
    elif swap:
        image[18:72, 24:60] = (190, 70, 35)
        image[18:72, 60:96] = (35, 55, 190)
    else:
        image[18:72, 24:60] = (35, 55, 190)
        image[18:72, 60:96] = (190, 70, 35)
    source = tmp_path / f"{name}.png"
    cv2.imwrite(str(source), image)
    return extract_reference_evidence(source, tmp_path / f"{name}-evidence")


def test_two_color_object_proposes_editable_regions_without_semantic_authorization(tmp_path: Path):
    evidence = _evidence(tmp_path, "two-color")
    result = propose_component_regions(evidence, tmp_path / "proposal", maximum_regions=4, seed=7)
    assert result["region_count"] == 2
    assert result["accepted_as_semantic_evidence"] is False
    assert result["review_required"] is True
    labels = cv2.imread(result["artifacts"]["editable_label_map"], cv2.IMREAD_GRAYSCALE)
    source_mask = cv2.imread(evidence["artifacts"]["editable_mask"], cv2.IMREAD_GRAYSCALE) >= 128
    assert np.array_equal(labels > 0, source_mask)
    assert set(np.unique(labels)) == {0, 1, 2}
    assert all(region["connected_fragment_count"] == 1 for region in result["regions"])


def test_uniform_object_does_not_invent_multiple_components(tmp_path: Path):
    evidence = _evidence(tmp_path, "uniform", uniform=True)
    result = propose_component_regions(evidence, tmp_path / "uniform-proposal", maximum_regions=6)
    assert result["region_count"] == 1
    assert result["proposal_confidence"] == 1.0


def test_cross_view_match_uses_appearance_not_left_right_position(tmp_path: Path):
    front = propose_component_regions(_evidence(tmp_path, "front"), tmp_path / "front-proposal", seed=3)
    reverse = propose_component_regions(_evidence(tmp_path, "reverse", swap=True), tmp_path / "reverse-proposal", seed=3)
    result = propose_cross_view_correspondences([
        {"view_id": "front", "proposal": front},
        {"view_id": "reverse", "proposal": reverse},
    ])
    assert result["status"] == "CONFIDENT_PROPOSAL"
    assert result["accepted_as_semantic_identity"] is False
    front_regions = {region["proposal_region_id"]: np.asarray(region["mean_lab"]) for region in front["regions"]}
    reverse_regions = {region["proposal_region_id"]: np.asarray(region["mean_lab"]) for region in reverse["regions"]}
    for group in result["groups"]:
        distance = np.linalg.norm(front_regions[group["matches"]["front"]] - reverse_regions[group["matches"]["reverse"]])
        assert distance < 1.0


def test_cross_view_match_preserves_descriptor_ambiguity(tmp_path: Path):
    first = propose_component_regions(_evidence(tmp_path, "first"), tmp_path / "first-proposal", seed=5)
    second = propose_component_regions(_evidence(tmp_path, "second", swap=True), tmp_path / "second-proposal", seed=5)
    ambiguous = copy.deepcopy(second)
    shared = np.mean([region["mean_lab"] for region in ambiguous["regions"]], axis=0).tolist()
    for region in ambiguous["regions"]:
        region["mean_lab"] = shared
        region["visible_area_fraction_of_object"] = 0.5
        region["measurements"]["aspect_ratio_width_over_height"] = 2.0 / 3.0
    for region in first["regions"]:
        region["visible_area_fraction_of_object"] = 0.5
        region["measurements"]["aspect_ratio_width_over_height"] = 2.0 / 3.0
    result = propose_cross_view_correspondences([
        {"view_id": "first", "proposal": first},
        {"view_id": "ambiguous", "proposal": ambiguous},
    ])
    assert result["status"] == "AMBIGUOUS_REVIEW_REQUIRED"
    assert len(result["ambiguous_matches"]) == 2


def test_tampered_proposal_label_map_cannot_be_matched(tmp_path: Path):
    first = propose_component_regions(_evidence(tmp_path, "a"), tmp_path / "a-proposal")
    second = propose_component_regions(_evidence(tmp_path, "b", swap=True), tmp_path / "b-proposal")
    cv2.imwrite(first["artifacts"]["editable_label_map"], np.zeros((90, 120), dtype=np.uint8))
    try:
        propose_cross_view_correspondences([
            {"view_id": "a", "proposal": first},
            {"view_id": "b", "proposal": second},
        ])
    except ValueError as error:
        assert "stale or missing" in str(error)
    else:
        raise AssertionError("tampered component proposal was accepted")


def test_reviewed_correspondences_materialize_shared_semantic_component_evidence(tmp_path: Path):
    front_evidence = _evidence(tmp_path, "confirmed-front")
    reverse_evidence = _evidence(tmp_path, "confirmed-reverse", swap=True)
    front = propose_component_regions(front_evidence, tmp_path / "confirmed-front-proposal", seed=8)
    reverse = propose_component_regions(reverse_evidence, tmp_path / "confirmed-reverse-proposal", seed=8)
    correspondence = propose_cross_view_correspondences([
        {"view_id": "front", "proposal": front},
        {"view_id": "reverse", "proposal": reverse},
    ])
    assignments = [
        {
            "proposal_group_id": correspondence["groups"][0]["proposal_group_id"],
            "component_id": "body",
            "role": "PRIMARY_VOLUME",
            "continuity_policy": "CONTINUOUS_MESH",
        },
        {
            "proposal_group_id": correspondence["groups"][1]["proposal_group_id"],
            "component_id": "insert",
            "role": "SECONDARY_VOLUME",
            "continuity_policy": "SEPARATE_ASSEMBLY",
        },
    ]
    confirmation = {
        "decision": "CONFIRM_COMPONENT_IDENTITY",
        "reviewer_type": "AGENT_EVIDENCE_REVIEW",
        "reviewer_id": "controlled-test",
        "reviewed_at": "2026-09-02T00:00:00Z",
        "notes": "Controlled colors establish the fixture identity only.",
    }
    result = materialize_confirmed_component_evidence(
        correspondence,
        [
            {"view_id": "front", "proposal": front, "evidence": front_evidence},
            {"view_id": "reverse", "proposal": reverse, "evidence": reverse_evidence},
        ],
        assignments,
        confirmation,
        tmp_path / "confirmed-output",
    )
    assert result["ready_for_bundle"] is True
    for view_id in ("front", "reverse"):
        record = json.loads(Path(result["views"][view_id]["path"]).read_text(encoding="utf-8"))
        assert record["accepted_for_bundle"] is True
        assert record["component_ids"] == ["body", "insert"]
        assert record["proposal_confirmation"]["confirmation"]["decision"] == "CONFIRM_COMPONENT_IDENTITY"
    audit = {
        "record_type": "REFERENCE_SET_AUDIT",
        "target_id": "confirmed-fixture",
        "target_variant": "v1",
        "authorized_reference_sha256": [
            front_evidence["source"]["sha256"], reverse_evidence["source"]["sha256"],
        ],
        "pass": True,
    }
    registration = {
        "record_type": "REFERENCE_REGISTRATION_GATE",
        "target_id": "confirmed-fixture",
        "authoritative_views": ["front", "reverse"],
        "pass": True,
    }
    bundle = build_multiview_evidence_bundle(
        audit,
        registration,
        [
            {"view_id": "front", "source_id": "fixture", "evidence": front_evidence, "components": result["views"]["front"]["path"]},
            {"view_id": "reverse", "source_id": "fixture", "evidence": reverse_evidence, "components": result["views"]["reverse"]["path"]},
        ],
        required_component_support={"body": 2, "insert": 2},
    )
    assert bundle["accepted_for_shape_solving"] is True
    assert bundle["component_support"] == {"body": ["front", "reverse"], "insert": ["front", "reverse"]}


def test_confirmation_requires_complete_assignments_and_explicit_decision(tmp_path: Path):
    first_evidence = _evidence(tmp_path, "gate-first")
    second_evidence = _evidence(tmp_path, "gate-second", swap=True)
    first = propose_component_regions(first_evidence, tmp_path / "gate-first-proposal")
    second = propose_component_regions(second_evidence, tmp_path / "gate-second-proposal")
    correspondence = propose_cross_view_correspondences([
        {"view_id": "first", "proposal": first},
        {"view_id": "second", "proposal": second},
    ])
    views = [
        {"view_id": "first", "proposal": first, "evidence": first_evidence},
        {"view_id": "second", "proposal": second, "evidence": second_evidence},
    ]
    confirmation = {
        "decision": "CONFIRM_COMPONENT_IDENTITY",
        "reviewer_type": "HUMAN",
        "reviewer_id": "fixture-reviewer",
        "reviewed_at": "2026-09-02T00:00:00Z",
    }
    incomplete = [{"proposal_group_id": correspondence["groups"][0]["proposal_group_id"], "component_id": "body"}]
    try:
        materialize_confirmed_component_evidence(correspondence, views, incomplete, confirmation, tmp_path / "incomplete")
    except ValueError as error:
        assert "cover every proposal group" in str(error)
    else:
        raise AssertionError("incomplete semantic confirmation was accepted")
    invalid_confirmation = dict(confirmation, decision="APPROVE")
    assignments = [
        {"proposal_group_id": group["proposal_group_id"], "component_id": f"part-{index}"}
        for index, group in enumerate(correspondence["groups"], 1)
    ]
    try:
        materialize_confirmed_component_evidence(correspondence, views, assignments, invalid_confirmation, tmp_path / "invalid")
    except ValueError as error:
        assert "CONFIRM_COMPONENT_IDENTITY" in str(error)
    else:
        raise AssertionError("invalid confirmation decision was accepted")
