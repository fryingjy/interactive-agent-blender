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
    observations: dict[str, dict[str, Any]] | None = None,
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
    if prediction_type in {"numeric_range", "boolean_state"}:
        return _evaluate_independent_observation(
            consequence,
            reference_item,
            observations=observations or {},
        )
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


def _reference_value(reference_item: Any, key: str) -> Any:
    if isinstance(reference_item, dict):
        return reference_item.get(key)
    return getattr(reference_item, key, None)


def _evaluate_independent_observation(
    consequence: dict[str, Any],
    reference_item: Any,
    *,
    observations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate a prediction against separately recorded evidence.

    The observation is deliberately looked up by ID rather than accepted inline
    on the strategy.  This keeps a candidate from carrying both its answer and
    its own supposed proof, which was the circularity found in the 2026-08-19
    runtime-skill audit.
    """
    prediction_type = consequence.get("prediction_type")
    observation_id = consequence.get("observation_id")
    observation = observations.get(observation_id)
    if not observation:
        return {
            "status": "UNDECIDABLE",
            "reason": f"independent observation '{observation_id}' is missing",
            "prediction_type": prediction_type,
        }

    expected_reference = _reference_value(reference_item, "reference_id")
    bindings = {
        "reference_id": expected_reference,
        "view": consequence.get("view"),
        "property": consequence.get("property"),
    }
    mismatches = [
        key for key, expected in bindings.items()
        if expected and observation.get(key) != expected
    ]
    if mismatches:
        return {
            "status": "UNDECIDABLE",
            "reason": "observation binding mismatch: " + ", ".join(mismatches),
            "prediction_type": prediction_type,
            "observation_id": observation_id,
        }

    if prediction_type == "boolean_state":
        observed = observation.get("value")
        predicted = consequence.get("prediction")
        if not isinstance(observed, bool) or not isinstance(predicted, bool):
            return {
                "status": "UNDECIDABLE",
                "reason": "boolean_state requires boolean observed and predicted values",
                "prediction_type": prediction_type,
                "observation_id": observation_id,
            }
        return {
            "status": "CONFIRMED" if observed == predicted else "CONTRADICTED",
            "reason": f"observed {observed!r}; predicted {predicted!r}",
            "prediction_type": prediction_type,
            "observation_id": observation_id,
        }

    predicted = consequence.get("prediction")
    observed = observation.get("value")
    if not (
        isinstance(predicted, dict)
        and isinstance(observed, dict)
        and {"min", "max"} <= set(predicted)
        and {"min", "max"} <= set(observed)
    ):
        return {
            "status": "UNDECIDABLE",
            "reason": "numeric_range requires independent and predicted {min, max} intervals",
            "prediction_type": prediction_type,
            "observation_id": observation_id,
        }
    try:
        predicted_min, predicted_max = float(predicted["min"]), float(predicted["max"])
        observed_min, observed_max = float(observed["min"]), float(observed["max"])
    except (TypeError, ValueError):
        return {
            "status": "UNDECIDABLE",
            "reason": "numeric_range interval bounds must be numeric",
            "prediction_type": prediction_type,
            "observation_id": observation_id,
        }
    if predicted_min > predicted_max or observed_min > observed_max:
        return {
            "status": "UNDECIDABLE",
            "reason": "numeric_range interval minimum exceeds maximum",
            "prediction_type": prediction_type,
            "observation_id": observation_id,
        }
    overlap = max(0.0, min(predicted_max, observed_max) - max(predicted_min, observed_min))
    observed_span = observed_max - observed_min
    if observed_span <= 1e-12:
        confirmed = predicted_min <= observed_min <= predicted_max
        overlap_fraction = 1.0 if confirmed else 0.0
    else:
        overlap_fraction = overlap / observed_span
        confirmed = overlap_fraction >= float(consequence.get("minimum_observed_overlap", 0.8))
    return {
        "status": "CONFIRMED" if confirmed else "CONTRADICTED",
        "reason": (
            f"predicted interval [{predicted_min:g}, {predicted_max:g}] covers "
            f"{overlap_fraction:.1%} of observed interval [{observed_min:g}, {observed_max:g}]"
        ),
        "prediction_type": prediction_type,
        "observation_id": observation_id,
        "overlap_fraction": overlap_fraction,
        "unit": observation.get("unit", ""),
    }


def rank_competing_hypotheses(
    candidates: list[dict[str, Any]],
    reference_items: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    *,
    minimum_confirmed_views: int = 2,
) -> dict[str, Any]:
    """Rank competing representations without silently inventing certainty.

    A winner must be unique, free of contradictions, and confirmed by the
    requested number of distinct views.  Ties, missing references, and
    unsupported prediction types remain explicit instead of falling back to
    list order or prose confidence.
    """
    if len(candidates) < 2:
        raise ValueError("competing-hypothesis ranking requires at least two candidates")
    reports = []
    for candidate in candidates:
        results = []
        for consequence in candidate.get("predicted_consequences", []):
            reference_id = consequence.get("reference_id")
            reference_item = reference_items.get(reference_id)
            if reference_item is None:
                result = {
                    "status": "UNDECIDABLE",
                    "reason": f"reference item '{reference_id}' is missing",
                    "prediction_type": consequence.get("prediction_type"),
                }
            else:
                result = evaluate_predicted_consequence(
                    consequence,
                    reference_item,
                    landmarks=consequence.get("landmarks"),
                    observations=observations,
                )
            results.append({"consequence": consequence, "result": result})
        confirmed_views = sorted({
            item["consequence"].get("view")
            for item in results
            if item["result"]["status"] == "CONFIRMED" and item["consequence"].get("view")
        })
        counts = {
            status: sum(item["result"]["status"] == status for item in results)
            for status in ("CONFIRMED", "CONTRADICTED", "UNDECIDABLE")
        }
        viable = counts["CONTRADICTED"] == 0 and len(confirmed_views) >= minimum_confirmed_views
        reports.append({
            "name": candidate.get("name"),
            "representation": candidate.get("representation"),
            "results": results,
            "counts": counts,
            "confirmed_views": confirmed_views,
            "score": counts["CONFIRMED"] - counts["CONTRADICTED"],
            "viable": viable,
        })

    viable = [item for item in reports if item["viable"]]
    best_score = max((item["score"] for item in viable), default=None)
    winners = [item for item in viable if item["score"] == best_score]
    selected = winners[0]["name"] if len(winners) == 1 else None
    if selected:
        disposition = "SELECTED"
        reason = f"unique contradiction-free candidate confirmed across at least {minimum_confirmed_views} views"
    elif not viable:
        disposition = "INSUFFICIENT_EVIDENCE"
        reason = "no candidate met the contradiction-free cross-view evidence requirement"
    else:
        disposition = "AMBIGUOUS"
        reason = "multiple viable candidates remain tied"
    return {
        "schema_version": 1,
        "disposition": disposition,
        "selected_candidate": selected,
        "reason": reason,
        "minimum_confirmed_views": minimum_confirmed_views,
        "candidates": reports,
    }
