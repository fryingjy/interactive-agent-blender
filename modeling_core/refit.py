"""Turn retained multiview fit disagreement into scoped, evidence-bearing refit tickets."""

from __future__ import annotations

import copy
from typing import Any

import numpy as np

from .fitting import mask_diagnostics
from .hypothesis import pointer_get, pointer_set, validate_hypothesis
from .mesh import build_shape_mesh
from .render import render_silhouette


def _probe_shape_parameters(
    fitted_result: dict[str, Any],
    reference_masks: dict[str, np.ndarray],
    *,
    probe_fraction: float,
) -> dict[str, list[dict[str, Any]]]:
    hypothesis = validate_hypothesis(fitted_result["hypothesis"])
    views = {view["id"]: view for view in hypothesis["views"]}
    baseline = {view_id: float(item["loss"]) for view_id, item in fitted_result["per_view"].items()}
    probes = {view_id: [] for view_id in views}
    for variable in hypothesis["variables"]:
        pointer = variable["pointer"]
        if not pointer.startswith("/shape/"):
            continue
        retained_value = float(pointer_get(hypothesis, pointer))
        low, high = map(float, variable["bounds"])
        delta = (high - low) * probe_fraction
        tested_values = sorted({max(low, retained_value - delta), min(high, retained_value + delta)} - {retained_value})
        for tested_value in tested_values:
            candidate = copy.deepcopy(hypothesis)
            pointer_set(candidate, pointer, tested_value)
            try:
                candidate = validate_hypothesis(candidate)
                vertices, faces = build_shape_mesh(candidate["shape"])
                losses = {
                    view_id: float(mask_diagnostics(
                        reference_masks[view_id],
                        render_silhouette(vertices, faces, view),
                    )["loss"])
                    for view_id, view in views.items()
                }
            except ValueError:
                continue
            mean_loss = float(np.mean(list(losses.values())))
            baseline_mean = float(np.mean(list(baseline.values())))
            for view_id in views:
                probes[view_id].append({
                    "parameter_pointer": pointer,
                    "retained_value": retained_value,
                    "tested_value": float(tested_value),
                    "direction": "INCREASE" if tested_value > retained_value else "DECREASE",
                    "view_loss_before": baseline[view_id],
                    "view_loss_after": losses[view_id],
                    "view_improvement": baseline[view_id] - losses[view_id],
                    "mean_loss_before": baseline_mean,
                    "mean_loss_after": mean_loss,
                    "mean_loss_change": mean_loss - baseline_mean,
                })
    for view_id in probes:
        probes[view_id].sort(key=lambda item: (-item["view_improvement"], item["mean_loss_change"], item["parameter_pointer"]))
    return probes


def build_component_refit_tickets(
    component_id: str,
    fitted_result: dict[str, Any],
    reference_masks: dict[str, np.ndarray],
    *,
    minimum_view_loss: float = 0.015,
    minimum_probe_improvement: float = 0.001,
    maximum_mean_regression: float = 0.001,
    probe_fraction: float = 0.03,
) -> list[dict[str, Any]]:
    """Build localized tickets without treating one-view improvement as a safe edit.

    Probes are diagnostic only. A parameter is actionable only when a bounded perturbation improves
    the named view without materially worsening the retained multiview mean.
    """
    if not str(component_id).strip():
        raise ValueError("component_id must be non-empty")
    if fitted_result.get("record_type") != "FITTED_SHAPE_HYPOTHESIS":
        raise ValueError("refit tickets require a fitted shape hypothesis")
    if (
        not 0 <= minimum_view_loss
        or not 0 <= minimum_probe_improvement
        or not 0 <= maximum_mean_regression
        or not 0 < probe_fraction <= 0.25
    ):
        raise ValueError("ticket and probe thresholds are invalid")
    hypothesis = validate_hypothesis(fitted_result["hypothesis"])
    views = {view["id"]: view for view in hypothesis["views"]}
    view_ids = set(views)
    if set(reference_masks) != view_ids or set(fitted_result.get("per_view", {})) != view_ids:
        raise ValueError("refit evidence must exactly match fitted view ids")
    for view_id, mask in reference_masks.items():
        expected = (views[view_id]["image_size"][1], views[view_id]["image_size"][0])
        if np.asarray(mask).shape != expected or not np.asarray(mask, dtype=bool).any():
            raise ValueError(f"reference mask {view_id} is empty or has the wrong dimensions")
    vertices, faces = build_shape_mesh(hypothesis["shape"])
    recomputed = {
        view_id: mask_diagnostics(reference_masks[view_id], render_silhouette(vertices, faces, view))
        for view_id, view in views.items()
    }
    for view_id in view_ids:
        recorded = fitted_result["per_view"][view_id]
        if (
            abs(float(recorded.get("loss", float("inf"))) - float(recomputed[view_id]["loss"])) > 1e-9
            or recorded.get("reference_hole_count") != recomputed[view_id]["reference_hole_count"]
            or recorded.get("candidate_hole_count") != recomputed[view_id]["candidate_hole_count"]
        ):
            raise ValueError(f"{view_id}: fitted residual record is stale for the supplied mask or hypothesis")
    evidence_result = {**fitted_result, "hypothesis": hypothesis, "per_view": recomputed}
    probes = _probe_shape_parameters(evidence_result, reference_masks, probe_fraction=probe_fraction)
    tickets = []
    for view_id in sorted(view_ids):
        diagnostics = recomputed[view_id]
        hole_mismatch = diagnostics["reference_hole_count"] != diagnostics["candidate_hole_count"]
        if hole_mismatch:
            tickets.append({
                "type": "component_negative_space_failure",
                "source": "COMPONENT_MULTIVIEW_FIT",
                "target": component_id,
                "view_id": view_id,
                "severity": 1.0,
                "root_cause": "REPRESENTATION_FAILURE",
                "repair_scope": "CHANGE_FAMILY_OR_COMPONENT_GRAPH",
                "evidence": {
                    "reference_hole_count": diagnostics["reference_hole_count"],
                    "candidate_hole_count": diagnostics["candidate_hole_count"],
                    "hole_iou": diagnostics["hole_iou"],
                },
                "recommended_action": "CHANGE_REPRESENTATION",
            })
        view_loss = float(diagnostics["loss"])
        if view_loss <= minimum_view_loss:
            continue
        safe_probes = [
            item for item in probes[view_id]
            if item["view_improvement"] >= minimum_probe_improvement
            and item["mean_loss_change"] <= maximum_mean_regression
        ]
        best = safe_probes[0] if safe_probes else None
        ticket = {
            "type": "component_view_residual",
            "source": "COMPONENT_MULTIVIEW_FIT",
            "target": component_id,
            "view_id": view_id,
            "severity": min(1.0, view_loss),
            "root_cause": "DECLARED_PARAMETER_MISMATCH" if best else "REPRESENTATION_OR_COUPLED_PARAMETER_FAILURE",
            "repair_scope": "REFIT_COMPONENT" if best else "RECONSIDER_FAMILY_OR_BOUNDS",
            "evidence": {
                "loss": view_loss,
                "silhouette_iou": diagnostics["silhouette_iou"],
                "contour_error_normalized": diagnostics["contour_error_normalized"],
                "hole_iou": diagnostics["hole_iou"],
            },
            "recommended_action": "REFIT_ALL_VIEWS" if best else "COMPARE_ALTERNATE_FAMILY",
            "parameter_probes": safe_probes[:3],
        }
        if best:
            ticket["operation_params"] = {
                "component_id": component_id,
                "parameter_pointer": best["parameter_pointer"],
                "probe_direction": best["direction"],
                "retained_value": best["retained_value"],
                "tested_value": best["tested_value"],
                "requires_multiview_refit": True,
            }
        tickets.append(ticket)
    tickets.sort(key=lambda item: (-item["severity"], item["type"], item["view_id"]))
    for priority, ticket in enumerate(tickets, 1):
        ticket["priority"] = priority
    return tickets
