"""Pure-Python stage evidence validation shared by Blender runtime and tests."""

from __future__ import annotations

import string
from typing import Any


STAGE_REQUIREMENTS = {
    "REFERENCE_ANALYSIS": (
        "component_graph_pass", "measured_ratio_count", "uncertainty_recorded",
        "reference_set_audit_pass", "same_target_identity_pass", "view_coverage_pass",
        "critical_property_coverage_pass", "conflicts_resolved_pass",
        "question_driven_research_pass", "visual_reconstruction_audit_pass",
        "component_reference_coverage_pass",
        "depth_critical_reference_support_pass",
        "reference_audit",
        "modeling_spec_audit",
    ),
    "PRIMARY_BLOCKOUT": (
        "dimensions_checked", "primary_components_present", "component_coverage",
    ),
    "PROPORTION_SILHOUETTE": (
        "view_count", "worst_view_iou", "multiview_regression_pass",
        "declared_view_ids", "constraint_report", "visual_mismatch_ledger", "render_evidence_preflight",
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


def _visual_reconstruction_audit_is_valid(value: Any) -> bool:
    """Require the real 11-pass audit_visual_reconstruction() result, not a bare True.

    Mirrors _component_coverage_is_valid's own precedent: a self-asserted boolean proves
    nothing, so this checks the actual structured record type and its own computed pass.
    """
    required_checks = {
        "identity_bound", "independent_observations", "property_specific_authority",
        "eleven_passes_recorded", "competing_interpretations_tested",
        "bad_interpretation_eliminated", "construction_bound_to_selected_interpretation",
        "uncertainty_kept_reversible", "every_component_has_construction_justification",
    }
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return False
    checks = value.get("checks")
    selected = value.get("selected_hypothesis_ids")
    return (
        value.get("record_type") == "VISUAL_RECONSTRUCTION_AUDIT"
        and isinstance(value.get("target_id"), str) and bool(value["target_id"])
        and isinstance(checks, dict) and required_checks <= set(checks)
        and all(checks.get(key) is True for key in required_checks)
        and isinstance(value.get("region_reports"), list) and bool(value["region_reports"])
        and isinstance(selected, list) and bool(selected) and len(selected) == len(set(selected))
        and _is_number(value.get("contradiction_count")) and value["contradiction_count"] > 0
        and value.get("errors") == []
        and value.get("pass") is True
    )


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


def _component_reference_coverage_is_valid(value: Any) -> bool:
    """Require validate_component_reference_coverage()'s structured result, not a bare True."""
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return False
    covered = value.get("covered_component_ids")
    count = value.get("component_count")
    return (
        value.get("record_type") == "COMPONENT_REFERENCE_COVERAGE"
        and isinstance(count, int) and not isinstance(count, bool) and count > 0
        and isinstance(covered, list) and len(covered) == count and len(covered) == len(set(covered))
        and value.get("uncovered_component_ids") == []
        and value.get("pass") is True
    )


def _depth_critical_reference_support_is_valid(value: Any) -> bool:
    """Require the structured depth-critical support report, never a bare assertion."""
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or value.get("record_type") != "DEPTH_CRITICAL_REFERENCE_SUPPORT"
    ):
        return False
    component_ids = value.get("depth_critical_component_ids")
    reports = value.get("component_reports")
    if (
        not isinstance(component_ids, list)
        or len(component_ids) != len(set(component_ids))
        or not isinstance(reports, dict)
        or set(reports) != set(component_ids)
        or value.get("unsupported_component_ids") != []
        or value.get("pass") is not True
    ):
        return False
    return all(
        isinstance(report, dict)
        and report.get("pass") is True
        and isinstance(report.get("view_ids"), list)
        and len(set(report["view_ids"])) >= 2
        and report.get("view_count") == len(set(report["view_ids"]))
        and isinstance(report.get("reference_ids"), list)
        and len(report["reference_ids"]) >= 2
        for report in reports.values()
    )


def _visual_evidence_failures(evidence: dict[str, Any]) -> list[str]:
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
    view_ids = evidence["declared_view_ids"]
    if (
        not isinstance(view_ids, list)
        or len(view_ids) < 2
        or any(not isinstance(view_id, str) or not view_id.strip() for view_id in view_ids)
        or len(set(view_ids)) != len(view_ids)
    ):
        failures.append("declared_view_ids must contain at least two unique non-empty view identifiers")
        return failures

    report = evidence["constraint_report"]
    if not isinstance(report, dict) or report.get("record_type") != "LOCAL_REFERENCE_CONSTRAINT_EVALUATION":
        failures.append("constraint_report must be a local reference-constraint evaluation")
    elif report.get("pass") is not True or report.get("blocking_constraint_ids") != []:
        failures.append("high-salience reference constraints remain unresolved")

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


def evaluate_stage_gate(stage: str, evidence: dict[str, Any], *, min_iou: float = 0.9) -> dict:
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
            if not evidence["component_graph_pass"]: failures.append("component graph invalid")
            ratio_count = evidence["measured_ratio_count"]
            if not _is_number(ratio_count) or ratio_count < 1:
                failures.append("measured_ratio_count must be a positive number")
            if not evidence["uncertainty_recorded"]: failures.append("reference uncertainty omitted")
            if not evidence["reference_set_audit_pass"]: failures.append("reference set is not ready to model")
            if not evidence["same_target_identity_pass"]: failures.append("reference set mixes target identities or variants")
            if not evidence["view_coverage_pass"]: failures.append("required reference views are missing")
            if not evidence["critical_property_coverage_pass"]: failures.append("critical properties lack authoritative evidence")
            if not evidence["conflicts_resolved_pass"]: failures.append("reference conflicts remain unresolved")
            if not evidence["question_driven_research_pass"]: failures.append("high-impact reference questions remain open or unaudited")
            audit_checks = reference_audit.get("checks", {}) if isinstance(reference_audit, dict) else {}
            flattened = {
                "reference_set_audit_pass": reference_audit.get("pass") if isinstance(reference_audit, dict) else None,
                "same_target_identity_pass": audit_checks.get("same_target_identity_pass"),
                "view_coverage_pass": bool(audit_checks.get("view_coverage_pass")) and bool(audit_checks.get("orthographic_coverage_pass")),
                "critical_property_coverage_pass": audit_checks.get("critical_property_coverage_pass"),
                "conflicts_resolved_pass": audit_checks.get("conflicts_resolved_pass"),
                "question_driven_research_pass": audit_checks.get("question_driven_research_pass"),
            }
            if any(evidence.get(key) is not value for key, value in flattened.items()):
                failures.append("flattened reference flags contradict the structured reference_audit")
            if not _visual_reconstruction_audit_is_valid(evidence["visual_reconstruction_audit_pass"]):
                failures.append("visual reconstruction audit missing, invalid, or not passing")
            if not _component_reference_coverage_is_valid(evidence["component_reference_coverage_pass"]):
                failures.append("reference evidence does not cover every declared component")
            if not _depth_critical_reference_support_is_valid(evidence["depth_critical_reference_support_pass"]):
                failures.append("depth-critical components lack multi-view structural evidence")
            if _reference_audit_is_valid(reference_audit):
                target_id = reference_audit["target_id"]
                target_variant = reference_audit["target_variant"]
                visual_audit = evidence["visual_reconstruction_audit_pass"]
                if isinstance(visual_audit, dict) and visual_audit.get("target_id") != target_id:
                    failures.append("visual reconstruction audit targets a different asset")
                if _modeling_spec_audit_is_valid(modeling_spec_audit) and (
                    modeling_spec_audit["target_id"] != target_id
                    or modeling_spec_audit["target_variant"] != target_variant
                ):
                    failures.append("modeling spec targets a different asset or variant")
                if _modeling_spec_audit_is_valid(modeling_spec_audit) and not set(
                    modeling_spec_audit["authorized_reference_sha256"]
                ) <= set(reference_audit["authorized_reference_sha256"]):
                    failures.append("modeling spec cites reference artifacts outside the audited set")
        elif stage == "PRIMARY_BLOCKOUT":
            if not evidence["dimensions_checked"]: failures.append("dimensions not checked")
            if not evidence["primary_components_present"]: failures.append("primary components missing")
            if not _component_coverage_is_valid(evidence["component_coverage"]):
                failures.append("structured distinct component coverage is missing or invalid")
        elif stage == "PROPORTION_SILHOUETTE":
            view_count = evidence["view_count"]
            worst_view_iou = evidence["worst_view_iou"]
            if not _is_number(view_count) or view_count < 2:
                failures.append("view_count must describe at least two relevant views")
            if not _is_number(worst_view_iou) or not 0.0 <= worst_view_iou <= 1.0:
                failures.append("worst_view_iou must be a number in [0, 1]")
            elif worst_view_iou < min_iou:
                failures.append(f"worst-view IoU below {min_iou}")
            if not evidence["multiview_regression_pass"]: failures.append("a relevant view regressed")
            failures.extend(_visual_evidence_failures(evidence))
        else:
            for key in STAGE_REQUIREMENTS[stage]:
                if isinstance(evidence[key], bool) and not evidence[key]:
                    failures.append(f"{key} is false")
    return {"stage": stage, "required": list(STAGE_REQUIREMENTS[stage]), "missing": missing, "failures": failures, "pass": not missing and not failures}
