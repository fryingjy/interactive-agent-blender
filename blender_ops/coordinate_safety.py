"""Generic, asset-agnostic detector for a geometry edit that jumped to what
looks like a different coordinate frame -- the observable symptom shared by
the recurring world/local coordinate-space bug (see coordinate_frames.py's
docstring for the three real, independent cases this is grounded in).

Pure Python, no bpy dependency: takes the ``local_bounds``/``local_centroid``
fields state_probe.mesh_health() reports before and after a mutation, and
flags when the centroid moved by an amount large relative to the shape's own
size. This is informational, not a hard block -- the same precedent
DecisionTransaction.verify() already sets for op_delta (see its own
docstring): a real signal the agent should notice, not something to silently
miss or silently refuse to proceed on.
"""

from __future__ import annotations

from typing import Any


def _diagonal(bounds: dict[str, list[float]]) -> float:
    lo, hi = bounds["min"], bounds["max"]
    return sum((h - l) ** 2 for l, h in zip(lo, hi)) ** 0.5


def _distance(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def detect_implausible_shift(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    max_relative_shift: float = 3.0,
) -> dict[str, Any]:
    """Flag an implausible centroid jump between two mesh_health() readings.

    ``before``/``after`` must each carry ``local_bounds`` (``{"min": [...],
    "max": [...]}``) and ``local_centroid`` ([x, y, z]) -- callers lacking
    either field get an explicit UNAVAILABLE result rather than a silent
    pass, so the absence of evidence is never confused with the absence of
    a problem.
    """
    for label, state in (("before", before), ("after", after)):
        if not isinstance(state, dict) or "local_bounds" not in state or "local_centroid" not in state:
            return {
                "flagged": False,
                "status": "UNAVAILABLE",
                "reason": f"{label} state lacks local_bounds/local_centroid -- cannot evaluate",
            }

    diagonal = _diagonal(before["local_bounds"])
    shift = _distance(before["local_centroid"], after["local_centroid"])

    if diagonal <= 1e-9:
        # A single-point or degenerate before-shape has no meaningful scale
        # to compare against; any nonzero shift is reported but not flagged.
        flagged = False
        reason = (
            f"before-shape diagonal is ~0 (degenerate/point geometry); centroid shift {shift:.4g} "
            f"reported but not evaluated against a relative threshold"
        )
    else:
        relative_shift = shift / diagonal
        flagged = relative_shift > max_relative_shift
        reason = (
            f"centroid shifted {shift:.4g} ({relative_shift:.2f}x the shape's own bounding-box "
            f"diagonal of {diagonal:.4g}); threshold is {max_relative_shift:.2f}x"
        )
        if flagged:
            reason = (
                "possible coordinate-frame mixup: " + reason +
                " -- this magnitude of shift for a local mesh edit is the same symptom the "
                "Swingline 747 recess/hinge-throat and donut/mug foam-placement bugs both showed"
            )

    return {"flagged": flagged, "status": "EVALUATED", "reason": reason}
