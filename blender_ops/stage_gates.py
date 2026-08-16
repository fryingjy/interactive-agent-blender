"""Pure-Python stage evidence validation shared by Blender runtime and tests."""

from __future__ import annotations

from typing import Any


STAGE_REQUIREMENTS = {
    "REFERENCE_ANALYSIS": (
        "component_graph_pass", "measured_ratio_count", "uncertainty_recorded",
        "reference_set_audit_pass", "same_target_identity_pass", "view_coverage_pass",
        "critical_property_coverage_pass", "conflicts_resolved_pass",
        "question_driven_research_pass",
    ),
    "PRIMARY_BLOCKOUT": (
        "dimensions_checked", "primary_components_present", "component_coverage",
    ),
    "PROPORTION_SILHOUETTE": ("view_count", "worst_view_iou", "multiview_regression_pass"),
    "SECONDARY_FORMS": ("secondary_components_present", "placement_checked"),
    "TOPOLOGY_SURFACE": ("technical_clean", "topology_reviewed", "evaluated_surface_reviewed"),
    "TERTIARY_DETAIL": ("upstream_gates_pass", "detail_scope_reviewed"),
    "PRODUCTION_PREP": ("organization_pass", "transforms_reviewed", "materials_reviewed", "export_plan_recorded"),
    "FINAL_REVIEW": ("independent_verification_pass", "reference_review_pass", "editable_source_saved"),
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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
    if set(matches) != set(declared) or len(set(matches.values())) != len(matches):
        return False
    if not all(name in built for name in matches.values()):
        return False
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


def evaluate_stage_gate(stage: str, evidence: dict[str, Any], *, min_iou: float = 0.9) -> dict:
    if stage not in STAGE_REQUIREMENTS:
        raise ValueError(f"unknown modeling stage: {stage}")
    missing = [key for key in STAGE_REQUIREMENTS[stage] if key not in evidence]
    failures: list[str] = []
    if not missing:
        if stage == "REFERENCE_ANALYSIS":
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
        elif stage == "PRIMARY_BLOCKOUT":
            if not evidence["dimensions_checked"]: failures.append("dimensions not checked")
            if not evidence["primary_components_present"]: failures.append("primary components missing")
            if not _component_coverage_is_valid(evidence["component_coverage"]):
                failures.append("structured one-to-one component coverage is missing or invalid")
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
        else:
            for key in STAGE_REQUIREMENTS[stage]:
                if isinstance(evidence[key], bool) and not evidence[key]:
                    failures.append(f"{key} is false")
    return {"stage": stage, "required": list(STAGE_REQUIREMENTS[stage]), "missing": missing, "failures": failures, "pass": not missing and not failures}
