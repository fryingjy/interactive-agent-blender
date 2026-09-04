"""Machine-checkable stage gates and multi-channel professional review aggregation.

These gates validate evidence presence and declared thresholds. They do not replace human artistic
judgment and never turn a narrow technical check into a professional-capability claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from blender_ops.stage_gates import evaluate_stage_gate

__all__ = ["ReviewChannel", "aggregate_professional_review", "evaluate_stage_gate"]


@dataclass(frozen=True)
class ReviewChannel:
    name: str
    score: float
    weight: float = 1.0
    hard_pass: bool = True
    evidence: str = ""

    def validate(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"{self.name} score must be in [0, 1]")
        if self.weight <= 0:
            raise ValueError(f"{self.name} weight must be positive")
        if not self.evidence.strip():
            raise ValueError(f"{self.name} requires an evidence reference")


def aggregate_professional_review(
    channels: list[ReviewChannel],
    *,
    required_criteria: list[str],
    threshold: float = 0.8,
) -> dict:
    """Aggregate declared review criteria without permitting silent omissions."""
    if not channels:
        raise ValueError("at least one review channel is required")
    if (
        not required_criteria
        or any(not isinstance(name, str) or not name.strip() for name in required_criteria)
        or len(required_criteria) != len(set(required_criteria))
    ):
        raise ValueError("required_criteria must contain unique non-empty names")
    for channel in channels:
        channel.validate()
    names = [channel.name for channel in channels]
    if len(names) != len(set(names)):
        raise ValueError("review channel names must be unique")
    uncovered = sorted(set(required_criteria) - set(names))
    unexpected = sorted(set(names) - set(required_criteria))
    total_weight = sum(channel.weight for channel in channels)
    score = sum(channel.score * channel.weight for channel in channels) / total_weight
    hard_failures = [channel.name for channel in channels if not channel.hard_pass]
    return {
        "score": round(score, 6),
        "threshold": threshold,
        "hard_failures": hard_failures,
        "required_criteria": list(required_criteria),
        "uncovered_criteria": uncovered,
        "unexpected_criteria": unexpected,
        "criteria_coverage_pass": not uncovered and not unexpected,
        "pass": score >= threshold and not hard_failures and not uncovered and not unexpected,
        "channels": [channel.__dict__ for channel in channels],
    }
