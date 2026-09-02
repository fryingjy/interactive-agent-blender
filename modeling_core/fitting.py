"""Bounded multiview fitting of an executable shape hypothesis."""

from __future__ import annotations

import copy
from typing import Any

import cv2
import numpy as np

from knowledge_engine.parameter_fitting import fit_bounded_parameters

from .hypothesis import pointer_get, pointer_set, validate_hypothesis
from .mesh import build_shape_mesh
from .render import render_silhouette


def _enclosed_holes(mask: np.ndarray) -> tuple[np.ndarray, int]:
    inverse = (~np.asarray(mask, dtype=bool)).astype(np.uint8)
    count, labels = cv2.connectedComponents(inverse, connectivity=8)
    border_labels = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    hole_labels = [label for label in range(1, count) if label not in border_labels]
    holes = np.isin(labels, hole_labels)
    return holes, len(hole_labels)


def mask_diagnostics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float | int]:
    reference = np.asarray(reference, dtype=bool)
    candidate = np.asarray(candidate, dtype=bool)
    union = np.logical_or(reference, candidate).sum()
    if not union or not candidate.any():
        return {"loss": 10.0, "silhouette_iou": 0.0, "contour_error_normalized": 1.0, "reference_hole_count": 0, "candidate_hole_count": 0, "hole_iou": 0.0}
    silhouette_iou = np.logical_and(reference, candidate).sum() / union
    ref_edge = cv2.morphologyEx(reference.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    can_edge = cv2.morphologyEx(candidate.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    ref_distance = cv2.distanceTransform(1 - ref_edge, cv2.DIST_L2, 3)
    can_distance = cv2.distanceTransform(1 - can_edge, cv2.DIST_L2, 3)
    contour = 0.5 * (float(ref_distance[can_edge > 0].mean()) + float(can_distance[ref_edge > 0].mean()))
    contour /= max(reference.shape)
    reference_holes, reference_hole_count = _enclosed_holes(reference)
    candidate_holes, candidate_hole_count = _enclosed_holes(candidate)
    hole_union = np.logical_or(reference_holes, candidate_holes).sum()
    hole_iou = 1.0 if not hole_union else float(np.logical_and(reference_holes, candidate_holes).sum() / hole_union)
    loss = 1.0 - float(silhouette_iou) + 0.35 * contour + 0.15 * (1.0 - hole_iou)
    return {"loss": float(loss), "silhouette_iou": float(silhouette_iou), "contour_error_normalized": float(contour), "reference_hole_count": reference_hole_count, "candidate_hole_count": candidate_hole_count, "hole_iou": hole_iou}


def mask_loss(reference: np.ndarray, candidate: np.ndarray) -> float:
    return float(mask_diagnostics(reference, candidate)["loss"])


def fit_hypothesis(
    raw: dict[str, Any],
    reference_masks: dict[str, np.ndarray],
    *,
    seed: int = 0,
    maxiter: int = 30,
    popsize: int = 8,
) -> dict[str, Any]:
    """Fit declared variables only and return the retained hypothesis plus per-view evidence."""
    hypothesis = validate_hypothesis(raw)
    variables = hypothesis["variables"]
    if not variables:
        raise ValueError("fitting requires at least one declared variable")
    views = {view["id"]: view for view in hypothesis["views"]}
    if set(reference_masks) != set(views):
        raise ValueError("reference mask ids must exactly match hypothesis view ids")
    for identifier, mask in reference_masks.items():
        expected = (views[identifier]["image_size"][1], views[identifier]["image_size"][0])
        if np.asarray(mask).shape != expected or not np.asarray(mask, dtype=bool).any():
            raise ValueError(f"reference mask {identifier} is empty or has the wrong dimensions")

    initial = [float(pointer_get(hypothesis, item["pointer"])) for item in variables]
    bounds = [tuple(item["bounds"]) for item in variables]

    def materialize(parameters: np.ndarray) -> dict[str, Any]:
        candidate = copy.deepcopy(hypothesis)
        for variable, value in zip(variables, parameters):
            pointer_set(candidate, variable["pointer"], float(value))
        return candidate

    def objective(parameters: np.ndarray) -> float:
        candidate = materialize(parameters)
        vertices, faces = build_shape_mesh(candidate["shape"])
        try:
            losses = [mask_loss(reference_masks[key], render_silhouette(vertices, faces, candidate_view)) for key, candidate_view in ((view["id"], view) for view in candidate["views"])]
        except ValueError:
            return 10.0
        if candidate["shape"]["family"] == "section_loft":
            widths = np.asarray([station["half_width"] for station in candidate["shape"]["stations"]])
            depths = np.asarray([station["half_depth"] for station in candidate["shape"]["stations"]])
            smoothness = sum(np.abs(np.diff(values, n=2)).mean() for values in (widths, depths) if len(values) > 2)
        else:
            smoothness = 0.0
        return float(np.mean(losses) + 0.01 * smoothness)

    fit = fit_bounded_parameters(objective, bounds, initial=initial, seed=seed, maxiter=maxiter, popsize=popsize)
    retained = materialize(np.asarray(fit["retained_parameters"], dtype=float))
    vertices, faces = build_shape_mesh(retained["shape"])
    per_view = {}
    for view in retained["views"]:
        rendered = render_silhouette(vertices, faces, view)
        per_view[view["id"]] = mask_diagnostics(reference_masks[view["id"]], rendered)
    mean_view_loss = float(np.mean([item["loss"] for item in per_view.values()]))
    acceptance = retained["acceptance"]
    compatibility_issues = []
    if mean_view_loss > acceptance["max_mean_view_loss"]:
        compatibility_issues.append("mean view loss exceeds the family limit")
    for identifier, diagnostics in per_view.items():
        if diagnostics["loss"] > acceptance["max_each_view_loss"]:
            compatibility_issues.append(f"{identifier}: view loss exceeds the family limit")
        if acceptance["require_hole_count_match"] and diagnostics["reference_hole_count"] != diagnostics["candidate_hole_count"]:
            compatibility_issues.append(f"{identifier}: enclosed negative-space count cannot be represented")
    return {
        "schema_version": 1,
        "record_type": "FITTED_SHAPE_HYPOTHESIS",
        "hypothesis": retained,
        "fit": fit,
        "per_view": per_view,
        "mean_view_loss": mean_view_loss,
        "family_compatible": not compatibility_issues,
        "compatibility_issues": compatibility_issues,
        "claim_boundary": "This proves bounded agreement with supplied masks and cameras; it does not prove hidden geometry, final topology, or artistic quality.",
    }
