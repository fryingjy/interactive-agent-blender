"""Fail-closed evidence gate for tutorial-led Blender reproduction."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


CONSTRUCTION_COMMANDS = {
    "create_primitive", "create_curve", "create_revolved_profile", "create_profile_extrusion",
    "create_profile_loft", "create_quad_shell_grid", "create_quad_shell_sections",
    "create_quad_open_surface", "create_quad_annular_shell", "create_quad_layered_annular_shell",
    "create_authored_quad_mesh", "create_quad_radial_surface",
}
SURFACE_OPERATIONS = {
    "add_modifier", "set_edge_crease_by_ids", "set_bevel_weight_by_ids",
    "set_bevel_scoping", "set_shading", "set_smooth_by_angle",
}


def _sequence_operations(sequence: list[dict[str, Any]]) -> set[str]:
    """Collect direct commands and transaction operations without trusting one encoding."""
    operations: set[str] = set()
    for step in sequence:
        if not isinstance(step, dict):
            continue
        command = step.get("command")
        if isinstance(command, str):
            operations.add(command)
        transaction = step.get("transaction")
        if isinstance(transaction, dict) and isinstance(transaction.get("operation"), str):
            operations.add(transaction["operation"])
    return operations


def tutorial_modeling_gate_required(sequence_path: str | Path, sequence: list[dict[str, Any]]) -> bool:
    """Return whether a sequence is new tutorial construction rather than read-only review."""
    tutorial_path = any("tutorial-" in part.lower() or "_tutorial-" in part.lower() for part in Path(sequence_path).parts)
    mutates_geometry = bool(_sequence_operations(sequence) & CONSTRUCTION_COMMANDS)
    return tutorial_path and mutates_geometry


def tutorial_surface_gate_required(sequence_path: str | Path, sequence: list[dict[str, Any]]) -> bool:
    """Return whether a tutorial sequence attempts surface treatment after blockout."""
    tutorial_path = any("tutorial-" in part.lower() or "_tutorial-" in part.lower() for part in Path(sequence_path).parts)
    operations = _sequence_operations(sequence)
    return tutorial_path and bool(operations & SURFACE_OPERATIONS)


def validate_tutorial_premodeling_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate evidence that can actually constrain a tutorial reproduction's geometry."""
    issues: list[str] = []
    identity = payload.get("source_identity") if isinstance(payload.get("source_identity"), dict) else {}
    identity_pass = bool(identity.get("url") and identity.get("title") and identity.get("creator") and identity.get("duration_verified") is True)
    if not identity_pass:
        issues.append("source identity requires URL, title, creator and independently verified duration")

    access = payload.get("video_access") if isinstance(payload.get("video_access"), dict) else {}
    audiovisual_pass = access.get("video_inspected") is True and access.get("audio_inspected") is True
    if not audiovisual_pass:
        issues.append("the relevant tutorial range must be inspected as both video and audio")

    frames = payload.get("target_frames") if isinstance(payload.get("target_frames"), list) else []
    inspected = [item for item in frames if isinstance(item, dict) and item.get("independently_inspected") is True]
    frame_file_failures: list[str] = []
    for item in inspected:
        local_path = item.get("local_path")
        expected_digest = item.get("sha256")
        path = Path(local_path) if isinstance(local_path, str) and local_path else None
        if path is None or not path.is_file():
            frame_file_failures.append(f"{item.get('id', '<unnamed>')}: retained frame file is missing")
            continue
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if not isinstance(expected_digest, str) or actual_digest.lower() != expected_digest.lower():
            frame_file_failures.append(f"{item.get('id', '<unnamed>')}: retained frame SHA-256 does not match")
    frame_files_pass = bool(inspected) and not frame_file_failures
    if not frame_files_pass:
        issues.extend(frame_file_failures or ["at least one retained independently inspected frame file is required"])
    final_frames = [item for item in inspected if item.get("role") == "final_result"]
    geometry_frames = [item for item in inspected if item.get("usable_for_geometry") is True and item.get("role") in {"orthographic_reference", "dimensioned_reference", "depth_reference"}]
    final_result_pass = bool(final_frames)
    if not final_result_pass:
        issues.append("at least one independently inspected final-result frame is required")

    orthographic = [item for item in geometry_frames if item.get("projection") in {"orthographic", "dimensioned"}]
    unique_geometry_views = {str(item.get("view", "")).lower() for item in geometry_frames if item.get("view")}
    geometry_reference_pass = bool(orthographic) or len(unique_geometry_views) >= 2
    if not geometry_reference_pass:
        issues.append("geometry requires an orthographic/dimensioned reference or at least two independently inspected usable views")

    thumbnail_geometry_misuse = any(item.get("source_kind") == "thumbnail" and item.get("usable_for_geometry") is True for item in frames if isinstance(item, dict))
    if thumbnail_geometry_misuse:
        issues.append("a promotional thumbnail may document the final target but cannot authorize traced geometry")

    accepted_ids = {str(item.get("id")) for item in geometry_frames if item.get("id")}
    constraints = payload.get("constraints") if isinstance(payload.get("constraints"), list) else []
    high_salience_constraints = [
        item for item in constraints
        if isinstance(item, dict)
        and item.get("name")
        and item.get("high_salience") is True
        and item.get("measurement_status") == "MEASURED"
        and str(item.get("evidence_frame_id")) in accepted_ids
        and isinstance(item.get("value_normalized"), (int, float))
        and not isinstance(item.get("value_normalized"), bool)
        and 0.0 <= float(item["value_normalized"]) <= 1.0
    ]
    unique_constraint_names = {str(item["name"]) for item in high_salience_constraints}
    constraints_pass = len(high_salience_constraints) >= 3 and len(unique_constraint_names) == len(high_salience_constraints)
    if not constraints_pass:
        issues.append("at least three uniquely named, normalized high-salience constraints must cite geometry-usable frames")

    component_plan = payload.get("component_plan") if isinstance(payload.get("component_plan"), list) else []
    component_plan_pass = bool(component_plan) and all(isinstance(item, dict) and item.get("component") and item.get("construction_strategy") and bool(set(map(str, item.get("evidence_frame_ids", []))) & accepted_ids) for item in component_plan)
    if not component_plan_pass:
        issues.append("every planned component requires a construction strategy tied to geometry-usable evidence")

    unresolved = payload.get("unresolved_high_salience")
    unresolved_pass = isinstance(unresolved, list) and not unresolved
    if not unresolved_pass:
        issues.append("unresolved high-salience form or depth questions block construction")

    checks = {
        "source_identity_pass": identity_pass,
        "audiovisual_access_pass": audiovisual_pass,
        "retained_frame_files_pass": frame_files_pass,
        "independent_final_result_pass": final_result_pass,
        "geometry_reference_pass": geometry_reference_pass,
        "thumbnail_not_used_as_geometry_pass": not thumbnail_geometry_misuse,
        "measured_constraints_pass": constraints_pass,
        "component_plan_evidence_pass": component_plan_pass,
        "no_unresolved_high_salience_pass": unresolved_pass,
    }
    return {
        "schema_version": 1,
        "record_type": "TUTORIAL_PREMODELING_GATE_RESULT",
        "checks": checks,
        "accepted_geometry_frame_ids": sorted(accepted_ids),
        "measured_high_salience_constraint_count": len(high_salience_constraints),
        "issues": issues,
        "pass": all(checks.values()),
        "claim_boundary": "This authorizes only a reversible primary blockout; it does not prove tutorial fidelity or modeling quality.",
    }


def validate_tutorial_blockout_review(payload: dict[str, Any]) -> dict[str, Any]:
    """Require measured major-form acceptance before modifiers or shading may conceal the cage."""
    issues: list[str] = []
    renders = payload.get("renders") if isinstance(payload.get("renders"), list) else []
    inspected_views = {
        str(item.get("view", "")).lower()
        for item in renders
        if isinstance(item, dict) and item.get("independently_inspected") is True and item.get("base_cage_only") is True
    }
    render_pass = {"front", "isometric", "wireframe"} <= inspected_views
    if not render_pass:
        issues.append("front, isometric and wireframe base-cage renders must be independently inspected")

    comparisons = payload.get("constraint_comparisons") if isinstance(payload.get("constraint_comparisons"), list) else []
    high_salience = [item for item in comparisons if isinstance(item, dict) and item.get("high_salience") is True]
    measured_passes = [
        item for item in high_salience
        if item.get("status") == "PASS"
        and isinstance(item.get("measured_error"), (int, float))
        and isinstance(item.get("tolerance"), (int, float))
        and float(item["measured_error"]) <= float(item["tolerance"])
    ]
    constraint_pass = len(high_salience) >= 3 and len(measured_passes) == len(high_salience)
    if not constraint_pass:
        issues.append("at least three high-salience measured comparisons must all pass their declared tolerances")

    tickets = payload.get("primary_mismatch_tickets")
    no_primary_mismatch_pass = isinstance(tickets, list) and not tickets
    if not no_primary_mismatch_pass:
        issues.append("unresolved primary-form mismatch tickets block surface treatment")

    decision_pass = payload.get("decision") == "ADVANCE_TO_SURFACE"
    if not decision_pass:
        issues.append("blockout review decision must be ADVANCE_TO_SURFACE")

    critic = payload.get("semantic_critic") if isinstance(payload.get("semantic_critic"), dict) else {}
    critic_analysis = critic.get("analysis") if isinstance(critic.get("analysis"), dict) else {}
    critic_artifacts = (
        critic.get("provenance", {}).get("view_artifacts", [])
        if isinstance(critic.get("provenance"), dict) else []
    )
    critic_artifacts_pass = bool(critic_artifacts)
    for artifact in critic_artifacts:
        if not isinstance(artifact, dict):
            critic_artifacts_pass = False
            break
        for role in ("reference", "candidate"):
            path_value = artifact.get(role)
            expected = artifact.get(f"{role}_sha256")
            path = Path(path_value) if isinstance(path_value, str) and path_value else None
            if path is None or not path.is_file() or not isinstance(expected, str):
                critic_artifacts_pass = False
                break
            if hashlib.sha256(path.read_bytes()).hexdigest().lower() != expected.lower():
                critic_artifacts_pass = False
                break
        if not critic_artifacts_pass:
            break
        if str(artifact.get("reference_sha256", "")).lower() == str(artifact.get("candidate_sha256", "")).lower():
            critic_artifacts_pass = False
            break
    semantic_critic_pass = (
        critic.get("record_type") == "GEMINI_REFERENCE_CRITIC"
        and critic_artifacts_pass
        and critic_analysis.get("target_identity_matches") is True
        and critic_analysis.get("decision") == "ADVANCE_TO_SURFACE_CANDIDATE"
    )
    if not semantic_critic_pass:
        issues.append("a hash-valid semantic critic must identify the target and return ADVANCE_TO_SURFACE_CANDIDATE")

    checks = {
        "base_cage_render_review_pass": render_pass,
        "high_salience_constraints_pass": constraint_pass,
        "no_primary_mismatch_tickets_pass": no_primary_mismatch_pass,
        "advance_decision_pass": decision_pass,
        "semantic_critic_pass": semantic_critic_pass,
    }
    return {
        "schema_version": 1,
        "record_type": "TUTORIAL_BLOCKOUT_REVIEW_GATE_RESULT",
        "checks": checks,
        "issues": issues,
        "pass": all(checks.values()),
        "claim_boundary": "This permits surface-control work only; it is not a final fidelity score.",
    }
