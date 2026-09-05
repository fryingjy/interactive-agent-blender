"""Contracts for turning fitted shape proxies into editable modeling decisions."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any


def propose_feature_edges(
    edges: list[dict[str, Any]], *, angle_degrees: float, rationale: str,
    preserve_ids: list[int] | None = None, smooth_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Propose crease candidates from inspected edges, with explicit intent overrides.

    Angles measure existing geometry, not artistic intent. Boundary/invalid edges
    remain unresolved and this function never mutates Blender.
    """
    if not math.isfinite(angle_degrees) or not 0 < angle_degrees < 180:
        raise ValueError("angle_degrees must be finite and between 0 and 180")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("feature proposal requires a modeling rationale")
    ids = [edge.get("agent_id") for edge in edges]
    if not edges or any(type(value) is not int or value <= 0 for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("inspected edges require unique positive persistent IDs")
    preserve, smooth = set(preserve_ids or []), set(smooth_ids or [])
    if any(type(value) is not int for value in preserve | smooth) or (preserve | smooth) - set(ids):
        raise ValueError("intent overrides must resolve to inspected persistent IDs")
    if preserve & smooth:
        raise ValueError("an edge cannot have conflicting preserve and smooth intent")
    selected, unresolved, decisions = [], [], []
    for edge in sorted(edges, key=lambda item: item["agent_id"]):
        edge_id, angle = edge["agent_id"], edge.get("face_angle_radians")
        valid = isinstance(angle, (int, float)) and not isinstance(angle, bool) and math.isfinite(angle) and 0 <= angle <= math.pi + 1e-5
        if edge.get("is_boundary") is not False or not valid:
            unresolved.append(edge_id)
            reason = "REQUIRES_TOPOLOGY_REVIEW"
        elif edge_id in smooth:
            reason = "EXPLICIT_SMOOTH_INTENT"
        elif edge_id in preserve:
            selected.append(edge_id)
            reason = "EXPLICIT_PRESERVE_INTENT"
        elif math.degrees(angle) >= angle_degrees:
            selected.append(edge_id)
            reason = "ANGLE_CANDIDATE"
        else:
            reason = "BELOW_ANGLE_THRESHOLD"
        decisions.append({"edge_id": edge_id, "reason": reason})
    return {
        "schema_version": 1, "record_type": "FEATURE_EDGE_PROPOSAL",
        "source_edges_sha256": selection_sha256({"edges": sorted(edges, key=lambda item: item["agent_id"])}),
        "angle_degrees": angle_degrees, "rationale": rationale,
        "candidate_edge_ids": selected, "unresolved_edge_ids": unresolved,
        "decisions": decisions, "mutation_authorized": False,
        "claim_boundary": "Geometric candidates require surface-intent review and current-state ID validation before applying crease or bevel. An angle is not proof of desired sharpness.",
    }


CONSTRUCTION_METHODS = {
    "BOX_SUBD_CAGE",
    "CONNECTED_PROFILE_CAGE",
    "RADIAL_PROFILE_CAGE",
    "CURVE_SWEEP_CAGE",
    "BOOLEAN_SUPPORT_CAGE",
    "HYBRID_FEATURE_CAGE",
}
FEATURE_OPERATIONS = {
    "EXTRUDE",
    "INSET",
    "LOOP_CUT",
    "BRIDGE_LOOPS",
    "KNIFE_OR_CONNECT",
    "MIRROR",
    "SOLIDIFY",
    "BOOLEAN",
    "CREASE",
    "SUPPORT_LOOP",
    "BEVEL_WEIGHT",
    "BEVEL_MODIFIER",
    "SHADE_FLAT",
    "SMOOTH_BY_ANGLE",
    "SUBDIVISION",
}
REQUIRED_REVIEW_CRITERIA = {
    "reference_fidelity",
    "major_form_and_proportion",
    "depth_and_negative_space",
    "base_cage_editability",
    "evaluated_surface_and_highlight_flow",
    "edge_and_shading_intent",
}


def selection_sha256(selection_set: dict[str, Any]) -> str:
    encoded = json.dumps(selection_set, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _selected_family(selection_set: dict[str, Any], component_id: str) -> str:
    report = selection_set["components"][component_id]
    result = report.get("selection", {}).get("selected_result")
    if not isinstance(result, dict) or result.get("family_compatible") is not True:
        raise ValueError(f"component {component_id!r} has no compatible fitted proxy")
    family = result.get("hypothesis", {}).get("shape", {}).get("family")
    if not isinstance(family, str):
        raise ValueError(f"component {component_id!r} fitted proxy has no family")
    return family


def validate_editable_construction_plan(
    raw: dict[str, Any],
    selection_set: dict[str, Any],
) -> dict[str, Any]:
    """Validate the explicit bridge between shape fitting and Blender authoring.

    A fitted proxy constrains form; it is not itself proof of an editable cage.
    This contract requires every component to declare feature, topology, modifier,
    surface, evidence, and rollback intent before production realization begins.
    """
    if selection_set.get("record_type") != "COMPONENT_FAMILY_SELECTION_SET" or not selection_set.get("ready_for_compilation"):
        raise ValueError("construction planning requires a compatible fitted component selection")
    if raw.get("schema_version") != 1 or raw.get("record_type") != "EDITABLE_CONSTRUCTION_PLAN":
        raise ValueError("construction plan must be an EDITABLE_CONSTRUCTION_PLAN schema-version 1 record")
    result = copy.deepcopy(raw)
    for key in ("target_id", "target_variant"):
        if result.get(key) != selection_set.get(key):
            raise ValueError(f"construction plan {key} does not match its fitted selection")
    expected_hash = selection_sha256(selection_set)
    if result.get("source_selection_sha256") != expected_hash:
        raise ValueError("construction plan is not hash-bound to its fitted selection")
    plans = result.get("components")
    if not isinstance(plans, list):
        raise ValueError("construction plan components must be a list")
    expected_ids = set(selection_set.get("components", {}))
    observed_ids = [item.get("component_id") for item in plans if isinstance(item, dict)]
    if len(observed_ids) != len(plans) or set(observed_ids) != expected_ids or len(observed_ids) != len(set(observed_ids)):
        raise ValueError("construction plan must cover each fitted component exactly once")
    unresolved = []
    for plan in plans:
        component_id = plan["component_id"]
        family = _selected_family(selection_set, component_id)
        if plan.get("source_proxy_family") != family:
            raise ValueError(f"component {component_id!r} construction plan cites the wrong proxy family")
        if plan.get("construction_method") not in CONSTRUCTION_METHODS:
            raise ValueError(f"component {component_id!r} requires an editable construction method")
        if plan.get("object_policy") not in {"CONNECTED_CAGE", "SEPARATE_ASSEMBLY"}:
            raise ValueError(f"component {component_id!r} requires an explicit object policy")
        features = plan.get("feature_sequence")
        if not isinstance(features, list) or not features:
            raise ValueError(f"component {component_id!r} requires a non-empty feature sequence")
        feature_ids = [feature.get("feature_id") for feature in features if isinstance(feature, dict)]
        if len(feature_ids) != len(features) or any(not isinstance(value, str) or not value.strip() for value in feature_ids) or len(feature_ids) != len(set(feature_ids)):
            raise ValueError(f"component {component_id!r} feature ids must be unique non-empty strings")
        for feature in features:
            if feature.get("operation") not in FEATURE_OPERATIONS:
                raise ValueError(f"component {component_id!r} feature {feature['feature_id']!r} has an unsupported operation")
            for field in ("rationale", "expected_visual_effect", "rollback_trigger"):
                if not isinstance(feature.get(field), str) or not feature[field].strip():
                    raise ValueError(f"component {component_id!r} feature {feature['feature_id']!r} requires {field}")
            evidence = feature.get("evidence_basis")
            if not isinstance(evidence, list) or not evidence:
                raise ValueError(f"component {component_id!r} feature {feature['feature_id']!r} requires evidence")
            for item in evidence:
                if not isinstance(item, dict) or item.get("status") not in {"OBSERVED", "INFERRED"}:
                    raise ValueError("feature evidence must distinguish OBSERVED from INFERRED")
                if item["status"] == "OBSERVED" and not item.get("view_id"):
                    raise ValueError("observed feature evidence requires a view_id")
                if not isinstance(item.get("basis"), str) or not item["basis"].strip():
                    raise ValueError("feature evidence requires a concrete basis")
        surface = plan.get("surface_strategy")
        if not isinstance(surface, dict) or surface.get("shading") not in {"FLAT", "SMOOTH_BY_ANGLE", "SUBD"}:
            raise ValueError(f"component {component_id!r} requires an explicit surface strategy")
        if surface.get("edge_control") not in {"NONE", "CREASE", "SUPPORT_LOOPS", "BEVEL_WEIGHT", "BEVEL_MODIFIER", "MIXED"}:
            raise ValueError(f"component {component_id!r} requires explicit edge control")
        if not isinstance(surface.get("rationale"), str) or not surface["rationale"].strip():
            raise ValueError(f"component {component_id!r} surface strategy requires rationale")
        modifiers = surface.get("live_modifiers", [])
        if not isinstance(modifiers, list) or any(not isinstance(item, dict) or not item.get("type") or item.get("apply") is not False for item in modifiers):
            raise ValueError(f"component {component_id!r} modifiers must be named and explicitly remain live")
        criteria = set(plan.get("review_criteria", []))
        missing = sorted(REQUIRED_REVIEW_CRITERIA - criteria)
        if missing:
            raise ValueError(f"component {component_id!r} leaves review criteria uncovered: {missing}")
        component_unresolved = plan.get("unresolved_decisions", [])
        if not isinstance(component_unresolved, list) or any(not isinstance(item, str) or not item.strip() for item in component_unresolved):
            raise ValueError(f"component {component_id!r} unresolved decisions must be strings")
        unresolved.extend(f"{component_id}: {item}" for item in component_unresolved)
    result["source_selection_sha256"] = expected_hash
    result["unresolved_decisions"] = unresolved
    result["ready_for_blender_realization"] = not unresolved
    result["status"] = "READY" if not unresolved else "REQUIRES_DECISIONS"
    result["claim_boundary"] = (
        "This validates construction intent and evidence coverage only. It does not prove that the cage, modifiers, "
        "surface, or reference match has been realized correctly in Blender."
    )
    return result
