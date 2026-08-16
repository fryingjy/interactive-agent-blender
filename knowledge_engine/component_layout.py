"""Compare observed component bounds without hiding local layout errors in a global mask."""

from __future__ import annotations

from typing import Any


_FIELDS = ("left", "top", "right", "bottom")


def _rect(value: Any, *, component_id: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"component {component_id!r} must be an object")
    missing = [field for field in _FIELDS if field not in value]
    if missing:
        raise ValueError(f"component {component_id!r} is missing {missing}")
    result = {field: float(value[field]) for field in _FIELDS}
    if any(number < 0.0 or number > 1.0 for number in result.values()):
        raise ValueError(f"component {component_id!r} bounds must be normalized to [0, 1]")
    if result["right"] < result["left"] or result["bottom"] < result["top"]:
        raise ValueError(f"component {component_id!r} has inverted bounds")
    return result


def compare_component_layout(reference_components: dict[str, Any], candidate_components: dict[str, Any]) -> dict[str, Any]:
    """Compare named normalized component rectangles.

    This deliberately reports measurement disagreement rather than a generic
    visual-pass boolean. Source rectangles may originate from an observed
    product image, while candidate rectangles originate from a controlled
    component-mask pass; callers must retain the reference-projection and
    annotation uncertainty alongside this output.
    """
    if not isinstance(reference_components, dict) or not isinstance(candidate_components, dict):
        raise ValueError("reference_components and candidate_components must be objects")
    reference = {name: _rect(rect, component_id=name) for name, rect in reference_components.items()}
    candidate = {name: _rect(rect, component_id=name) for name, rect in candidate_components.items()}
    missing = sorted(set(reference) - set(candidate))
    extra = sorted(set(candidate) - set(reference))
    comparisons: dict[str, Any] = {}
    tickets: list[dict[str, Any]] = []
    for component_id in sorted(set(reference) & set(candidate)):
        expected, observed = reference[component_id], candidate[component_id]
        coordinate_errors = {field: abs(observed[field] - expected[field]) for field in _FIELDS}
        expected_size = {"width": expected["right"] - expected["left"], "height": expected["bottom"] - expected["top"]}
        observed_size = {"width": observed["right"] - observed["left"], "height": observed["bottom"] - observed["top"]}
        size_errors = {field: abs(observed_size[field] - expected_size[field]) for field in expected_size}
        severity = max(*coordinate_errors.values(), *size_errors.values())
        comparisons[component_id] = {
            "reference": expected,
            "candidate": observed,
            "coordinate_errors": coordinate_errors,
            "reference_size": expected_size,
            "candidate_size": observed_size,
            "size_errors": size_errors,
            "mean_coordinate_error": sum(coordinate_errors.values()) / len(coordinate_errors),
            "severity": severity,
        }
        if severity > 0:
            tickets.append({"type": "component_layout", "target": component_id, "severity": severity, "evidence": comparisons[component_id]})
    for component_id in missing:
        tickets.append({"type": "missing_component", "target": component_id, "severity": 1.0, "evidence": None})
    for component_id in extra:
        tickets.append({"type": "extra_component", "target": component_id, "severity": 0.5, "evidence": None})
    tickets.sort(key=lambda item: (-item["severity"], item["type"], item["target"]))
    for priority, ticket in enumerate(tickets, start=1):
        ticket["priority"] = priority
    severities = [item["severity"] for item in comparisons.values()]
    return {
        "schema_version": 1,
        "record_type": "NORMALIZED_COMPONENT_LAYOUT_COMPARISON",
        "components": comparisons,
        "mean_component_severity": sum(severities) / len(severities) if severities else None,
        "worst_component_severity": max(severities, default=None),
        "missing_components": missing,
        "extra_components": extra,
        "tickets": tickets,
        "claim_boundary": "Normalized bounds localize component placement and proportion disagreement. They do not calibrate a perspective source image, prove 3D depth, or establish visual acceptance.",
    }
