"""Bounded, reproducible parameter fitting for registered low-resolution masks.

Topology is intentionally outside this API. Callers expose only predeclared semantic parameters
(camera, landmark, radius, length, or profile controls), so the optimizer cannot invent parts or
silently rewrite a mesh representation.
"""

from __future__ import annotations

from typing import Callable, Sequence

import numpy as np

from .visual_compare import compare_masks


def silhouette_objective(
    reference_mask: np.ndarray,
    render_mask: Callable[[np.ndarray], np.ndarray],
    *,
    contour_weight: float = 0.25,
    negative_space_weight: float = 0.25,
) -> Callable[[np.ndarray], float]:
    reference = np.asarray(reference_mask, dtype=bool)
    if reference.ndim != 2 or not reference.any():
        raise ValueError("reference_mask must be a non-empty 2D mask")

    def objective(parameters: np.ndarray) -> float:
        candidate = np.asarray(render_mask(np.asarray(parameters, dtype=float)), dtype=bool)
        if candidate.shape != reference.shape or not candidate.any():
            return 10.0
        metrics = compare_masks(reference, candidate)
        contour = metrics["symmetric_contour_error_normalized"]
        negative_iou = metrics["negative_space_iou"]
        contour_penalty = 1.0 if contour is None else float(contour)
        negative_penalty = 1.0 if negative_iou is None else 1.0 - float(negative_iou)
        return (
            1.0 - float(metrics["silhouette_iou"])
            + contour_weight * contour_penalty
            + negative_space_weight * negative_penalty
        )

    return objective


def fit_bounded_parameters(
    objective: Callable[[np.ndarray], float],
    bounds: Sequence[tuple[float, float]],
    *,
    initial: Sequence[float] | None = None,
    seed: int = 0,
    maxiter: int = 40,
    popsize: int = 8,
) -> dict:
    """Run deterministic differential evolution and retain only a measurable improvement."""
    try:
        from scipy.optimize import differential_evolution
    except ImportError as exc:
        raise RuntimeError(
            "Install the scoped reference-analysis dependencies: "
            "pip install -r requirements/reference-analysis.txt"
        ) from exc
    clean_bounds = [(float(low), float(high)) for low, high in bounds]
    if not clean_bounds or any(not low < high for low, high in clean_bounds):
        raise ValueError("bounds must contain finite increasing pairs")
    if initial is None:
        initial_array = np.asarray([(low + high) * 0.5 for low, high in clean_bounds], dtype=float)
    else:
        initial_array = np.asarray(initial, dtype=float)
    if initial_array.shape != (len(clean_bounds),):
        raise ValueError("initial parameter count does not match bounds")
    if any(value < low or value > high for value, (low, high) in zip(initial_array, clean_bounds)):
        raise ValueError("initial parameters lie outside bounds")
    initial_score = float(objective(initial_array))
    result = differential_evolution(
        objective,
        clean_bounds,
        strategy="best1bin",
        maxiter=maxiter,
        popsize=popsize,
        tol=1e-6,
        polish=True,
        rng=np.random.default_rng(seed),
        workers=1,
        updating="immediate",
        x0=initial_array,
    )
    final_score = float(result.fun)
    improved = final_score < initial_score - 1e-8
    return {
        "schema_version": 1,
        "record_type": "BOUNDED_PARAMETER_FIT",
        "initial_parameters": initial_array.tolist(),
        "candidate_parameters": np.asarray(result.x, dtype=float).tolist(),
        "retained_parameters": np.asarray(result.x if improved else initial_array, dtype=float).tolist(),
        "initial_objective": initial_score,
        "candidate_objective": final_score,
        "improvement": initial_score - final_score,
        "retain_candidate": improved,
        "optimizer_success": bool(result.success),
        "optimizer_message": str(result.message),
        "function_evaluations": int(result.nfev),
        "seed": seed,
        "claim_boundary": "The fit searches only declared bounded parameters. It cannot choose topology, representation, semantic parts, or professional quality.",
    }
