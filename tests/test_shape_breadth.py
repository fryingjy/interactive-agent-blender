import numpy as np
import pytest

from modeling_core import (
    build_curve_sweep,
    build_profile_revolution,
    compile_blender_command,
    fit_hypothesis,
    render_silhouette,
    shape_boundary_ports,
    validate_hypothesis,
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
