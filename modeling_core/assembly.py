"""Propose and resolve generic component-assembly interpretations from multiview evidence."""

from __future__ import annotations

from itertools import combinations
from typing import Any


GENERIC_COMPONENT_FAMILIES = {
    "box_poly",
    "profile_extrusion",
    "section_loft",
    "profile_revolution",
    "curve_sweep",
    "boolean_cage",
}
COMPONENT_ROLES = {"primary", "secondary", "tertiary"}


def _pair(first: str, second: str) -> tuple[str, str]:
    return tuple(sorted((first, second)))


def _pair_id(first: str, second: str) -> str:
    return "::".join(_pair(first, second))


def propose_assembly_hypotheses(
    bundle: dict[str, Any],
    component_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create bounded representation and relationship candidates without selecting them.

    Visible adjacency is evidence that two projected regions meet.  It is not evidence that they
    share one editable cage, so every adjacent pair receives both a continuous-transition and a
    separate-assembly interpretation until an independent observation discriminates them.
    """
    if bundle.get("record_type") != "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE" or not bundle.get("accepted_for_shape_solving"):
        raise ValueError("assembly hypotheses require an accepted multiview evidence bundle")
    if not component_specs:
        raise ValueError("component_specs cannot be empty")
    ids = [str(item.get("id") or "").strip() for item in component_specs]
    if any(not identifier for identifier in ids) or len(ids) != len(set(ids)):
        raise ValueError("component ids must be unique and non-empty")
    supported = set(bundle.get("component_support", {}))
    if set(ids) != supported:
        raise ValueError(f"component specs must exactly match bundled components: {sorted(supported)}")

    per_component: dict[str, list[dict[str, Any]]] = {identifier: [] for identifier in ids}
    adjacency_views: dict[tuple[str, str], list[str]] = {}
    for view in bundle.get("views", []):
        view_id = view.get("view_id")
        record = view.get("component_evidence") or {}
        for identifier, observation in record.get("observations", {}).items():
            if identifier in per_component:
                per_component[identifier].append({"view_id": view_id, **observation})
        for relation in record.get("visible_adjacency", []):
            if isinstance(relation, list) and len(relation) == 2 and set(relation) <= set(ids):
                adjacency_views.setdefault(_pair(*relation), []).append(view_id)

    components = []
    for specification, identifier in zip(component_specs, ids):
        role = specification.get("role", "secondary")
        if role not in COMPONENT_ROLES:
            raise ValueError(f"component {identifier!r} has invalid role {role!r}")
        families = specification.get("candidate_families") or ["box_poly", "profile_extrusion", "section_loft"]
        if (
            not isinstance(families, list)
            or len(families) < 2
            or any(family not in GENERIC_COMPONENT_FAMILIES for family in families)
            or len(families) != len(set(families))
        ):
            raise ValueError(f"component {identifier!r} needs at least two unique generic candidate families")
        observations = per_component[identifier]
        if not observations:
            raise ValueError(f"component {identifier!r} has no bound per-view observations")
        aspect_ratios = [item["measurements"]["aspect_ratio_width_over_height"] for item in observations]
        negative_spaces = [item["measurements"]["enclosed_negative_space_count"] for item in observations]
        components.append({
            "component_id": identifier,
            "role": role,
            "supporting_views": [item["view_id"] for item in observations],
            "observed_aspect_ratio_range": [min(aspect_ratios), max(aspect_ratios)],
            "maximum_visible_negative_spaces": max(negative_spaces),
            "representation_candidates": [
                {
                    "family": family,
                    "status": "CANDIDATE",
                    "required_discriminating_evidence": {
                        "box_poly": "planarity, corner, and depth evidence",
                        "profile_extrusion": "outline stability plus a depth profile",
                        "section_loft": "cross-section change along a dominant axis",
                        "profile_revolution": "radial symmetry and axis evidence",
                        "curve_sweep": "path and cross-section evidence",
                        "boolean_cage": "opening/cavity depth and boundary evidence",
                    }[family],
                }
                for family in families
            ],
            "selected_family": None,
        })

    relationship_hypotheses = []
    for first, second in combinations(ids, 2):
        views = sorted(set(adjacency_views.get(_pair(first, second), [])))
        if not views:
            continue
        pair_id = _pair_id(first, second)
        relationship_hypotheses.append({
            "pair_id": pair_id,
            "components": list(_pair(first, second)),
            "visible_adjacency_views": views,
            "disposition": "AMBIGUOUS",
            "selected_hypothesis_id": None,
            "hypotheses": [
                {
                    "hypothesis_id": f"{pair_id}:continuous",
                    "relationship": "transitions_into",
                    "construction_policy": "CONTINUOUS_MESH",
                    "construction_pattern": "shared_editable_cage",
                    "prediction": "no physical seam and continuous surface flow across the boundary",
                },
                {
                    "hypothesis_id": f"{pair_id}:separate",
                    "relationship": "attached_to",
                    "construction_policy": "SEPARATE_COMPONENTS",
                    "construction_pattern": "separate_objects",
                    "prediction": "a seam, occlusion boundary, material break with depth, or independent motion exists",
                },
            ],
            "required_observation": "registered secondary/oblique evidence of seam, surface continuity, separation, or independent motion",
        })
    graph_candidates = []
    if relationship_hypotheses:
        for suffix, candidate_index in (("continuous-bracket", 0), ("separate-bracket", 1)):
            graph_candidates.append({
                "graph_candidate_id": suffix,
                "status": "CANDIDATE",
                "relationships": [relation["hypotheses"][candidate_index] for relation in relationship_hypotheses],
                "scope": "bracketing candidate; mixed edge policies may be selected after evidence",
            })
    single_component = len(relationship_hypotheses) == 0 and len(components) == 1
    return {
        "schema_version": 1,
        "record_type": "ASSEMBLY_HYPOTHESIS_SET",
        "target_id": bundle.get("target_id"),
        "target_variant": bundle.get("target_variant"),
        "source_view_ids": [view.get("view_id") for view in bundle.get("views", [])],
        "source_view_evidence": {
            view.get("view_id"): {
                "source_path": view.get("source_path"),
                "source_sha256": view.get("source_sha256"),
                "mask_path": view.get("mask_path"),
                "mask_sha256": view.get("mask_sha256"),
            }
            for view in bundle.get("views", [])
        },
        "components": components,
        "relationship_hypotheses": relationship_hypotheses,
        "graph_candidates": graph_candidates,
        "assembly_graph_resolved": single_component,
        "component_representations_resolved": False,
        "ready_for_construction": False,
        "disposition": "SINGLE_COMPONENT_REPRESENTATION_UNRESOLVED" if single_component else "REQUIRES_DISCRIMINATING_EVIDENCE",
        "claim_boundary": "Candidates bracket generic component and continuity interpretations. Visible adjacency alone never selects topology or object boundaries.",
    }


def resolve_assembly_hypotheses(
    hypothesis_set: dict[str, Any],
    observations: list[dict[str, Any]],
    *,
    minimum_multiview_support: int = 2,
) -> dict[str, Any]:
    """Resolve relationship candidates from independently recorded view observations."""
    if hypothesis_set.get("record_type") != "ASSEMBLY_HYPOTHESIS_SET":
        raise ValueError("resolver requires an ASSEMBLY_HYPOTHESIS_SET")
    if minimum_multiview_support < 2:
        raise ValueError("minimum_multiview_support must be at least two")
    valid_views = set(hypothesis_set.get("source_view_ids", []))
    view_evidence = hypothesis_set.get("source_view_evidence", {})
    by_pair: dict[str, list[dict[str, Any]]] = {}
    for observation in observations:
        pair_id = str(observation.get("pair_id") or "")
        view_id = str(observation.get("view_id") or "")
        if not pair_id or view_id not in valid_views:
            raise ValueError("assembly observations require a known pair_id and source view_id")
        evidence_path = str(observation.get("evidence_path") or "").strip()
        evidence_sha256 = str(observation.get("evidence_sha256") or "").strip().lower()
        method = str(observation.get("method") or "").strip()
        authorized_hashes = {
            str(view_evidence.get(view_id, {}).get("source_sha256") or "").lower(),
            str(view_evidence.get(view_id, {}).get("mask_sha256") or "").lower(),
        } - {""}
        if not evidence_path or not method or evidence_sha256 not in authorized_hashes:
            raise ValueError("assembly observations require method and evidence bound to the cited source view")
        boolean_fields = (
            "seam_visible",
            "surface_transition_continuous",
            "projected_separation_visible",
            "independent_motion_verified",
        )
        if not any(isinstance(observation.get(field), bool) for field in boolean_fields):
            raise ValueError("assembly observation contains no supported boolean evidence")
        by_pair.setdefault(pair_id, []).append(observation)

    resolved = []
    unresolved = []
    known_pairs = {item["pair_id"] for item in hypothesis_set.get("relationship_hypotheses", [])}
    unknown_pairs = sorted(set(by_pair) - known_pairs)
    if unknown_pairs:
        raise ValueError(f"observations cite unknown component pairs: {unknown_pairs}")
    for relation in hypothesis_set.get("relationship_hypotheses", []):
        pair_id = relation["pair_id"]
        evidence = by_pair.get(pair_id, [])
        continuous_views = {
            item["view_id"] for item in evidence
            if item.get("surface_transition_continuous") is True and item.get("seam_visible") is not True
        }
        separate_views = {
            item["view_id"] for item in evidence
            if item.get("seam_visible") is True or item.get("projected_separation_visible") is True
        }
        motion_verified = any(item.get("independent_motion_verified") is True for item in evidence)
        continuous_supported = len(continuous_views) >= minimum_multiview_support
        separate_supported = motion_verified or len(separate_views) >= minimum_multiview_support
        if continuous_supported and separate_supported:
            status, selected = "CONTRADICTORY_EVIDENCE", None
        elif continuous_supported:
            status, selected = "SELECTED", f"{pair_id}:continuous"
        elif separate_supported:
            status, selected = "SELECTED", f"{pair_id}:separate"
        else:
            status, selected = "INSUFFICIENT_EVIDENCE", None
        item = {
            **relation,
            "disposition": status,
            "selected_hypothesis_id": selected,
            "evidence_summary": {
                "continuous_views": sorted(continuous_views),
                "separate_views": sorted(separate_views),
                "independent_motion_verified": motion_verified,
                "observation_count": len(evidence),
            },
        }
        resolved.append(item)
        if selected is None:
            unresolved.append(pair_id)
    selected_relationships = [
        hypothesis
        for relation in resolved
        for hypothesis in relation["hypotheses"]
        if hypothesis["hypothesis_id"] == relation["selected_hypothesis_id"]
    ]
    ready = not unresolved and bool(resolved)
    return {
        "schema_version": 1,
        "record_type": "RESOLVED_ASSEMBLY_HYPOTHESES",
        "target_id": hypothesis_set.get("target_id"),
        "target_variant": hypothesis_set.get("target_variant"),
        "relationships": resolved,
        "selected_relationships": selected_relationships,
        "selected_graph": {
            "graph_candidate_id": "evidence-resolved-mixed-graph",
            "relationships": selected_relationships,
        } if ready else None,
        "unresolved_pair_ids": unresolved,
        "ready_for_component_graph": ready,
        "component_representations_resolved": False,
        "ready_for_construction": False,
        "disposition": "RESOLVED" if ready else "REQUIRES_MORE_EVIDENCE",
        "claim_boundary": "Resolution chooses component connectivity only. Each component's 3D representation family still requires independent multiview fitting and selection.",
    }
