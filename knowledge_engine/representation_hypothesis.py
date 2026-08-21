"""Test a StrategyCandidate's predicted visual consequence against a specific
reference item, honestly refusing the test when the evidence can't support it.

Why this exists (2026-08-21, direct user critique): reference_analysis.py and
scene_decomposition.py check whether evidence and candidate strategies EXIST,
not whether a candidate's predicted consequences actually hold against that
evidence. Found live, not hypothetically: trying to decide whether the Scotch
C38 tape dispenser's shell roof is a flat tapered plane or a continuously
curved profile, a landmark-based pixel measurement on the reference photo
came back internally contradictory. The reason: a flat 3D plane does not
project to a straight line in image space under PERSPECTIVE projection --
only under ORTHOGRAPHIC (or a calibrated camera) does "does the silhouette
boundary look linear" actually test "is the surface flat". The measurement
had silently assumed orthographic projection while measuring an oblique
photo. `ReferenceItem.projection` already records which case applies; this
module is what actually reads it before running a test, instead of a human
or agent quietly assuming orthographic and getting a confident wrong answer.

This module deliberately covers ONE prediction_type to start
(`boundary_linearity`, the exact class that broke) rather than a generic
framework for arbitrary predictions -- see the plan this shipped under for
why: build the one piece blocking real work, not a speculative general
system ahead of a second proven need.
"""

from __future__ import annotations

from typing import Any


UNDECIDABLE_PERSPECTIVE_REASON = (
    "a flat 3D plane does not project to a straight line under uncalibrated "
    "perspective projection -- boundary_linearity cannot be tested from a "
    "PERSPECTIVE reference without known camera parameters"
)


def evaluate_predicted_consequence(
    consequence: dict[str, Any],
    reference_item: Any,
    *,
    landmarks: list[tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Evaluate one StrategyCandidate.predicted_consequences entry against one
    reference item.

    ``landmarks`` is only used for prediction_type "boundary_linearity" on an
    ORTHOGRAPHIC reference: three or more (position_fraction, boundary_value)
    points along the axis in question, in the same units the caller wants
    reported. Position fractions are in [0, 1] along the measured span.

    Returns a dict with:
      status: "CONFIRMED" | "CONTRADICTED" | "UNDECIDABLE"
      reason: human-readable explanation, always present
      prediction_type: echoed from the input consequence
    """
    prediction_type = consequence.get("prediction_type")
    if prediction_type != "boundary_linearity":
        return {
            "status": "UNDECIDABLE",
            "reason": f"no evaluator implemented for prediction_type '{prediction_type}'",
            "prediction_type": prediction_type,
        }

    projection = getattr(reference_item, "projection", None)
    if projection is None and isinstance(reference_item, dict):
        projection = reference_item.get("projection")

    if projection == "PERSPECTIVE" or projection == "UNKNOWN":
        return {
            "status": "UNDECIDABLE",
            "reason": UNDECIDABLE_PERSPECTIVE_REASON,
            "prediction_type": prediction_type,
        }

    if projection != "ORTHOGRAPHIC":
        return {
            "status": "UNDECIDABLE",
            "reason": f"unrecognized projection '{projection}'",
            "prediction_type": prediction_type,
        }

    if not landmarks or len(landmarks) < 3:
        return {
            "status": "UNDECIDABLE",
            "reason": "boundary_linearity on an orthographic reference needs at least 3 landmarks "
                      "(two endpoints plus at least one independent interior point) -- none/too few supplied",
            "prediction_type": prediction_type,
        }

    ordered = sorted(landmarks, key=lambda p: p[0])
    (x0, y0), (x1, y1) = ordered[0], ordered[-1]
    span = x1 - x0
    if abs(span) < 1e-9:
        return {
            "status": "UNDECIDABLE",
            "reason": "landmark endpoints have no separation along the measured axis",
            "prediction_type": prediction_type,
        }

    max_deviation = 0.0
    for x, y in ordered[1:-1]:
        frac = (x - x0) / span
        predicted_y = y0 + frac * (y1 - y0)
        max_deviation = max(max_deviation, abs(y - predicted_y))

    predicted_shape = consequence.get("prediction")
    tolerance = consequence.get("tolerance", 0.05 * abs(y1 - y0) if abs(y1 - y0) > 1e-9 else 1e-6)
    is_linear = max_deviation <= tolerance

    if predicted_shape == "linear":
        status = "CONFIRMED" if is_linear else "CONTRADICTED"
    elif predicted_shape == "curved":
        status = "CONFIRMED" if not is_linear else "CONTRADICTED"
    else:
        return {
            "status": "UNDECIDABLE",
            "reason": f"unrecognized boundary_linearity prediction value '{predicted_shape}' (expected 'linear' or 'curved')",
            "prediction_type": prediction_type,
        }

    return {
        "status": status,
        "reason": f"max interior deviation from the straight-line prediction was {max_deviation:.4g} "
                  f"(tolerance {tolerance:.4g})",
        "prediction_type": prediction_type,
        "max_deviation": max_deviation,
        "tolerance": tolerance,
    }
