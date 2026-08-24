"""Bounded visual-repair control for reference-modeling loops.

Repeated Blender edits are not evidence of progress. This module turns recent decision records
into a fail-closed continue/change-strategy decision so an asset cannot consume unlimited repair
passes while the same visible mismatch remains.
"""

from __future__ import annotations

import math
from typing import Any


def evaluate_iteration_budget(
    decisions: list[dict[str, Any]],
    *,
    stage: str,
    target_region: str | None,
    max_attempts: int = 3,
    stagnation_limit: int = 2,
    minimum_improvement: float = 0.01,
) -> dict[str, Any]:
    if max_attempts < 1 or stagnation_limit < 1:
        raise ValueError("iteration limits must be positive")
    if not math.isfinite(minimum_improvement) or minimum_improvement < 0:
        raise ValueError("minimum_improvement must be finite and non-negative")
    relevant = [
        item for item in decisions
        if isinstance(item, dict)
        and item.get("stage") == stage
        and item.get("target_region") == target_region
        and item.get("status") in {"committed", "accepted", "failed", "rejected"}
    ]
    measured: list[dict[str, Any]] = []
    for item in relevant:
        before = item.get("before_score")
        after = item.get("after_score")
        if (
            isinstance(before, (int, float)) and not isinstance(before, bool)
            and isinstance(after, (int, float)) and not isinstance(after, bool)
            and math.isfinite(float(before)) and math.isfinite(float(after))
        ):
            measured.append({**item, "improvement": float(after) - float(before)})
    trailing_stagnant = 0
    for item in reversed(measured):
        if item["improvement"] < minimum_improvement:
            trailing_stagnant += 1
        else:
            break
    attempts_exhausted = len(relevant) >= max_attempts
    stagnated = trailing_stagnant >= stagnation_limit
    change_strategy = attempts_exhausted or stagnated
    return {
        "schema_version": 1,
        "record_type": "MODELING_ITERATION_BUDGET",
        "stage": stage,
        "target_region": target_region,
        "attempt_count": len(relevant),
        "measured_attempt_count": len(measured),
        "trailing_stagnant_attempts": trailing_stagnant,
        "attempts_remaining": max(0, max_attempts - len(relevant)),
        "decision": "CHANGE_STRATEGY" if change_strategy else "CONTINUE_BOUNDED_REPAIR",
        "reason": (
            "maximum repair attempts reached"
            if attempts_exhausted
            else "consecutive measured repairs produced no material visual improvement"
            if stagnated
            else "bounded repair budget remains"
        ),
        "pass": not change_strategy,
    }
