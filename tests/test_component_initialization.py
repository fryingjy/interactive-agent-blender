import copy
import hashlib
from pathlib import Path

import cv2
import numpy as np

from modeling_core import (
    build_shape_mesh,
    fit_component_families,
    initialize_component_candidates,
    render_silhouette,
    solve_orthographic_component_bounds,
)


VIEWS = [
    {
        "id": "front", "projection": "orthographic", "image_size": [128, 128],
        "yaw_degrees": 0.0, "pitch_degrees": 0.0, "roll_degrees": 0.0,
        "world_scale": 3.2, "offset_x": 0.0, "offset_y": 0.0,
    },
    {
        "id": "side", "projection": "orthographic", "image_size": [128, 128],
        "yaw_degrees": 90.0, "pitch_degrees": 0.0, "roll_degrees": 0.0,
        "world_scale": 3.2, "offset_x": 0.0, "offset_y": 0.0,
    },
]


def _bundle(tmp_path: Path, shape, *, views=None):
    views = copy.deepcopy(views or VIEWS)
    vertices, faces = build_shape_mesh(shape)
    records = []
    for view in views:
        mask = render_silhouette(vertices, faces, view)
        label_path = tmp_path / f"{view['id']}-labels.png"
        cv2.imwrite(str(label_path), mask.astype(np.uint8))
        records.append({
            "view_id": view["id"],
            "solver_view": view,
            "component_evidence": {
                "label_map": {"path": str(label_path), "sha256": hashlib.sha256(label_path.read_bytes()).hexdigest()},
                "observations": {"body": {"label": 1}},
            },
        })
    return {
        "record_type": "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE",
        "target_id": "initializer-fixture",
        "target_variant": "v1",
        "accepted_for_shape_solving": True,
        "views": records,
    }


def _assembly(families):
    return {
        "record_type": "ASSEMBLY_HYPOTHESIS_SET",
        "target_id": "initializer-fixture",
        "target_variant": "v1",
        "components": [{
            "component_id": "body",
            "representation_candidates": [{"family": family} for family in families],
        }],
    }


def test_registered_front_and_side_masks_initialize_world_bounds_and_two_families(tmp_path: Path):
    shape = {
        "family": "section_loft",
        "segments": 12,
        "cross_section": "box",
        "translate_x": 0.38,
        "translate_y": -0.24,
        "translate_z": 0.16,
        "stations": [
            {"z": -0.65, "half_width": 0.32, "half_depth": 0.2, "power": 4.0},
            {"z": 0.65, "half_width": 0.32, "half_depth": 0.2, "power": 4.0},
        ],
    }
    result = initialize_component_candidates(
        _bundle(tmp_path, shape),
        _assembly(["section_loft", "profile_extrusion", "profile_revolution"]),
    )
    report = result["initialization_reports"]["body"]
    assert report["bounds"]["status"] == "SOLVED"
    np.testing.assert_allclose(report["bounds"]["center"], [0.38, -0.24, 0.16], atol=0.035)
    np.testing.assert_allclose(report["bounds"]["half_extents"], [0.32, 0.2, 0.65], atol=0.04)
    assert {candidate["shape"]["family"] for candidate in result["components"]["body"]} == {
        "section_loft", "profile_extrusion",
    }
    assert report["families"]["profile_revolution"]["status"] == "NOT_INITIALIZED"
    assert result["ready_for_component_fitting"] is True
    assert all(len(candidate["variables"]) == 6 for candidate in result["components"]["body"])


def test_rank_deficient_views_preserve_depth_uncertainty_instead_of_inventing_it(tmp_path: Path):
    shape = {
        "family": "section_loft", "segments": 12, "cross_section": "box",
        "stations": [
            {"z": -0.6, "half_width": 0.3, "half_depth": 0.2, "power": 4.0},
            {"z": 0.6, "half_width": 0.3, "half_depth": 0.2, "power": 4.0},
        ],
    }
    duplicate_front = [copy.deepcopy(VIEWS[0]), {**copy.deepcopy(VIEWS[0]), "id": "front-copy"}]
    result = initialize_component_candidates(
        _bundle(tmp_path, shape, views=duplicate_front),
        _assembly(["section_loft", "profile_extrusion"]),
    )
    report = result["initialization_reports"]["body"]
    assert report["bounds"]["status"] == "UNDERCONSTRAINED"
    assert report["candidate_count"] == 0
    assert result["ready_for_component_fitting"] is False


def test_one_visible_hole_initializes_ring_and_solid_competing_candidates(tmp_path: Path):
    shape = {
        "family": "profile_ring_extrusion",
        "translate_x": -0.2,
        "translate_y": 0.18,
        "translate_z": 0.1,
        "outer_profile": [[-0.75, -0.65], [0.75, -0.65], [0.75, 0.65], [-0.75, 0.65]],
        "inner_profile": [[-0.28, -0.25], [0.28, -0.25], [0.28, 0.25], [-0.28, 0.25]],
        "depth_stations": [{"y": -0.16}, {"y": 0.16}],
    }
    bundle = _bundle(tmp_path, shape)
    assembly = _assembly(["profile_ring_extrusion", "profile_extrusion", "section_loft"])
    result = initialize_component_candidates(bundle, assembly)
    families = {candidate["shape"]["family"] for candidate in result["components"]["body"]}
    assert families == {"profile_ring_extrusion", "profile_extrusion", "section_loft"}
    ring = next(candidate for candidate in result["components"]["body"] if candidate["shape"]["family"] == "profile_ring_extrusion")
    assert len(ring["shape"]["outer_profile"]) == 12
    assert len(ring["shape"]["inner_profile"]) == 12
    assert result["ready_for_component_fitting"] is True
    fitted = fit_component_families(
        bundle,
        assembly,
        result["components"],
        seed=3,
        maxiter=6,
        popsize=4,
    )
    assert fitted["components"]["body"]["selection"]["selected_family"] == "profile_ring_extrusion"
    assert fitted["ready_for_compilation"] is True


def test_inconsistent_registered_bounds_are_rejected_instead_of_widening_forever():
    front = np.zeros((128, 128), dtype=bool)
    side = np.zeros((128, 128), dtype=bool)
    front[35:94, 45:84] = True
    side[70:120, 45:84] = True
    result = solve_orthographic_component_bounds(
        {"front": front, "side": side},
        copy.deepcopy(VIEWS),
        maximum_relative_residual=0.1,
    )
    assert result["status"] == "REJECTED"
    assert "disagree" in result["issues"][0]
