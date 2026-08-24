"""Create a durable, artifact-bound checkpoint for one visual modeling iteration."""

from __future__ import annotations

from typing import Any

from knowledge_engine.gemini_reference_critic import (
    derive_correction_directive,
    validate_critic_record,
)
from knowledge_engine.iteration_control import evaluate_iteration_budget


def build_visual_stage_checkpoint(
    critic_record: dict[str, Any],
    *,
    target_id: str,
    stage: str,
    scene_revision: int,
    candidate_views: dict[str, str],
    authorized_reference_hashes: set[str],
    recent_decisions: list[dict[str, Any]],
    previous_correction_focus: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind one stage judgment to exact files, revision, focus, and repair budget.

    A checkpoint deliberately chooses one dominant correction. Parallel low-salience fixes make
    before/after attribution ambiguous and are deferred until the dominant mismatch is resolved.
    """
    if not isinstance(stage, str) or not stage.strip():
        raise ValueError("stage must be a non-empty string")
    if not isinstance(scene_revision, int) or isinstance(scene_revision, bool) or scene_revision < 0:
        raise ValueError("scene_revision must be a non-negative integer")
    validate_critic_record(
        critic_record,
        expected_target_id=target_id,
        expected_views=candidate_views,
        authorized_reference_hashes=authorized_reference_hashes,
    )
    directive = derive_correction_directive(critic_record["analysis"])
    focus = None
    budget = None
    if directive["disposition"] != "ADVANCE":
        ticket = directive.get("ticket") or {}
        focus = {
            "component_id": ticket.get("component_id"),
            "root_cause": ticket.get("root_cause"),
            "repair_scope": ticket.get("repair_scope"),
            "correction_goal": ticket.get("correction_goal"),
            "prohibited_shortcut": directive.get("prohibited_shortcut"),
        }
        budget = evaluate_iteration_budget(
            recent_decisions,
            stage=stage,
            target_region=focus["component_id"],
        )
    if directive["disposition"] == "ADVANCE":
        decision = "ADVANCE"
    elif budget and budget["decision"] == "CHANGE_STRATEGY":
        decision = "CHANGE_STRATEGY"
    else:
        decision = "CORRECT_ONE_DOMINANT_MISMATCH"
    return {
        "schema_version": 1,
        "record_type": "VISUAL_MODELING_STAGE_CHECKPOINT",
        "target_id": target_id,
        "stage": stage,
        "scene_revision": scene_revision,
        "candidate_views": dict(sorted(candidate_views.items())),
        "authorized_reference_sha256": sorted(authorized_reference_hashes),
        "critic_request_sha256": critic_record["provenance"]["request_sha256"],
        "previous_correction_focus": previous_correction_focus,
        "correction_focus": focus,
        "iteration_budget": budget,
        "decision": decision,
        "parallel_repairs_allowed": False if focus else None,
        "pass": decision == "ADVANCE",
        "claim_boundary": "ADVANCE means this artifact-bound checkpoint passed; it does not authorize a different render, revision, target, or stage.",
    }
