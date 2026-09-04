"""Pure-Python stage evidence validation shared by Blender runtime and tests."""

from __future__ import annotations

import string
from typing import Any


STAGE_REQUIREMENTS = {
    "REFERENCE_ANALYSIS": (
        "reference_audit",
        "modeling_spec_audit",
        "shape_pipeline_evidence",
    ),
    "PRIMARY_BLOCKOUT": (
        "dimensions_checked", "primary_components_present", "component_coverage",
    ),
    "PROPORTION_SILHOUETTE": (
        "fitted_shape_evidence", "visual_mismatch_ledger", "render_evidence_preflight",
    ),
    "SECONDARY_FORMS": ("secondary_components_present", "placement_checked"),
    "TOPOLOGY_SURFACE": ("technical_clean", "topology_reviewed", "evaluated_surface_reviewed"),
    "TERTIARY_DETAIL": ("upstream_gates_pass", "detail_scope_reviewed"),
    "PRODUCTION_PREP": ("organization_pass", "transforms_reviewed", "materials_reviewed", "export_plan_recorded"),
    "FINAL_REVIEW": ("independent_verification_pass", "reference_review_pass", "editable_source_saved"),
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in string.hexdigits for character in value)
    )


def _component_coverage_is_valid(value: Any) -> bool:
    """Validate the useful subset of a structured scene-component coverage report.

    A mere ``primary_components_present=True`` is a self-authored assertion.  The
    report must instead preserve the declared components, inspected object names,
    one-to-one matches, and the absence of unmatched primary components.  This
    remains a presence gate rather than a reference-likeness gate.
    """
    if not isinstance(value, dict) or value.get("capture_type") != "LIVE_MODELER_RUNTIME":
        return False
    if not isinstance(value.get("session_id"), str) or not value["session_id"]:
        return False
    if not _is_number(value.get("scene_revision")):
        return False
    if value.get("pass") is not True:
        return False
    coverage = value.get("coverage")
    if not isinstance(coverage, dict):
        return False
    declared = coverage.get("declared_primary_components")
    built = coverage.get("built_object_names")
    matches = coverage.get("component_matches")
    unmatched = coverage.get("unmatched_primary_components")
    if (
        not isinstance(declared, list) or not declared
        or not isinstance(built, list) or not isinstance(matches, dict)
        or unmatched != [] or coverage.get("coverage_ok") is not True
    ):
        return False
    if value.get("mesh_object_names") != built:
        return False
    if set(matches) != set(declared):
        return False
    if not all(name in built for name in matches.values()):
        return False
    component_evidence = coverage.get("component_evidence")
    if component_evidence is None:
        # Legacy reports prove separation only through one-to-one object names.
        if len(set(matches.values())) != len(matches):
            return False
    else:
        if not isinstance(component_evidence, dict) or set(component_evidence) != set(declared):
            return False
        evidence_keys: set[tuple[str, str, str | None]] = set()
        for component in declared:
            record = component_evidence.get(component)
            if not isinstance(record, dict):
                return False
            kind = record.get("kind")
            object_name = record.get("object_name")
            region_id = record.get("region_id")
            if object_name != matches[component] or object_name not in built:
                return False
            if kind == "object":
                if region_id is not None:
                    return False
            elif kind == "semantic_region":
                if not isinstance(region_id, str) or not region_id:
                    return False
                element_count = record.get("element_count")
                if (
                    record.get("region_valid") is not True
                    or not isinstance(element_count, int)
                    or isinstance(element_count, bool)
                    or element_count <= 0
                ):
                    return False
            else:
                return False
            key = (kind, object_name, region_id)
            if key in evidence_keys:
                return False
            evidence_keys.add(key)
    layout = value.get("component_layout")
    if layout is None:
        return True  # compatibility for existing boards without measured regions
    if not isinstance(layout, dict) or not isinstance(layout.get("layout_expectations_present"), bool):
        return False
    if not layout["layout_expectations_present"]:
        return layout.get("layout_ok") is None and layout.get("status") == "not_applicable"
    reports = layout.get("component_reports")
    if layout.get("layout_ok") is not True or layout.get("status") != "pass" or not isinstance(reports, dict):
        return False
    return all(
        component in reports
        and reports[component].get("object_name") == matches[component]
        and reports[component].get("presence_ok") is True
        and reports[component].get("placement_ok") is True
        and reports[component].get("proportion_ok") is True
        for component in declared
    )


def _shape_pipeline_evidence_is_valid(value: Any) -> bool:
    """Require the hash-bound multiview bundle consumed by ``modeling_core``."""
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return False
    views = value.get("views")
    return (
        value.get("record_type") == "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE"
        and isinstance(value.get("target_id"), str) and bool(value["target_id"])
        and isinstance(value.get("target_variant"), str) and bool(value["target_variant"])
        and isinstance(views, list) and len(views) >= 2
        and len({view.get("view_id") for view in views if isinstance(view, dict)}) == len(views)
        and all(
            isinstance(view, dict)
            and isinstance(view.get("view_id"), str) and bool(view["view_id"])
            and isinstance(view.get("source_sha256"), str) and _is_sha256(view["source_sha256"])
            and isinstance(view.get("mask_sha256"), str) and _is_sha256(view["mask_sha256"])
            and view.get("issues") == []
            for view in views
        )
        and value.get("missing_component_support") == {}
        and value.get("issues") == []
        and value.get("accepted_for_shape_solving") is True
    )


def _fitted_view_ids(value: Any) -> list[str] | None:
    """Validate fitted solver evidence and return its independently scored views."""
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return None
    if value.get("record_type") == "SHAPE_FAMILY_SELECTION":
        selected = value.get("selected_result")
        candidates = value.get("candidates")
        if (
            value.get("pass") is not True
            or not isinstance(candidates, list) or len(candidates) < 2
            or not isinstance(selected, dict)
            or selected.get("record_type") != "FITTED_SHAPE_HYPOTHESIS"
            or selected.get("family_compatible") is not True
            or selected.get("compatibility_issues") != []
        ):
            return None
        per_view = selected.get("per_view")
        return sorted(per_view) if isinstance(per_view, dict) and len(per_view) >= 2 else None
    if value.get("record_type") == "COMPONENT_FAMILY_SELECTION_SET":
        components = value.get("components")
        if value.get("ready_for_compilation") is not True or not isinstance(components, dict) or not components:
            return None
        view_sets = []
        for report in components.values():
            selected = report.get("selection", {}).get("selected_result") if isinstance(report, dict) else None
            per_view = selected.get("per_view") if isinstance(selected, dict) else None
            if (
                not isinstance(report, dict)
                or report.get("status") != "SELECTED"
                or not isinstance(selected, dict)
                or selected.get("record_type") != "FITTED_SHAPE_HYPOTHESIS"
                or selected.get("family_compatible") is not True
                or selected.get("compatibility_issues") != []
                or not isinstance(per_view, dict) or len(per_view) < 2
            ):
                return None
            view_sets.append(set(per_view))
        shared = set.intersection(*view_sets)
        return sorted(shared) if len(shared) >= 2 and all(views == shared for views in view_sets) else None
    return None


def _reference_audit_is_valid(value: Any) -> bool:
    required_checks = {
        "same_target_identity_pass", "view_coverage_pass", "orthographic_coverage_pass",
        "provenance_coverage_pass", "critical_property_coverage_pass",
        "dimensional_anchor_pass", "conflicts_resolved_pass", "question_driven_research_pass",
        "artifact_binding_pass",
    }
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return False
    checks = value.get("checks")
    return (
        value.get("record_type") == "REFERENCE_SET_AUDIT"
        and isinstance(value.get("target_id"), str) and bool(value["target_id"])
        and isinstance(value.get("target_variant"), str) and bool(value["target_variant"])
        and isinstance(value.get("reference_count"), int) and value["reference_count"] > 0
        and isinstance(value.get("matching_reference_count"), int)
        and 0 < value["matching_reference_count"] <= value["reference_count"]
        and isinstance(checks, dict) and required_checks <= set(checks)
        and all(checks.get(key) is True for key in required_checks)
        and value.get("issues") == []
        and value.get("pass") is True
        and value.get("disposition") == "READY_TO_MODEL"
        and isinstance(value.get("authorized_reference_sha256"), list)
        and bool(value["authorized_reference_sha256"])
        and len(value["authorized_reference_sha256"]) == len(set(value["authorized_reference_sha256"]))
        and all(_is_sha256(item) for item in value["authorized_reference_sha256"])
    )


def _modeling_spec_audit_is_valid(value: Any) -> bool:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return False
    component_ids = value.get("component_ids")
    feature_ids = value.get("identity_feature_ids")
    reference_hashes = value.get("authorized_reference_sha256")
    return (
        value.get("record_type") == "REFERENCE_MODELING_SPEC_AUDIT"
        and isinstance(value.get("target_id"), str) and bool(value["target_id"])
        and isinstance(value.get("target_variant"), str) and bool(value["target_variant"])
        and isinstance(component_ids, list) and bool(component_ids)
        and len(component_ids) == len(set(component_ids))
        and all(isinstance(item, str) and item for item in component_ids)
        and isinstance(feature_ids, list) and bool(feature_ids)
        and len(feature_ids) == len(set(feature_ids))
        and all(isinstance(item, str) and item for item in feature_ids)
        and isinstance(reference_hashes, list) and bool(reference_hashes)
        and len(reference_hashes) == len(set(reference_hashes))
        and all(_is_sha256(item) for item in reference_hashes)
        and value.get("errors") == []
        and value.get("pass") is True
    )


def _visual_evidence_failures(evidence: dict[str, Any], view_ids: list[str]) -> list[str]:
    """Validate the review records that numbers alone cannot replace.

    This deliberately checks provenance and completeness rather than trying to
    turn a subjective review into an automated resemblance score.  Every
    declared view needs an explicit assessment, and an unresolved high-salience
    mismatch must keep the asset at the proportion stage.
    """
    failures: list[str] = []
    preflight = evidence["render_evidence_preflight"]
    if not isinstance(preflight, dict) or preflight.get("record_type") != "MULTIVIEW_RENDER_EVIDENCE_PREFLIGHT":
        failures.append("render_evidence_preflight must be a multiview render evidence report")
    elif (
        preflight.get("pass") is not True
        or preflight.get("blank_views") != []
        or preflight.get("duplicate_view_groups") != []
    ):
        failures.append("render evidence contains blank or duplicate declared views")
    ledger = evidence["visual_mismatch_ledger"]
    if not isinstance(ledger, list) or not ledger:
        failures.append("visual_mismatch_ledger must record a review for every declared view")
        return failures
    reviewed_views: set[str] = set()
    allowed_statuses = {"accepted", "repair", "unresolved"}
    allowed_salience = {"high", "medium", "low"}
    for entry in ledger:
        if not isinstance(entry, dict):
            failures.append("visual_mismatch_ledger contains a non-object entry")
            continue
        view_id = entry.get("view_id")
        status = entry.get("status")
        salience = entry.get("salience", "low")
        observation = entry.get("observation")
        if view_id not in view_ids:
            failures.append("visual_mismatch_ledger references an undeclared view")
        else:
            reviewed_views.add(view_id)
        if status not in allowed_statuses:
            failures.append("visual_mismatch_ledger status must be accepted, repair, or unresolved")
        if salience not in allowed_salience:
            failures.append("visual_mismatch_ledger salience must be high, medium, or low")
        if not isinstance(observation, str) or not observation.strip():
            failures.append("visual_mismatch_ledger entries require an observation")
        if salience == "high" and status != "accepted":
            failures.append("an unresolved high-salience visual mismatch blocks proportion advance")
    missing_views = sorted(set(view_ids) - reviewed_views)
    if missing_views:
        failures.append("visual_mismatch_ledger is missing declared views: " + ", ".join(missing_views))
    return failures


def evaluate_stage_gate(stage: str, evidence: dict[str, Any]) -> dict:
    if stage not in STAGE_REQUIREMENTS:
        raise ValueError(f"unknown modeling stage: {stage}")
    missing = [key for key in STAGE_REQUIREMENTS[stage] if key not in evidence]
    failures: list[str] = []
    if not missing:
        if stage == "REFERENCE_ANALYSIS":
            reference_audit = evidence["reference_audit"]
            if not _reference_audit_is_valid(reference_audit):
                failures.append("reference_audit is missing, malformed, or not ready to model")
            modeling_spec_audit = evidence["modeling_spec_audit"]
            if not _modeling_spec_audit_is_valid(modeling_spec_audit):
                failures.append("modeling_spec_audit is missing, malformed, or not passing")
            shape_pipeline_evidence = evidence["shape_pipeline_evidence"]
            if not _shape_pipeline_evidence_is_valid(shape_pipeline_evidence):
                failures.append("shape_pipeline_evidence is missing, malformed, or not accepted for shape solving")
            if _reference_audit_is_valid(reference_audit):
                target_id = reference_audit["target_id"]
                target_variant = reference_audit["target_variant"]
                if _modeling_spec_audit_is_valid(modeling_spec_audit) and (
                    modeling_spec_audit["target_id"] != target_id
                    or modeling_spec_audit["target_variant"] != target_variant
                ):
                    failures.append("modeling spec targets a different asset or variant")
                if _modeling_spec_audit_is_valid(modeling_spec_audit) and not set(
                    modeling_spec_audit["authorized_reference_sha256"]
                ) <= set(reference_audit["authorized_reference_sha256"]):
                    failures.append("modeling spec cites reference artifacts outside the audited set")
                if _shape_pipeline_evidence_is_valid(shape_pipeline_evidence) and (
                    shape_pipeline_evidence["target_id"] != target_id
                    or shape_pipeline_evidence["target_variant"] != target_variant
                ):
                    failures.append("shape pipeline evidence targets a different asset or variant")
                if _shape_pipeline_evidence_is_valid(shape_pipeline_evidence) and not {
                    view["source_sha256"] for view in shape_pipeline_evidence["views"]
                } <= set(reference_audit["authorized_reference_sha256"]):
                    failures.append("shape pipeline evidence cites reference artifacts outside the audited set")
        elif stage == "PRIMARY_BLOCKOUT":
            if not evidence["dimensions_checked"]: failures.append("dimensions not checked")
            if not evidence["primary_components_present"]: failures.append("primary components missing")
            if not _component_coverage_is_valid(evidence["component_coverage"]):
                failures.append("structured distinct component coverage is missing or invalid")
        elif stage == "PROPORTION_SILHOUETTE":
            view_ids = _fitted_view_ids(evidence["fitted_shape_evidence"])
            if view_ids is None:
                failures.append("fitted_shape_evidence is not a passing multi-family, multi-view solver result")
            else:
                failures.extend(_visual_evidence_failures(evidence, view_ids))
        else:
            for key in STAGE_REQUIREMENTS[stage]:
                if isinstance(evidence[key], bool) and not evidence[key]:
                    failures.append(f"{key} is false")
    return {"stage": stage, "required": list(STAGE_REQUIREMENTS[stage]), "missing": missing, "failures": failures, "pass": not missing and not failures}
