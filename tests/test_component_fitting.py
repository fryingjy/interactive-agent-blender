import copy
import hashlib
from pathlib import Path

import cv2
import numpy as np

from modeling_core import (
    build_profile_extrusion,
    build_section_loft,
    compile_component_assembly,
    fit_component_families,
    render_silhouette,
)


VIEWS = [
    {"id": "front", "projection": "orthographic", "image_size": [96, 96], "yaw_degrees": 0, "pitch_degrees": 0, "roll_degrees": 0, "world_scale": 3.0, "offset_x": 0, "offset_y": 0},
    {"id": "oblique", "projection": "orthographic", "image_size": [96, 96], "yaw_degrees": 0, "pitch_degrees": 0, "roll_degrees": 38, "world_scale": 3.0, "offset_x": 0, "offset_y": 0},
]


def _loft(translate_x):
    return {
        "family": "section_loft", "segments": 12, "cross_section": "box",
        "scale_x": 1.0, "scale_y": 1.0, "scale_z": 1.0,
        "translate_x": translate_x, "translate_y": 0.0, "translate_z": 0.0,
        "stations": [
            {"z": -0.55, "half_width": 0.27, "half_depth": 0.18, "power": 4.0},
            {"z": 0.55, "half_width": 0.34, "half_depth": 0.23, "power": 4.0},
        ],
    }


def _profile(translate_x):
    return {
        "family": "profile_extrusion", "scale_x": 1.0, "scale_y": 1.0, "scale_z": 1.0,
        "translate_x": translate_x, "translate_y": 0.0, "translate_z": 0.0,
        "profile": [[-0.16, -0.46], [0.16, -0.46], [0.23, 0.12], [0.0, 0.52], [-0.23, 0.12]],
        "depth_stations": [{"y": -0.09}, {"y": 0.09}],
    }


def _hypothesis(candidate_id, shape, *, translate_bounds):
    return {
        "schema_version": 1,
        "candidate_id": candidate_id,
        "shape": shape,
        "views": [{}],
        "variables": [{"pointer": "/shape/translate_x", "bounds": list(translate_bounds)}],
        "acceptance": {"max_mean_view_loss": 0.2, "max_each_view_loss": 0.26, "require_hole_count_match": True},
    }


def _fixture(tmp_path: Path):
    truths = {"body": _loft(-0.72), "handle": _profile(0.72)}
    labels_by_view = {}
    view_records = []
    for view in VIEWS:
        labels = np.zeros((96, 96), dtype=np.uint8)
        for label, (component_id, shape) in enumerate(truths.items(), 1):
            builder = build_section_loft if shape["family"] == "section_loft" else build_profile_extrusion
            vertices, faces = builder(shape)
            mask = render_silhouette(vertices, faces, view)
            labels[mask] = label
        label_path = tmp_path / f"{view['id']}-labels.png"
        cv2.imwrite(str(label_path), labels)
        label_hash = hashlib.sha256(label_path.read_bytes()).hexdigest()
        component_record = {
            "record_type": "REFERENCE_COMPONENT_EVIDENCE",
            "label_map": {"path": str(label_path), "sha256": label_hash},
            "observations": {"body": {"label": 1}, "handle": {"label": 2}},
            "visible_adjacency": [],
        }
        view_records.append({"view_id": view["id"], "solver_view": copy.deepcopy(view), "component_evidence": component_record})
        labels_by_view[view["id"]] = labels
    bundle = {
        "record_type": "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE",
        "target_id": "two-part-fixture",
        "target_variant": "v1",
        "accepted_for_shape_solving": True,
        "component_support": {"body": ["front", "oblique"], "handle": ["front", "oblique"]},
        "views": view_records,
    }
    assembly = {
        "record_type": "ASSEMBLY_HYPOTHESIS_SET",
        "target_id": "two-part-fixture",
        "target_variant": "v1",
        "components": [
            {"component_id": "body", "representation_candidates": [{"family": "section_loft"}, {"family": "profile_extrusion"}]},
            {"component_id": "handle", "representation_candidates": [{"family": "profile_extrusion"}, {"family": "section_loft"}]},
        ],
        "relationship_hypotheses": [{"pair_id": "body::handle"}],
    }
    resolved = {
        "record_type": "RESOLVED_ASSEMBLY_HYPOTHESES",
        "target_id": "two-part-fixture",
        "target_variant": "v1",
        "ready_for_component_graph": True,
        "selected_relationships": [{
            "pair_id": "body::handle",
            "hypothesis_id": "body::handle:separate",
            "construction_policy": "SEPARATE_COMPONENTS",
        }],
    }
    candidates = {
        "body": [
            _hypothesis("body-loft", _loft(-0.45), translate_bounds=(-0.9, -0.3)),
            _hypothesis("body-profile", _profile(-0.45), translate_bounds=(-0.9, -0.3)),
        ],
        "handle": [
            _hypothesis("handle-profile", _profile(0.45), translate_bounds=(0.3, 0.9)),
            _hypothesis("handle-loft", _loft(0.45), translate_bounds=(0.3, 0.9)),
        ],
    }
    return bundle, assembly, resolved, candidates, truths, labels_by_view


def test_multicomponent_family_fitting_uses_fixed_cameras_and_recovers_placement(tmp_path: Path):
    bundle, assembly, resolved, candidates, truths, _labels = _fixture(tmp_path)
    result = fit_component_families(
        bundle, assembly, candidates, resolved_assembly=resolved,
        seed=7, maxiter=10, popsize=5,
    )
    assert result["ready_for_compilation"] is True
    assert result["components"]["body"]["selection"]["selected_family"] == "section_loft"
    assert result["components"]["handle"]["selection"]["selected_family"] == "profile_extrusion"
    for component_id, truth in truths.items():
        fitted = result["components"][component_id]["selection"]["selected_result"]["hypothesis"]["shape"]
        assert abs(fitted["translate_x"] - truth["translate_x"]) < 0.08


def test_separate_assembly_compiles_to_distinct_typed_objects(tmp_path: Path):
    bundle, assembly, resolved, candidates, _truths, _labels = _fixture(tmp_path)
    selection = fit_component_families(
        bundle, assembly, candidates, resolved_assembly=resolved,
        seed=7, maxiter=8, popsize=5,
    )
    compiled = compile_component_assembly(selection, object_prefix="Fixture_")
    assert compiled["object_map"] == {"body": "Fixture_body", "handle": "Fixture_handle"}
    assert len(compiled["command_sequence"]) == 2
    assert all(item["command"] == "create_authored_quad_mesh" for item in compiled["command_sequence"])
    assert all(item["metadata"]["assembly_policy"] == "SEPARATE_COMPONENT" for item in compiled["command_sequence"])
    assert compiled["modifiers_applied"] is False


def test_continuous_relationship_fails_instead_of_joining_fitted_components(tmp_path: Path):
    bundle, assembly, resolved, candidates, _truths, _labels = _fixture(tmp_path)
    resolved["selected_relationships"][0] = {
        "pair_id": "body::handle",
        "hypothesis_id": "body::handle:continuous",
        "construction_policy": "CONTINUOUS_MESH",
    }
    selection = fit_component_families(
        bundle, assembly, candidates, resolved_assembly=resolved,
        seed=7, maxiter=8, popsize=5,
    )
    try:
        compile_component_assembly(selection)
    except ValueError as error:
        assert "shared-cage compilation is not implemented" in str(error)
    else:
        raise AssertionError("continuous components were incorrectly compiled as separate objects")


def test_candidate_cannot_optimize_shared_camera_to_win(tmp_path: Path):
    bundle, assembly, resolved, candidates, _truths, _labels = _fixture(tmp_path)
    candidates["body"][0]["variables"].append({"pointer": "/views/0/offset_x", "bounds": [-0.2, 0.2]})
    try:
        fit_component_families(bundle, assembly, candidates, resolved_assembly=resolved)
    except ValueError as error:
        assert "cannot optimize shared camera" in str(error)
    else:
        raise AssertionError("family candidate was allowed to alter shared camera evidence")


def test_incomplete_forged_graph_resolution_cannot_authorize_compilation(tmp_path: Path):
    bundle, assembly, resolved, candidates, _truths, _labels = _fixture(tmp_path)
    resolved["selected_relationships"] = []
    result = fit_component_families(
        bundle, assembly, candidates, resolved_assembly=resolved,
        seed=7, maxiter=8, popsize=5,
    )
    assert result["all_components_selected"] is True
    assert result["assembly_graph_resolved"] is False
    assert result["ready_for_compilation"] is False
