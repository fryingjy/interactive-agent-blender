"""Compete generic shape families against the same reference evidence."""

from __future__ import annotations

from typing import Any

import numpy as np

from .fitting import fit_hypothesis


def select_shape_family(
    candidates: list[dict[str, Any]],
    reference_masks: dict[str, np.ndarray],
    *,
    seed: int = 0,
    maxiter: int = 20,
    popsize: int = 6,
) -> dict[str, Any]:
    """Fit every declared candidate and select the lowest-loss compatible family."""
    if len(candidates) < 2:
        raise ValueError("family selection requires at least two candidate hypotheses")
    results = []
    for index, candidate in enumerate(candidates):
        candidate_id = str(candidate.get("candidate_id") or f"candidate-{index + 1}")
        try:
            result = fit_hypothesis(candidate, reference_masks, seed=seed + index, maxiter=maxiter, popsize=popsize)
            results.append({
                "candidate_id": candidate_id,
                "family": result["hypothesis"]["shape"]["family"],
                "compatible": result["family_compatible"],
                "mean_view_loss": result["mean_view_loss"],
                "issues": result["compatibility_issues"],
                "result": result,
            })
        except (KeyError, TypeError, ValueError) as exc:
            results.append({
                "candidate_id": candidate_id,
                "family": candidate.get("shape", {}).get("family"),
                "compatible": False,
                "mean_view_loss": None,
                "issues": [f"candidate failed validation or fitting: {exc}"],
                "result": None,
            })
    compatible = [item for item in results if item["compatible"]]
    compatible.sort(key=lambda item: (item["mean_view_loss"], item["candidate_id"]))
    selected = compatible[0] if compatible else None
    return {
        "schema_version": 1,
        "record_type": "SHAPE_FAMILY_SELECTION",
        "selected_candidate_id": selected["candidate_id"] if selected else None,
        "selected_family": selected["family"] if selected else None,
        "selected_result": selected["result"] if selected else None,
        "candidates": results,
        "pass": selected is not None,
        "claim_boundary": "Selection compares only the supplied families, variables, cameras, and masks. A winner is not proof that unobserved geometry is correct.",
    }
