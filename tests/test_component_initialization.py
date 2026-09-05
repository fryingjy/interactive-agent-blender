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
    solve_perspective_component_bounds,
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


def _look_at_view(view_id, camera_center, target, *, image_size=(160, 160), fov=45.0):
    camera_center = np.asarray(camera_center, dtype=float)
    forward = np.asarray(target, dtype=float) - camera_center
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, np.asarray([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    rotation = np.vstack((right, down, forward))
    translation = -rotation @ camera_center
    return {
        "id": view_id,
        "projection": "perspective",
        "image_size": list(image_size),
        "vertical_fov_degrees": fov,
        "world_to_camera": np.column_stack((rotation, translation)).tolist(),
        "yaw_degrees": 0.0,
        "pitch_degrees": 0.0,
        "roll_degrees": 0.0,
        "world_scale": 1.0,
        "camera_distance": 1.0,
        "offset_x": 0.0,
        "offset_y": 0.0,
    }


def _perspective_views(target):
    return [
        _look_at_view("front-perspective", [0.0, -5.0, 0.4], target),
        _look_at_view("side-perspective", [5.0, 0.0, 0.6], target),
        _look_at_view("oblique-perspective", [3.5, -4.5, 2.2], target),
    ]


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


def test_profile_initialization_preserves_deep_open_concavities(tmp_path: Path):
    mask = np.zeros((256, 256), dtype=np.uint8)
    outline = np.asarray([
        [40, 220], [70, 150], [88, 60], [105, 145],
        [128, 25], [151, 145], [168, 60], [186, 150], [216, 220],
        [170, 195], [145, 220], [128, 190], [111, 220], [86, 195],
    ], dtype=np.int32)
    cv2.fillPoly(mask, [outline], 1)
    label_path = tmp_path / "front-labels.png"
    side_path = tmp_path / "side-labels.png"
    cv2.imwrite(str(label_path), mask)
    side = np.zeros_like(mask)
    side[25:221, 112:144] = 1
    cv2.imwrite(str(side_path), side)
    views = copy.deepcopy(VIEWS)
    views[0]["image_size"] = [256, 256]
    views[0]["world_scale"] = 2.5
    views[1]["image_size"] = [256, 256]
    views[1]["world_scale"] = 2.5
    bundle = {
        "record_type": "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE",
        "target_id": "concave-profile-fixture",
        "target_variant": "v1",
        "accepted_for_shape_solving": True,
        "views": [
            {
                "view_id": "front", "solver_view": views[0],
                "component_evidence": {
                    "label_map": {"path": str(label_path), "sha256": hashlib.sha256(label_path.read_bytes()).hexdigest()},
                    "observations": {"body": {"label": 1}},
                },
            },
            {
                "view_id": "side", "solver_view": views[1],
                "component_evidence": {
                    "label_map": {"path": str(side_path), "sha256": hashlib.sha256(side_path.read_bytes()).hexdigest()},
                    "observations": {"body": {"label": 1}},
                },
            },
        ],
    }
    assembly = {
        "record_type": "ASSEMBLY_HYPOTHESIS_SET",
        "target_id": "concave-profile-fixture",
        "target_variant": "v1",
        "components": [{
            "component_id": "body",
            "representation_candidates": [{"family": "profile_extrusion"}, {"family": "section_loft"}],
        }],
    }
    initialized = initialize_component_candidates(bundle, assembly)
    profile = next(
        candidate for candidate in initialized["components"]["body"]
        if candidate["shape"]["family"] == "profile_extrusion"
    )
    vertices, faces = build_shape_mesh(profile["shape"])
    reproduced = render_silhouette(vertices, faces, views[0])
    intersection = np.count_nonzero(reproduced & mask.astype(bool))
    union = np.count_nonzero(reproduced | mask.astype(bool))
    assert intersection / union >= 0.975
    assert len(profile["shape"]["profile"]) <= 64


def test_profile_initialization_measures_asymmetric_side_depth_envelope(tmp_path: Path):
    source = {
        "family": "profile_extrusion",
        "profile": [[-0.45, -0.7], [0.45, -0.7], [0.45, 0.7], [-0.45, 0.7]],
        "depth_stations": [
            {"y": -0.24, "scale_z": 0.18, "offset_z": -0.22},
            {"y": -0.12, "scale_z": 0.78, "offset_z": -0.07},
            {"y": 0.0, "scale_z": 1.0, "offset_z": 0.0},
            {"y": 0.12, "scale_z": 0.72, "offset_z": -0.09},
            {"y": 0.24, "scale_z": 0.16, "offset_z": -0.23},
        ],
    }
    bundle = _bundle(tmp_path, source)
    initialized = initialize_component_candidates(bundle, _assembly(["profile_extrusion", "section_loft"]))
    profile = next(
        candidate for candidate in initialized["components"]["body"]
        if candidate["shape"]["family"] == "profile_extrusion"
    )
    stations = profile["shape"]["depth_stations"]
    assert len(stations) > 2
    assert max(abs(station["offset_z"]) for station in stations) > 0.05
    vertices, faces = build_shape_mesh(profile["shape"])
    for view, record in zip(VIEWS, bundle["views"]):
        expected = cv2.imread(record["component_evidence"]["label_map"]["path"], cv2.IMREAD_GRAYSCALE) == 1
        reproduced = render_silhouette(vertices, faces, view)
        intersection = np.count_nonzero(reproduced & expected)
        union = np.count_nonzero(reproduced | expected)
        assert intersection / union >= 0.93


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


def test_calibrated_perspective_masks_initialize_bounds_and_profile_candidates(tmp_path: Path):
    center = np.asarray([0.3, -0.2, 0.15])
    extents = np.asarray([0.4, 0.25, 0.7])
    shape = {
        "family": "section_loft", "segments": 12, "cross_section": "box",
        "translate_x": float(center[0]), "translate_y": float(center[1]), "translate_z": float(center[2]),
        "stations": [
            {"z": float(-extents[2]), "half_width": float(extents[0]), "half_depth": float(extents[1]), "power": 4.0},
            {"z": float(extents[2]), "half_width": float(extents[0]), "half_depth": float(extents[1]), "power": 4.0},
        ],
    }
    views = _perspective_views(center)
    bundle = _bundle(tmp_path, shape, views=views)
    masks = {
        record["view_id"]: cv2.imread(record["component_evidence"]["label_map"]["path"], cv2.IMREAD_GRAYSCALE) == 1
        for record in bundle["views"]
    }
    solved = solve_perspective_component_bounds(masks, views)
    assert solved["status"] == "SOLVED"
    assert solved["method"] == "CALIBRATED_PERSPECTIVE_BBOX_FIT"
    np.testing.assert_allclose(solved["center"], center, atol=0.07)
    np.testing.assert_allclose(solved["half_extents"], extents, atol=0.08)

    initialized = initialize_component_candidates(
        bundle,
        _assembly(["section_loft", "profile_extrusion", "profile_revolution"]),
    )
    report = initialized["initialization_reports"]["body"]
    assert report["bounds"]["method"] == "CALIBRATED_PERSPECTIVE_BBOX_FIT"
    assert {candidate["shape"]["family"] for candidate in initialized["components"]["body"]} == {
        "section_loft", "profile_extrusion",
    }
    assert initialized["ready_for_component_fitting"] is True


def test_duplicate_perspective_camera_rays_remain_underconstrained(tmp_path: Path):
    center = np.asarray([0.3, -0.2, 0.15])
    shape = {
        "family": "section_loft", "segments": 12, "cross_section": "box",
        "stations": [
            {"z": -0.7, "half_width": 0.4, "half_depth": 0.25, "power": 4.0},
            {"z": 0.7, "half_width": 0.4, "half_depth": 0.25, "power": 4.0},
        ],
        "translate_x": 0.3, "translate_y": -0.2, "translate_z": 0.15,
    }
    first = _look_at_view("perspective-a", [0.0, -5.0, 0.4], center)
    second = copy.deepcopy(first)
    second["id"] = "perspective-b"
    bundle = _bundle(tmp_path, shape, views=[first, second])
    result = initialize_component_candidates(bundle, _assembly(["section_loft", "profile_extrusion"]))
    assert result["initialization_reports"]["body"]["bounds"]["status"] == "UNDERCONSTRAINED"
    assert result["components"]["body"] == []


def test_calibrated_perspective_negative_space_selects_ring_family(tmp_path: Path):
    center = np.asarray([0.3, -0.2, 0.15])
    shape = {
        "family": "profile_ring_extrusion",
        "translate_x": float(center[0]), "translate_y": float(center[1]), "translate_z": float(center[2]),
        "outer_profile": [[-0.45, -0.7], [0.45, -0.7], [0.45, 0.7], [-0.45, 0.7]],
        "inner_profile": [[-0.2, -0.35], [0.2, -0.35], [0.2, 0.35], [-0.2, 0.35]],
        "depth_stations": [{"y": -0.25}, {"y": 0.25}],
    }
    bundle = _bundle(tmp_path, shape, views=_perspective_views(center))
    assembly = _assembly(["profile_ring_extrusion", "profile_extrusion", "section_loft"])
    initialized = initialize_component_candidates(bundle, assembly)
    assert initialized["ready_for_component_fitting"] is True
    fitted = fit_component_families(
        bundle,
        assembly,
        initialized["components"],
        seed=4,
        maxiter=6,
        popsize=4,
    )
    assert fitted["components"]["body"]["selection"]["selected_family"] == "profile_ring_extrusion"
    assert fitted["ready_for_compilation"] is True


def test_non_rigid_perspective_calibration_is_rejected():
    view = _look_at_view("invalid", [0.0, -5.0, 0.4], [0.3, -0.2, 0.15])
    view["world_to_camera"][0][0] *= 1.2
    mask = np.zeros((160, 160), dtype=bool)
    mask[50:110, 55:105] = True
    with np.testing.assert_raises_regex(ValueError, "non-rigid calibration"):
        solve_perspective_component_bounds({"invalid": mask}, [view])
