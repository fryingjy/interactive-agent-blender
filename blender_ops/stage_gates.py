"""Pure-Python stage evidence validation shared by Blender runtime and tests."""

from __future__ import annotations

from typing import Any


STAGE_REQUIREMENTS = {
    "REFERENCE_ANALYSIS": (
        "component_graph_pass", "measured_ratio_count", "uncertainty_recorded",
        "reference_set_audit_pass", "same_target_identity_pass", "view_coverage_pass",
        "critical_property_coverage_pass", "conflicts_resolved_pass",
    ),
    "PRIMARY_BLOCKOUT": ("dimensions_checked", "primary_components_present"),
    "PROPORTION_SILHOUETTE": ("view_count", "worst_view_iou", "multiview_regression_pass"),
    "SECONDARY_FORMS": ("secondary_components_present", "placement_checked"),
    "TOPOLOGY_SURFACE": ("technical_clean", "topology_reviewed", "evaluated_surface_reviewed"),
    "TERTIARY_DETAIL": ("upstream_gates_pass", "detail_scope_reviewed"),
    "PRODUCTION_PREP": ("organization_pass", "transforms_reviewed", "materials_reviewed", "export_plan_recorded"),
    "FINAL_REVIEW": ("independent_verification_pass", "reference_review_pass", "editable_source_saved"),
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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
        elif stage == "PRIMARY_BLOCKOUT":
            if not evidence["dimensions_checked"]: failures.append("dimensions not checked")
            if not evidence["primary_components_present"]: failures.append("primary components missing")
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
