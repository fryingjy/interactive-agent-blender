"""Evaluate named, normalized reference constraints before blockout advance.

Whole-mask IoU and overall aspect ratio can look healthy while a handle,
panel, knob, or negative space is visibly wrong.  This module deliberately
evaluates those local relationships as declared evidence.  It is a correction
aid, not a claim that a numeric score replaces visual review.
"""

from __future__ import annotations

from math import hypot
from typing import Any


def _number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    return float(value)


def _point(value: Any, label: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{label} must be a two-value normalized point")
    return _number(value[0], f"{label}[0]"), _number(value[1], f"{label}[1]")


def _box(value: Any, label: str) -> tuple[float, float, float, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a box object")
    left = _number(value.get("left"), f"{label}.left")
    top = _number(value.get("top"), f"{label}.top")
    right = _number(value.get("right"), f"{label}.right")
    bottom = _number(value.get("bottom"), f"{label}.bottom")
    if right <= left or bottom <= top:
        raise ValueError(f"{label} must have positive width and height")
    return left, top, right, bottom


def _box_error(expected: tuple[float, float, float, float], actual: tuple[float, float, float, float]) -> dict:
    expected_width, expected_height = expected[2] - expected[0], expected[3] - expected[1]
    actual_width, actual_height = actual[2] - actual[0], actual[3] - actual[1]
    boundary_error = max(abs(a - b) for a, b in zip(expected, actual))
    center_error = hypot(
        ((expected[0] + expected[2]) - (actual[0] + actual[2])) / 2,
        ((expected[1] + expected[3]) - (actual[1] + actual[3])) / 2,
    )
    return {
        "max_boundary_error": boundary_error,
        "center_error": center_error,
        "width_error": abs(actual_width - expected_width),
        "height_error": abs(actual_height - expected_height),
    }


def evaluate_reference_constraints(contract: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Compare a declared normalized constraint contract to observations.

    Contract entries use one of three kinds:
    ``point`` (``target: [x, y]``), ``box`` (``target: {left, top, right,
    bottom}``), or ``scalar`` (``target: number``).  Each has an explicit
    non-negative tolerance.  Observations are keyed by constraint id and
    must contain matching normalized values.  Missing high-salience evidence
    blocks the result rather than being silently omitted.
    """
    constraints = contract.get("constraints")
    if not isinstance(constraints, list) or not constraints:
        raise ValueError("contract.constraints must be a non-empty list")
    observations = observed.get("observations")
    if not isinstance(observations, dict):
        raise ValueError("observed.observations must be an object keyed by constraint id")

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in constraints:
        if not isinstance(item, dict):
            raise ValueError("each constraint must be an object")
        identifier = str(item.get("id", "")).strip()
        kind = str(item.get("kind", "")).strip().lower()
        if not identifier or identifier in seen:
            raise ValueError("constraint ids must be non-empty and unique")
        seen.add(identifier)
        if kind not in {"point", "box", "scalar"}:
            raise ValueError(f"unsupported constraint kind for {identifier}: {kind}")
        tolerance = _number(item.get("tolerance"), f"{identifier}.tolerance")
        if tolerance < 0:
            raise ValueError(f"{identifier}.tolerance must be non-negative")
        importance = str(item.get("importance", "high")).lower()
        if importance not in {"high", "medium", "low"}:
            raise ValueError(f"{identifier}.importance must be high, medium, or low")

        if identifier not in observations:
            results.append({"id": identifier, "kind": kind, "importance": importance, "status": "MISSING", "pass": False})
            continue
        actual_value = observations[identifier]
        if kind == "point":
            expected = _point(item.get("target"), f"{identifier}.target")
            actual = _point(actual_value, f"observations.{identifier}")
            error = hypot(expected[0] - actual[0], expected[1] - actual[1])
            details = {"distance_error": error}
        elif kind == "box":
            expected = _box(item.get("target"), f"{identifier}.target")
            actual = _box(actual_value, f"observations.{identifier}")
            details = _box_error(expected, actual)
            error = details["max_boundary_error"]
        else:
            expected = _number(item.get("target"), f"{identifier}.target")
            actual = _number(actual_value, f"observations.{identifier}")
            error = abs(expected - actual)
            details = {"absolute_error": error}
        results.append({
            "id": identifier,
            "kind": kind,
            "importance": importance,
            "status": "PASS" if error <= tolerance else "FAIL",
            "pass": error <= tolerance,
            "tolerance": tolerance,
            "error": error,
            "target": item["target"],
            "observed": actual_value,
            **details,
        })

    missing = [row["id"] for row in results if row["status"] == "MISSING"]
    failed = [row["id"] for row in results if row["status"] == "FAIL"]
    blocking = [row["id"] for row in results if not row["pass"] and row["importance"] == "high"]
    tickets = sorted(
        (
            {
                "constraint_id": row["id"],
                "importance": row["importance"],
                "status": row["status"],
                "severity": 1.0 if row["status"] == "MISSING" else row.get("error", 0.0) / max(row.get("tolerance", 1.0), 1e-12),
            }
            for row in results if not row["pass"]
        ),
        key=lambda ticket: ({"high": 0, "medium": 1, "low": 2}[ticket["importance"]], -ticket["severity"], ticket["constraint_id"]),
    )
    for priority, ticket in enumerate(tickets, start=1):
        ticket["priority"] = priority
    return {
        "schema_version": 1,
        "record_type": "LOCAL_REFERENCE_CONSTRAINT_EVALUATION",
        "target_id": contract.get("target_id"),
        "claim_boundary": "Named normalized constraints localize correction work; passing them does not prove visual fidelity or replace human review.",
        "constraints": results,
        "missing_constraint_ids": missing,
        "failed_constraint_ids": failed,
        "blocking_constraint_ids": blocking,
        "tickets": tickets,
        "pass": not blocking,
    }
