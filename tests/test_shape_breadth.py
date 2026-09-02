import numpy as np
import pytest

from modeling_core import (
    build_curve_sweep,
    build_profile_extrusion,
    build_profile_revolution,
    build_profile_ring_extrusion,
    build_profile_sweep,
    compile_blender_command,
    fit_hypothesis,
    render_silhouette,
    shape_boundary_ports,
    validate_hypothesis,
    select_shape_family,
)


VIEW = {
    "id": "fixture",
    "projection": "orthographic",
    "image_size": [96, 96],
    "world_scale": 4.0,
}


def _hypothesis(shape):
    return {
        "schema_version": 1,
        "candidate_id": "breadth-fixture",
        "shape": shape,
        "views": [VIEW],
        "variables": [],
    }


def test_profile_revolution_builds_an_open_connected_quad_cage():
    shape = {
        "family": "profile_revolution",
        "segments": 12,
        "profile": [[0.25, -1.0], [0.45, -0.4], [0.32, 0.5], [0.18, 1.0]],
    }
    normalized = validate_hypothesis(_hypothesis(shape))
    vertices, faces = build_profile_revolution(normalized["shape"])
    assert vertices.shape == (48, 3)
    assert len(faces) == 36
    assert all(len(face) == 4 for face in faces)
    assert shape_boundary_ports(normalized["shape"]) == {
        "start": list(range(12)),
        "end": list(range(36, 48)),
    }
    command = compile_blender_command(normalized, name="RevolvedHandle")
    assert command["metadata"]["source"] == "modeling_core.profile_revolution"
    assert command["metadata"]["modifiers_applied"] is False


def test_profile_revolution_runs_through_bounded_silhouette_fitting():
    raw = _hypothesis({
        "family": "profile_revolution",
        "segments": 12,
        "scale_x": 0.8,
        "profile": [[0.25, -1.0], [0.45, -0.4], [0.32, 0.5], [0.18, 1.0]],
    })
    raw["variables"] = [{"pointer": "/shape/scale_x", "bounds": [0.6, 1.4]}]
    truth = validate_hypothesis(_hypothesis({
        **raw["shape"],
        "scale_x": 1.2,
    }))
    vertices, faces = build_profile_revolution(truth["shape"])
    reference = render_silhouette(vertices, faces, truth["views"][0])
    result = fit_hypothesis(raw, {"fixture": reference}, seed=5, maxiter=8, popsize=5)
    assert abs(result["hypothesis"]["shape"]["scale_x"] - 1.2) < 0.08
    assert result["family_compatible"] is True


def test_curve_sweep_builds_a_bent_all_quad_cage_with_nonzero_faces():
    shape = {
        "family": "curve_sweep",
        "segments": 12,
        "path_stations": [
            {"point": [-1.0, 0.0, 0.0], "radius": 0.18},
            {"point": [-0.3, 0.0, 0.15], "radius": 0.22},
            {"point": [0.35, 0.35, 0.25], "radius": 0.2, "scale_y": 0.8},
            {"point": [1.0, 0.6, 0.5], "radius": 0.14, "roll_degrees": 20.0},
        ],
    }
    normalized = validate_hypothesis(_hypothesis(shape))
    vertices, faces = build_curve_sweep(normalized["shape"])
    assert vertices.shape == (48, 3)
    assert len(faces) == 36
    for face in faces:
        points = vertices[list(face)]
        area = np.linalg.norm(np.cross(points[1] - points[0], points[2] - points[0]))
        assert area > 1e-8
    command = compile_blender_command(normalized, name="BentSweep")
    assert command["metadata"]["source"] == "modeling_core.curve_sweep"


def test_revolution_rejects_axis_poles_that_would_collapse_quad_rings():
    shape = {
        "family": "profile_revolution",
        "segments": 12,
        "profile": [[0.0, -1.0], [0.4, 1.0]],
    }
    with pytest.raises(ValueError, match="radii must be positive"):
        validate_hypothesis(_hypothesis(shape))


def test_revolution_allows_a_same_height_radius_step_for_a_sharp_shoulder():
    shape = {
        "family": "profile_revolution",
        "segments": 12,
        "profile": [[0.25, -1.0], [0.45, 0.0], [0.3, 0.0], [0.3, 1.0]],
    }
    normalized = validate_hypothesis(_hypothesis(shape))
    vertices, faces = build_profile_revolution(normalized["shape"])
    assert vertices.shape == (48, 3)
    assert len(faces) == 36


def test_curve_sweep_rejects_a_zero_centered_tangent():
    shape = {
        "family": "curve_sweep",
        "segments": 12,
        "path_stations": [
            {"point": [0.0, 0.0, 0.0], "radius": 0.2},
            {"point": [1.0, 0.0, 0.0], "radius": 0.2},
            {"point": [0.0, 0.0, 0.0], "radius": 0.2},
        ],
    }
    with pytest.raises(ValueError, match="tangents must be non-zero"):
        validate_hypothesis(_hypothesis(shape))


def test_profile_extrusion_still_rejects_reversed_depth_stations():
    shape = {
        "family": "profile_extrusion",
        "profile": [[-0.4, -0.5], [0.4, -0.5], [0.4, 0.5], [-0.4, 0.5]],
        "depth_stations": [{"y": 0.2}, {"y": -0.2}],
    }
    with pytest.raises(ValueError, match="strictly increasing"):
        validate_hypothesis(_hypothesis(shape))


def _square_ring_shape():
    return {
        "family": "profile_ring_extrusion",
        "outer_profile": [[-0.9, -0.9], [0.9, -0.9], [0.9, 0.9], [-0.9, 0.9]],
        "inner_profile": [[-0.35, -0.35], [0.35, -0.35], [0.35, 0.35], [-0.35, 0.35]],
        "depth_stations": [{"y": -0.12}, {"y": 0.12}],
    }


def test_ring_extrusion_builds_a_closed_manifold_all_quad_through_hole():
    normalized = validate_hypothesis(_hypothesis(_square_ring_shape()))
    vertices, faces = build_profile_ring_extrusion(normalized["shape"])
    assert vertices.shape == (16, 3)
    assert len(faces) == 16
    edge_uses = {}
    for face in faces:
        assert len(face) == 4
        for index in range(4):
            edge = tuple(sorted((face[index], face[(index + 1) % 4])))
            edge_uses[edge] = edge_uses.get(edge, 0) + 1
    assert set(edge_uses.values()) == {2}
    mask = render_silhouette(vertices, faces, normalized["views"][0])
    assert mask[48, 48] == 0
    command = compile_blender_command(normalized, name="GuardOpening")
    assert command["metadata"]["end_caps"] == "CLOSED_ANNULAR_CAPS"


def test_open_profile_extrusion_axial_view_is_filled_as_an_intended_volume():
    shape = {
        "family": "profile_extrusion",
        "profile": [[-0.9, -0.9], [0.9, -0.9], [0.9, 0.9], [-0.9, 0.9]],
        "depth_stations": [{"y": -0.12}, {"y": 0.12}],
    }
    normalized = validate_hypothesis(_hypothesis(shape))
    vertices, faces = build_profile_extrusion(normalized["shape"])
    mask = render_silhouette(vertices, faces, normalized["views"][0])
    assert mask[48, 48] == 1


def test_negative_space_evidence_selects_ring_family_over_solid_extrusion():
    ring = _hypothesis(_square_ring_shape())
    ring["candidate_id"] = "ring"
    ring["variables"] = [{"pointer": "/shape/scale_x", "bounds": [0.9, 1.1]}]
    normalized = validate_hypothesis(ring)
    vertices, faces = build_profile_ring_extrusion(normalized["shape"])
    reference = render_silhouette(vertices, faces, normalized["views"][0])
    solid = _hypothesis({
        "family": "profile_extrusion",
        "profile": _square_ring_shape()["outer_profile"],
        "depth_stations": [{"y": -0.12}, {"y": 0.12}],
    })
    solid["candidate_id"] = "solid"
    solid["variables"] = [{"pointer": "/shape/scale_x", "bounds": [0.9, 1.1]}]
    result = select_shape_family([solid, ring], {"fixture": reference}, seed=4, maxiter=5, popsize=4)
    assert result["selected_family"] == "profile_ring_extrusion"
    solid_result = next(item for item in result["candidates"] if item["candidate_id"] == "solid")
    assert solid_result["compatible"] is False
    assert any("negative-space" in issue for issue in solid_result["issues"])


def test_profile_sweep_bends_a_non_circular_outline_with_open_continuity_ports():
    shape = {
        "family": "profile_sweep",
        "profile": [[-0.3, -0.12], [0.3, -0.12], [0.3, 0.12], [-0.3, 0.12]],
        "path_stations": [
            {"point": [-1.0, 0.0, 0.0]},
            {"point": [-0.3, 0.0, 0.15], "scale_u": 0.9},
            {"point": [0.4, 0.25, 0.35], "roll_degrees": 12.0},
            {"point": [1.0, 0.55, 0.6], "scale_v": 0.75},
        ],
    }
    normalized = validate_hypothesis(_hypothesis(shape))
    vertices, faces = build_profile_sweep(normalized["shape"])
    assert vertices.shape == (16, 3)
    assert len(faces) == 12
    assert shape_boundary_ports(normalized["shape"]) == {
        "start": [0, 1, 2, 3],
        "end": [12, 13, 14, 15],
    }
    command = compile_blender_command(normalized, name="BentProfile")
    assert command["metadata"]["source"] == "modeling_core.profile_sweep"


def test_ring_extrusion_rejects_an_inner_profile_outside_the_outer_profile():
    shape = _square_ring_shape()
    shape["inner_profile"] = [[-0.3, -0.3], [1.1, -0.3], [1.1, 0.3], [-0.3, 0.3]]
    with pytest.raises(ValueError, match="strictly inside"):
        validate_hypothesis(_hypothesis(shape))


def test_outline_profile_rejects_nonadjacent_edge_touching():
    shape = {
        "family": "profile_extrusion",
        "profile": [[-1.0, -1.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, -1.0]],
        "depth_stations": [{"y": -0.1}, {"y": 0.1}],
    }
    with pytest.raises(ValueError, match="simple non-self-intersecting"):
        validate_hypothesis(_hypothesis(shape))


def test_ring_extrusion_rejects_correspondence_that_leaves_concave_material():
    shape = {
        "family": "profile_ring_extrusion",
        "outer_profile": [[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [0.2, 0.2], [-1.0, 1.0]],
        "inner_profile": [
            [-0.4167422923, -0.5762007589],
            [-0.2247301089, -0.5140332750],
            [-0.6201818852, -0.2180907826],
            [0.4015460517, 0.2605428218],
            [0.2181951230, -0.4336861892],
        ],
        "depth_stations": [{"y": -0.1}, {"y": 0.1}],
    }
    with pytest.raises(ValueError, match="correspondence"):
        validate_hypothesis(_hypothesis(shape))
