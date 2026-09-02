"""Bounded multiview fitting of an executable shape hypothesis."""

from __future__ import annotations

import copy
from typing import Any

import cv2
import numpy as np

from knowledge_engine.parameter_fitting import fit_bounded_parameters

from .hypothesis import pointer_get, pointer_set, validate_hypothesis
from .mesh import build_section_loft
from .render import render_silhouette


def mask_loss(reference: np.ndarray, candidate: np.ndarray) -> float:
    reference = np.asarray(reference, dtype=bool)
    candidate = np.asarray(candidate, dtype=bool)
    union = np.logical_or(reference, candidate).sum()
    if not union or not candidate.any():
        return 10.0
    iou_loss = 1.0 - np.logical_and(reference, candidate).sum() / union
    ref_edge = cv2.morphologyEx(reference.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    can_edge = cv2.morphologyEx(candidate.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    ref_distance = cv2.distanceTransform(1 - ref_edge, cv2.DIST_L2, 3)
    can_distance = cv2.distanceTransform(1 - can_edge, cv2.DIST_L2, 3)
    contour = 0.5 * (ref_distance[can_edge > 0].mean() + can_distance[ref_edge > 0].mean())
    contour /= max(reference.shape)
    return float(iou_loss + 0.35 * contour)


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
        vertices, faces = build_section_loft(candidate["shape"])
        losses = [mask_loss(reference_masks[key], render_silhouette(vertices, faces, candidate_view)) for key, candidate_view in ((view["id"], view) for view in candidate["views"])]
        widths = np.asarray([station["half_width"] for station in candidate["shape"]["stations"]])
        depths = np.asarray([station["half_depth"] for station in candidate["shape"]["stations"]])
        smoothness = sum(np.abs(np.diff(values, n=2)).mean() for values in (widths, depths) if len(values) > 2)
        return float(np.mean(losses) + 0.01 * smoothness)

    fit = fit_bounded_parameters(objective, bounds, initial=initial, seed=seed, maxiter=maxiter, popsize=popsize)
    retained = materialize(np.asarray(fit["retained_parameters"], dtype=float))
    vertices, faces = build_section_loft(retained["shape"])
    per_view = {}
    for view in retained["views"]:
        rendered = render_silhouette(vertices, faces, view)
        per_view[view["id"]] = {"loss": mask_loss(reference_masks[view["id"]], rendered)}
    return {
        "schema_version": 1,
        "record_type": "FITTED_SHAPE_HYPOTHESIS",
        "hypothesis": retained,
        "fit": fit,
        "per_view": per_view,
        "mean_view_loss": float(np.mean([item["loss"] for item in per_view.values()])),
        "claim_boundary": "This proves bounded agreement with supplied masks and cameras; it does not prove hidden geometry, final topology, or artistic quality.",
    }
