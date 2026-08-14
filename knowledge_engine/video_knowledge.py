"""Structured, temporally-grounded modeling knowledge extracted from a studied video.

Extraction itself is not automated by this module -- it requires a reviewer who has
actually read the source transcript (and, where visual claims are made, the
corresponding frames) and is recording a genuine claim, not inventing one from a
title or general Blender knowledge. This module provides the schema, validation, and
the transfer-test mechanism; a human or Claude populates KnowledgeItem instances by
reasoning about real source material.

Five knowledge types, chosen because they are what actually transfers to a new asset
-- not what the instructor merely said:

- PROCEDURE: a reproducible sequence of modeling actions.
- PRINCIPLE: a transferable modeling rule, independent of any specific asset.
- DECISION: a choice between alternative strategies, with the rejected alternative
  and the reason recorded, not just the path taken.
- VISUAL_CUE: a visible condition that triggered a modeling response.
- FAILURE: an observed mistake, its correction, and the lesson.

Every item starts at status CAPTURED and requires a separately recorded transfer test
before it can be trusted at runtime -- matching this project's own knowledge lifecycle
(docs/MASTER_DIRECTIVE.md: CAPTURED -> INTERPRETED -> CANDIDATE ->
EXPERIMENTALLY_TESTED -> TRANSFER_VALIDATED -> RUNTIME_VALIDATED -> PROMOTED) and the
same "no promotion without a declared replay" discipline already enforced for
session-mined skills in session_learning.py's apply_replay_result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_KNOWLEDGE_TYPES = {"PROCEDURE", "PRINCIPLE", "DECISION", "VISUAL_CUE", "FAILURE"}

VALID_STATUSES = {
    "CAPTURED",
    "INTERPRETED",
    "CANDIDATE",
    "EXPERIMENTALLY_TESTED",
    "TRANSFER_VALIDATED",
    "RUNTIME_VALIDATED",
    "PROMOTED",
    "CONTRADICTED",
    "NOT_YET_LEARNED",
}


@dataclass
class SourceTimestamp:
    """A time range inside a specific studied video's transcript/scene document."""

    source_id: str
    start_seconds: float
    end_seconds: float

    def validate(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")
        if self.start_seconds < 0:
            raise ValueError("start_seconds must be non-negative")
        if self.end_seconds < self.start_seconds:
            raise ValueError("end_seconds must be >= start_seconds")


@dataclass
class KnowledgeItem:
    knowledge_type: str
    claim: str
    source: SourceTimestamp
    confidence: float
    supporting_evidence: str
    status: str = "CAPTURED"
    rejected_alternative: str | None = None
    reason: str | None = None
    captured_while_building: str | None = None
    transfer_tests: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        if self.knowledge_type not in VALID_KNOWLEDGE_TYPES:
            raise ValueError(f"invalid knowledge_type: {self.knowledge_type}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid status: {self.status}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be in [0, 1]")
        if not self.claim.strip():
            raise ValueError("claim is required")
        if not self.supporting_evidence.strip():
            raise ValueError(
                "supporting_evidence is required -- a claim without cited evidence "
                "is not extraction, it is invention"
            )
        if self.knowledge_type == "DECISION" and not self.reason:
            raise ValueError("DECISION items require a reason")
        self.source.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "knowledge_type": self.knowledge_type,
            "claim": self.claim,
            "source": asdict(self.source),
            "confidence": self.confidence,
            "status": self.status,
            "supporting_evidence": self.supporting_evidence,
            "rejected_alternative": self.rejected_alternative,
            "reason": self.reason,
            "captured_while_building": self.captured_while_building,
            "transfer_tests": self.transfer_tests,
        }


def apply_transfer_test(item: dict[str, Any], transfer_test: dict[str, Any]) -> dict[str, Any]:
    """Record whether a knowledge item's claim actually transferred to a genuinely
    different, unseen asset.

    A technique only counts as learned if it improves performance on an unseen
    object -- never from summarizing the source or repeating its own terminology.
    transfer_test must name the asset it was tried on, what was expected, what was
    actually observed, and whether it counted as a pass.
    """
    required = {"target_asset", "expected_effect", "observed_effect", "pass", "evidence_path"}
    missing = sorted(required - set(transfer_test))
    if missing:
        raise ValueError(f"transfer test missing fields: {missing}")
    captured_from = item.get("captured_while_building")
    if captured_from and transfer_test["target_asset"] == captured_from:
        raise ValueError(
            "a transfer test must use a genuinely different asset than the one "
            "this knowledge was captured from"
        )
    updated = {**item, "transfer_tests": [*item.get("transfer_tests", []), transfer_test]}
    if transfer_test["pass"]:
        updated["status"] = "TRANSFER_VALIDATED"
    elif item["status"] in {"TRANSFER_VALIDATED", "RUNTIME_VALIDATED", "PROMOTED"}:
        updated["status"] = "CONTRADICTED"
    else:
        updated["status"] = "NOT_YET_LEARNED"
    return updated
