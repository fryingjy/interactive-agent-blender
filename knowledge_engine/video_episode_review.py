"""Fail-closed independent review of speech-to-visible-action video episodes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_POSITIONS = {"BEFORE", "DURING", "AFTER"}
VALID_ALIGNMENTS = {"ALIGNED", "MISMATCH", "UNVERIFIED"}


@dataclass(frozen=True)
class FrameObservation:
    timestamp: float
    path: str
    temporal_position: str
    observed_fact: str

    def validate(self) -> None:
        if self.timestamp < 0:
            raise ValueError("frame timestamp must be non-negative")
        if self.temporal_position not in VALID_POSITIONS:
            raise ValueError(f"invalid temporal position: {self.temporal_position}")
        if not self.path.strip() or not self.observed_fact.strip():
            raise ValueError("frame path and observed fact are required")


@dataclass(frozen=True)
class TranscriptEvidence:
    start_seconds: float
    end_seconds: float
    text: str

    def validate(self) -> None:
        if self.start_seconds < 0 or self.end_seconds < self.start_seconds:
            raise ValueError("invalid transcript timestamp range")
        if not self.text.strip():
            raise ValueError("transcript text is required")


@dataclass(frozen=True)
class EpisodeReviewEvidence:
    source_id: str
    start_seconds: float
    end_seconds: float
    visible_action_claim: str
    spoken_reason_claim: str
    source_identity_verified: bool
    independent_reviewer: bool
    frame_observations: tuple[FrameObservation, ...]
    transcript_segments: tuple[TranscriptEvidence, ...]
    visible_action_observed: bool | None
    speech_action_alignment: str
    source_identity_mismatch: bool = False

    def validate(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")
        if self.start_seconds < 0 or self.end_seconds <= self.start_seconds:
            raise ValueError("episode must have a positive timestamp range")
        if not self.visible_action_claim.strip() or not self.spoken_reason_claim.strip():
            raise ValueError("visible action and spoken reason claims are required")
        if self.speech_action_alignment not in VALID_ALIGNMENTS:
            raise ValueError(f"invalid speech/action alignment: {self.speech_action_alignment}")
        if self.source_identity_verified and self.source_identity_mismatch:
            raise ValueError("source identity cannot be both verified and mismatched")
        for frame in self.frame_observations:
            frame.validate()
        for segment in self.transcript_segments:
            segment.validate()


def review_episode_alignment(
    evidence: EpisodeReviewEvidence,
    *,
    minimum_frame_observations: int = 3,
    require_existing_frame_paths: bool = True,
) -> dict[str, Any]:
    """Classify an episode as VERIFIED, PENDING_REVIEW, or REJECTED.

    Missing evidence remains pending. Explicit source, visible-action, or speech/action
    contradictions are rejected. A model's own VIDEO claim is never treated as independent review.
    """
    evidence.validate()
    if minimum_frame_observations < 1:
        raise ValueError("minimum_frame_observations must be positive")

    positions = {frame.temporal_position for frame in evidence.frame_observations}
    before_timed = any(
        frame.temporal_position == "BEFORE" and frame.timestamp <= evidence.start_seconds
        for frame in evidence.frame_observations
    )
    during_timed = any(
        frame.temporal_position == "DURING"
        and evidence.start_seconds <= frame.timestamp <= evidence.end_seconds
        for frame in evidence.frame_observations
    )
    after_timed = any(
        frame.temporal_position == "AFTER" and frame.timestamp >= evidence.end_seconds
        for frame in evidence.frame_observations
    )
    transcript_overlap = any(
        segment.end_seconds > evidence.start_seconds
        and segment.start_seconds < evidence.end_seconds
        for segment in evidence.transcript_segments
    )
    frame_paths_exist = bool(evidence.frame_observations) and all(
        Path(frame.path).is_file() for frame in evidence.frame_observations
    )
    checks = {
        "source_identity_verified": evidence.source_identity_verified,
        "independent_reviewer": evidence.independent_reviewer,
        "minimum_frame_observations": (
            len(evidence.frame_observations) >= minimum_frame_observations
        ),
        "before_during_after_positions": VALID_POSITIONS <= positions,
        "temporal_positions_bracket_episode": before_timed and during_timed and after_timed,
        "frame_paths_exist": frame_paths_exist if require_existing_frame_paths else True,
        "visible_action_observed": evidence.visible_action_observed is True,
        "speech_overlaps_episode": transcript_overlap,
        "speech_action_alignment": evidence.speech_action_alignment == "ALIGNED",
    }
    contradictions = []
    if evidence.source_identity_mismatch:
        contradictions.append("source_identity_mismatch")
    if evidence.independent_reviewer and evidence.visible_action_observed is False:
        contradictions.append("visible_action_mismatch")
    if evidence.speech_action_alignment == "MISMATCH":
        contradictions.append("speech_action_mismatch")

    if contradictions:
        disposition = "REJECTED"
    elif all(checks.values()):
        disposition = "VERIFIED"
    else:
        disposition = "PENDING_REVIEW"
    return {
        "source_id": evidence.source_id,
        "episode": [evidence.start_seconds, evidence.end_seconds],
        "disposition": disposition,
        "pass": disposition == "VERIFIED",
        "checks": checks,
        "failures": [name for name, passed in checks.items() if not passed],
        "contradictions": contradictions,
        "frame_observation_count": len(evidence.frame_observations),
        "claim_boundary": (
            "This gate verifies evidence alignment only. It does not validate the transferable "
            "modeling principle or promote knowledge without reproduction and transfer."
        ),
    }
