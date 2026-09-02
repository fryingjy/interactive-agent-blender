"""Fit and compete generic 3D shape families independently for bundled components."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .compiler import compile_blender_command
from .continuity import build_continuous_cage
from .hypothesis import validate_hypothesis
from .selection import select_shape_family


class _ComponentGroups:
    def __init__(self, component_ids: list[str]):
        self.parent = {component_id: component_id for component_id in component_ids}

    def find(self, component_id: str) -> str:
        parent = self.parent[component_id]
        if parent != component_id:
            self.parent[component_id] = self.find(parent)
        return self.parent[component_id]

    def union(self, first: str, second: str) -> None:
        first_root, second_root = self.find(first), self.find(second)
        if first_root != second_root:
            self.parent[max(first_root, second_root)] = min(first_root, second_root)


def _relationship_components(relationship: dict[str, Any], known: set[str]) -> list[str]:
    components = relationship.get("components")
    if components is None:
        components = str(relationship.get("pair_id") or "").split("::")
    if not isinstance(components, list) or len(components) != 2 or len(set(components)) != 2:
        raise ValueError(f"relationship {relationship.get('pair_id')!r} must identify exactly two components")
    if not set(components) <= known or "::".join(sorted(components)) != relationship.get("pair_id"):
        raise ValueError(f"relationship {relationship.get('pair_id')!r} has inconsistent component ids")
    return components


def _object_name(prefix: str, component_ids: list[str]) -> str:
    identifier = "__".join(sorted(component_ids))
    return prefix + "".join(character if character.isalnum() or character == "_" else "_" for character in identifier)


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
    continuity_interfaces: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compile resolved continuous groups and separate assemblies into typed commands."""
    if selection_set.get("record_type") != "COMPONENT_FAMILY_SELECTION_SET" or not selection_set.get("ready_for_compilation"):
        raise ValueError("component assembly is not ready for compilation")
    resolution = selection_set.get("assembly_resolution")
    relationships = resolution.get("selected_relationships", []) if isinstance(resolution, dict) else []
    unsupported = [item.get("hypothesis_id") for item in relationships if item.get("construction_policy") not in {"CONTINUOUS_MESH", "SEPARATE_COMPONENTS"}]
    if unsupported:
        raise ValueError(f"unsupported assembly construction policies: {unsupported}")
    component_reports = selection_set.get("components", {})
    component_ids = list(component_reports)
    known_components = set(component_ids)
    selected_shapes = {}
    for component_id, report in component_reports.items():
        selected = report.get("selection", {}).get("selected_result")
        if selected is None or not selected.get("family_compatible"):
            raise ValueError(f"component {component_id!r} has no compatible fitted result")
        selected_shapes[component_id] = validate_hypothesis(selected["hypothesis"])["shape"]

    continuous_relationships = []
    groups = _ComponentGroups(component_ids)
    seen_pairs = set()
    for relationship in relationships:
        components = _relationship_components(relationship, known_components)
        if relationship["pair_id"] in seen_pairs:
            raise ValueError(f"duplicate assembly relationship: {relationship['pair_id']}")
        seen_pairs.add(relationship["pair_id"])
        normalized = {**relationship, "components": components}
        if relationship["construction_policy"] == "CONTINUOUS_MESH":
            continuous_relationships.append(normalized)
            groups.union(*components)
    expected_interfaces = {item["pair_id"] for item in continuous_relationships}
    provided_interfaces = set((continuity_interfaces or {}).keys())
    if provided_interfaces != expected_interfaces:
        raise ValueError("continuity interfaces must exactly match resolved continuous relationship pairs")

    grouped_components: dict[str, list[str]] = {}
    for component_id in component_ids:
        grouped_components.setdefault(groups.find(component_id), []).append(component_id)
    commands = []
    object_map = {}
    group_reports = []
    object_names = set()
    for members in grouped_components.values():
        name = _object_name(object_prefix, members)
        if name in object_names:
            raise ValueError("sanitized component ids collide as Blender object names")
        object_names.add(name)
        if len(members) == 1:
            component_id = members[0]
            selected = component_reports[component_id]["selection"]["selected_result"]
            command = compile_blender_command(selected["hypothesis"], name=name)
            command["metadata"].update({
                "component_id": component_id,
                "component_ids": members,
                "assembly_policy": "SEPARATE_COMPONENT",
            })
            group_report = {"object_name": name, "component_ids": members, "assembly_policy": "SEPARATE_COMPONENT"}
        else:
            member_set = set(members)
            group_relationships = [
                item for item in continuous_relationships if set(item["components"]) <= member_set
            ]
            group_interfaces = {
                item["pair_id"]: continuity_interfaces[item["pair_id"]]
                for item in group_relationships
            }
            cage = build_continuous_cage(
                {component_id: selected_shapes[component_id] for component_id in members},
                group_relationships,
                group_interfaces,
            )
            command = {
                "command": "create_authored_quad_mesh",
                "params": {
                    "name": name,
                    "vertices": cage["vertices"].tolist(),
                    "faces": [list(face) for face in cage["faces"]],
                },
                "metadata": {
                    "source": "modeling_core.continuity",
                    "component_ids": members,
                    "assembly_policy": "CONTINUOUS_GROUP",
                    "connected_components": 1,
                    "all_quad": True,
                    "end_caps": "OPEN_FOR_EXPLICIT_SURFACE_DECISION",
                    "modifiers_applied": False,
                    "interfaces": cage["interfaces"],
                    "topology_stats": cage["stats"],
                },
            }
            group_report = {
                "object_name": name,
                "component_ids": members,
                "assembly_policy": "CONTINUOUS_GROUP",
                "interfaces": cage["interfaces"],
                "topology_stats": cage["stats"],
            }
        commands.append(command)
        group_reports.append(group_report)
        for component_id in members:
            object_map[component_id] = name
    return {
        "schema_version": 1,
        "record_type": "COMPILED_COMPONENT_ASSEMBLY",
        "target_id": selection_set.get("target_id"),
        "object_map": object_map,
        "groups": group_reports,
        "command_sequence": commands,
        "modifiers_applied": False,
        "claim_boundary": "Commands preserve evidence-resolved object boundaries. Continuous groups use explicit equal-cardinality ports to weld or bridge one editable quad cage; arbitrary topology fusion, resampling, branch junctions, hidden surfaces, and final topology remain outside this claim.",
    }
