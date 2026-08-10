"""Machine-checkable stage gates and multi-channel professional review aggregation.

These gates validate evidence presence and declared thresholds. They do not replace human artistic
judgment and never turn a narrow technical check into a professional-capability claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from blender_ops.stage_gates import STAGE_REQUIREMENTS, evaluate_stage_gate


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


def aggregate_professional_review(channels: list[ReviewChannel], *, threshold: float = 0.8) -> dict:
    if not channels:
        raise ValueError("at least one review channel is required")
    for channel in channels:
        channel.validate()
    total_weight = sum(channel.weight for channel in channels)
    score = sum(channel.score * channel.weight for channel in channels) / total_weight
    hard_failures = [channel.name for channel in channels if not channel.hard_pass]
    return {
        "score": round(score, 6),
        "threshold": threshold,
        "hard_failures": hard_failures,
        "pass": score >= threshold and not hard_failures,
        "channels": [channel.__dict__ for channel in channels],
    }
