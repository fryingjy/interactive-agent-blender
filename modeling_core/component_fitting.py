"""Fit and compete generic 3D shape families independently for bundled components."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .compiler import compile_blender_command
from .selection import select_shape_family


def _component_masks(bundle: dict[str, Any], component_id: str) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    masks = {}
    solver_views = []
    for view in bundle.get("views", []):
        component_record = view.get("component_evidence") or {}
        observation = component_record.get("observations", {}).get(component_id)
        if observation is None:
            continue
        solver_view = view.get("solver_view")
        if not isinstance(solver_view, dict):
            raise ValueError(f"{component_id}: view {view.get('view_id')} has no solver camera")
        label_record = component_record.get("label_map", {})
        label_path = Path(label_record.get("path", ""))
        if not label_path.is_file() or hashlib.sha256(label_path.read_bytes()).hexdigest() != label_record.get("sha256"):
            raise ValueError(f"{component_id}: component label map is stale or missing")
        labels = cv2.imread(str(label_path), cv2.IMREAD_GRAYSCALE)
        if labels is None:
            raise ValueError(f"{component_id}: component label map is not decodable")
        label = observation.get("label")
        if not isinstance(label, int) or isinstance(label, bool) or not 1 <= label <= 255:
            raise ValueError(f"{component_id}: component observation has no valid label")
        mask = labels == label
        expected = (solver_view["image_size"][1], solver_view["image_size"][0])
        if mask.shape != expected or not mask.any():
            raise ValueError(f"{component_id}: component mask is empty or does not match its solver view")
        masks[view["view_id"]] = mask
        solver_views.append(copy.deepcopy(solver_view))
    if len(masks) < 2:
        raise ValueError(f"{component_id}: component family fitting requires at least two registered views")
    return masks, solver_views


def fit_component_families(
    bundle: dict[str, Any],
    assembly_hypotheses: dict[str, Any],
    component_candidates: dict[str, list[dict[str, Any]]],
    *,
    resolved_assembly: dict[str, Any] | None = None,
    minimum_loss_margin: float = 0.02,
    seed: int = 0,
    maxiter: int = 20,
    popsize: int = 6,
) -> dict[str, Any]:
    """Fit every component against its own per-view labels using shared fixed cameras."""
    if bundle.get("record_type") != "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE" or not bundle.get("accepted_for_shape_solving"):
        raise ValueError("component fitting requires an accepted multiview evidence bundle")
    if assembly_hypotheses.get("record_type") != "ASSEMBLY_HYPOTHESIS_SET":
        raise ValueError("component fitting requires an assembly hypothesis set")
    if bundle.get("target_id") != assembly_hypotheses.get("target_id"):
        raise ValueError("bundle and assembly hypotheses target different assets")
    if assembly_hypotheses.get("target_variant") not in {None, bundle.get("target_variant")}:
        raise ValueError("bundle and assembly hypotheses target different variants")
    if not 0.0 <= minimum_loss_margin <= 1.0:
        raise ValueError("minimum_loss_margin must be in [0, 1]")
    components = {item["component_id"]: item for item in assembly_hypotheses.get("components", [])}
    if set(component_candidates) != set(components):
        raise ValueError("candidate sets must exactly match assembly components")

    reports = {}
    for component_index, (component_id, component) in enumerate(components.items()):
        candidates = component_candidates[component_id]
        if not isinstance(candidates, list) or len(candidates) < 2:
            raise ValueError(f"{component_id}: at least two executable family candidates are required")
        allowed = {item["family"] for item in component.get("representation_candidates", [])}
        candidate_families = [candidate.get("shape", {}).get("family") for candidate in candidates]
        if len(candidate_families) != len(set(candidate_families)):
            raise ValueError(f"{component_id}: candidates must use distinct shape families")
        if any(family not in allowed for family in candidate_families):
            raise ValueError(f"{component_id}: executable candidate is not declared by the assembly hypothesis")
        masks, solver_views = _component_masks(bundle, component_id)
        normalized_candidates = []
        for candidate in candidates:
            normalized = copy.deepcopy(candidate)
            if any(str(variable.get("pointer", "")).startswith("/views") for variable in normalized.get("variables", [])):
                raise ValueError(f"{component_id}: family competition cannot optimize shared camera parameters")
            normalized["views"] = copy.deepcopy(solver_views)
            normalized_candidates.append(normalized)
        selection = select_shape_family(
            normalized_candidates,
            masks,
            seed=seed + component_index * len(candidates),
            maxiter=maxiter,
            popsize=popsize,
        )
        compatible = sorted(
            (item for item in selection["candidates"] if item["compatible"]),
            key=lambda item: (item["mean_view_loss"], item["candidate_id"]),
        )
        margin = None
        ambiguous = False
        if len(compatible) > 1:
            margin = compatible[1]["mean_view_loss"] - compatible[0]["mean_view_loss"]
            ambiguous = margin < minimum_loss_margin
        if ambiguous:
            selection = {
                **selection,
                "selected_candidate_id": None,
                "selected_family": None,
                "selected_result": None,
                "pass": False,
            }
        reports[component_id] = {
            "status": "SELECTED" if selection["pass"] else "AMBIGUOUS_OR_INCOMPATIBLE",
            "loss_margin": margin,
            "minimum_loss_margin": minimum_loss_margin,
            "selection": selection,
        }

    all_selected = all(item["status"] == "SELECTED" for item in reports.values())
    single_component = len(components) == 1
    graph_ready = single_component
    if not single_component and resolved_assembly:
        expected_pairs = {item["pair_id"] for item in assembly_hypotheses.get("relationship_hypotheses", [])}
        selected = resolved_assembly.get("selected_relationships", [])
        selected_pairs = {item.get("pair_id") for item in selected}
        policies_valid = all(item.get("construction_policy") in {"CONTINUOUS_MESH", "SEPARATE_COMPONENTS"} for item in selected)
        graph_ready = bool(
            resolved_assembly.get("record_type") == "RESOLVED_ASSEMBLY_HYPOTHESES"
            and resolved_assembly.get("ready_for_component_graph")
            and resolved_assembly.get("target_id") == bundle.get("target_id")
            and resolved_assembly.get("target_variant") in {None, bundle.get("target_variant")}
            and expected_pairs
            and selected_pairs == expected_pairs
            and len(selected) == len(expected_pairs)
            and policies_valid
        )
    return {
        "schema_version": 1,
        "record_type": "COMPONENT_FAMILY_SELECTION_SET",
        "target_id": bundle.get("target_id"),
        "target_variant": bundle.get("target_variant"),
        "components": reports,
        "assembly_resolution": copy.deepcopy(resolved_assembly),
        "all_components_selected": all_selected,
        "assembly_graph_resolved": graph_ready,
        "ready_for_compilation": all_selected and graph_ready,
        "claim_boundary": "Each selected family fits visible per-component masks under fixed shared cameras. Hidden geometry, interpenetration, shared-cage continuity, and final topology remain separate checks.",
    }


def compile_component_assembly(
    selection_set: dict[str, Any],
    *,
    object_prefix: str = "Blockout_",
) -> dict[str, Any]:
    """Compile a fully selected separate-object assembly into typed commands.

    Continuous relationships deliberately fail until a true shared-cage compiler can preserve their
    topology.  Compiling independently fitted meshes and joining them would violate the decision.
    """
    if selection_set.get("record_type") != "COMPONENT_FAMILY_SELECTION_SET" or not selection_set.get("ready_for_compilation"):
        raise ValueError("component assembly is not ready for compilation")
    resolution = selection_set.get("assembly_resolution")
    relationships = resolution.get("selected_relationships", []) if isinstance(resolution, dict) else []
    unsupported = [item.get("hypothesis_id") for item in relationships if item.get("construction_policy") not in {"CONTINUOUS_MESH", "SEPARATE_COMPONENTS"}]
    if unsupported:
        raise ValueError(f"unsupported assembly construction policies: {unsupported}")
    continuous = [item["hypothesis_id"] for item in relationships if item.get("construction_policy") == "CONTINUOUS_MESH"]
    if continuous:
        raise ValueError(f"shared-cage compilation is not implemented for continuous relationships: {continuous}")
    commands = []
    object_map = {}
    for component_id, report in selection_set["components"].items():
        selected = report["selection"].get("selected_result")
        if selected is None or not selected.get("family_compatible"):
            raise ValueError(f"component {component_id!r} has no compatible fitted result")
        name = object_prefix + "".join(character if character.isalnum() or character == "_" else "_" for character in component_id)
        command = compile_blender_command(selected["hypothesis"], name=name)
        command["metadata"]["component_id"] = component_id
        command["metadata"]["assembly_policy"] = "SEPARATE_COMPONENT"
        commands.append(command)
        object_map[component_id] = name
    if len(set(object_map.values())) != len(object_map):
        raise ValueError("sanitized component ids collide as Blender object names")
    return {
        "schema_version": 1,
        "record_type": "COMPILED_COMPONENT_ASSEMBLY",
        "target_id": selection_set.get("target_id"),
        "object_map": object_map,
        "command_sequence": commands,
        "modifiers_applied": False,
        "claim_boundary": "Commands create separately fitted editable cages. They do not apply modifiers or claim resolved shared topology.",
    }
