"""Fail-closed evidence gate for tutorial-led Blender reproduction."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

from knowledge_engine.gemini_reference_critic import validate_critic_record


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


def procedural_fixture_sequence(sequence_path: str | Path) -> bool:
    """Return whether the path explicitly identifies a controlled lab/test rather than an asset."""
    tokens = {part.lower().replace("_", "-") for part in Path(sequence_path).parts}
    return any("-lab" in token or token.startswith("lab-") or token in {"tests", "test"} for token in tokens)


def reference_modeling_gate_required(sequence_path: str | Path, sequence: list[dict[str, Any]]) -> bool:
    """Require structured reference readiness for every non-tutorial, non-lab asset build."""
    return (
        bool(_sequence_operations(sequence) & CONSTRUCTION_COMMANDS)
        and not tutorial_modeling_gate_required(sequence_path, sequence)
        and not procedural_fixture_sequence(sequence_path)
    )


def asset_surface_gate_required(sequence_path: str | Path, sequence: list[dict[str, Any]]) -> bool:
    """Surface treatment on any real asset requires an exact-render blockout review."""
    return bool(_sequence_operations(sequence) & SURFACE_OPERATIONS) and not procedural_fixture_sequence(sequence_path)


def asset_mutation_gate_required(sequence_path: str | Path, sequence: list[dict[str, Any]]) -> bool:
    """Identify any real-asset mutation, including local corrections that create no new object."""
    safe_prefixes = ("get_", "list_", "check_", "audit_", "render_", "poll_")
    safe_commands = {"heartbeat", "save_file", "save_checkpoint"}
    for step in sequence:
        if not isinstance(step, dict):
            continue
        if isinstance(step.get("transaction"), dict) or isinstance(step.get("advance_with_component_coverage"), dict):
            return True
        command = step.get("command")
        if isinstance(command, str) and command not in safe_commands and not command.startswith(safe_prefixes):
            return True
    return False


def validate_tutorial_premodeling_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate evidence that can actually constrain a tutorial reproduction's geometry."""
    issues: list[str] = []
    target_id = payload.get("target_id")
    target_variant = payload.get("target_variant")
    target_identity_pass = all(isinstance(value, str) and value.strip() for value in (target_id, target_variant))
    if not target_identity_pass:
        issues.append("tutorial evidence requires an explicit target_id and target_variant")
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
    frame_ids = [str(item.get("id")) for item in inspected if item.get("id")]
    frame_ids_pass = len(frame_ids) == len(inspected) and len(frame_ids) == len(set(frame_ids))
    if not frame_ids_pass:
        issues.append("every inspected frame requires a unique non-empty id")
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
        "target_identity_pass": target_identity_pass,
        "source_identity_pass": identity_pass,
        "audiovisual_access_pass": audiovisual_pass,
        "retained_frame_files_pass": frame_files_pass,
        "unique_frame_ids_pass": frame_ids_pass,
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
        "authorized_reference_sha256": sorted({
            str(item["sha256"]).lower()
            for item in geometry_frames
            if isinstance(item.get("sha256"), str)
        }),
        "measured_high_salience_constraint_count": len(high_salience_constraints),
        "issues": issues,
        "pass": all(checks.values()),
        "claim_boundary": "This authorizes only a reversible primary blockout; it does not prove tutorial fidelity or modeling quality.",
    }


def validate_tutorial_blockout_review(payload: dict[str, Any]) -> dict[str, Any]:
    """Require measured major-form acceptance before modifiers or shading may conceal the cage."""
    issues: list[str] = []
    target_id = payload.get("target_id")
    component_ids = payload.get("component_ids")
    scene_revision = payload.get("scene_revision")
    target_binding_pass = (
        isinstance(target_id, str) and bool(target_id.strip())
        and isinstance(component_ids, list) and bool(component_ids)
        and all(isinstance(item, str) and item.strip() for item in component_ids)
        and len(component_ids) == len(set(component_ids))
        and isinstance(scene_revision, int) and not isinstance(scene_revision, bool) and scene_revision >= 0
    )
    if not target_binding_pass:
        issues.append("blockout review requires target_id, unique component_ids, and a non-negative scene_revision")

    renders = payload.get("renders") if isinstance(payload.get("renders"), list) else []
    inspected_views: set[str] = set()
    render_hashes: dict[str, str] = {}
    semantic_views: dict[str, str] = {}
    render_artifacts_pass = bool(renders)
    for item in renders:
        if not isinstance(item, dict):
            render_artifacts_pass = False
            continue
        view = str(item.get("view") or "").strip().lower()
        path_value = item.get("local_path")
        expected_digest = item.get("sha256")
        path = Path(path_value) if isinstance(path_value, str) and path_value else None
        valid = (
            bool(view)
            and item.get("independently_inspected") is True
            and item.get("base_cage_only") is True
            and item.get("scene_revision") == scene_revision
            and path is not None and path.is_file()
            and isinstance(expected_digest, str) and len(expected_digest) == 64
        )
        if valid:
            actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            valid = actual_digest.lower() == expected_digest.lower()
        if not valid or view in inspected_views:
            render_artifacts_pass = False
            continue
        inspected_views.add(view)
        render_hashes[view] = actual_digest
        if item.get("semantic_candidate") is True:
            semantic_views[view] = actual_digest
    render_pass = render_artifacts_pass and {"front", "isometric", "wireframe"} <= inspected_views and bool(semantic_views)
    if not render_pass:
        issues.append("front, isometric and wireframe base-cage renders must be hash-bound to one scene revision; at least one must be a semantic candidate")

    comparisons = payload.get("constraint_comparisons") if isinstance(payload.get("constraint_comparisons"), list) else []
    high_salience = [item for item in comparisons if isinstance(item, dict) and item.get("high_salience") is True]
    measured_passes = [
        item for item in high_salience
        if item.get("status") == "PASS"
        and isinstance(item.get("name"), str) and item["name"].strip()
        and str(item.get("candidate_view", "")).strip().lower() in render_hashes
        and isinstance(item.get("measured_error"), (int, float))
        and not isinstance(item.get("measured_error"), bool)
        and math.isfinite(float(item["measured_error"]))
        and float(item["measured_error"]) >= 0.0
        and isinstance(item.get("tolerance"), (int, float))
        and not isinstance(item.get("tolerance"), bool)
        and math.isfinite(float(item["tolerance"]))
        and float(item["tolerance"]) > 0.0
        and float(item["measured_error"]) <= float(item["tolerance"])
    ]
    names = [str(item.get("name")) for item in measured_passes]
    constraint_pass = (
        len(high_salience) >= 3
        and len(measured_passes) == len(high_salience)
        and len(names) == len(set(names))
    )
    if not constraint_pass:
        issues.append("at least three uniquely named, finite, non-negative high-salience comparisons must pass against retained candidate views")

    tickets = payload.get("primary_mismatch_tickets")
    no_primary_mismatch_pass = isinstance(tickets, list) and not tickets
    if not no_primary_mismatch_pass:
        issues.append("unresolved primary-form mismatch tickets block surface treatment")

    decision_pass = payload.get("decision") == "ADVANCE_TO_SURFACE"
    if not decision_pass:
        issues.append("blockout review decision must be ADVANCE_TO_SURFACE")

    critic = payload.get("semantic_critic") if isinstance(payload.get("semantic_critic"), dict) else {}
    authorized_hashes_raw = payload.get("authorized_reference_sha256")
    authorized_hashes = {
        str(item).lower() for item in authorized_hashes_raw
        if isinstance(item, str) and len(item) == 64
    } if isinstance(authorized_hashes_raw, list) else set()
    semantic_critic_pass = False
    try:
        validate_critic_record(
            critic,
            expected_target_id=target_id if isinstance(target_id, str) else None,
            expected_views=semantic_views,
            authorized_reference_hashes=authorized_hashes,
        )
        critic_analysis = critic["analysis"]
        semantic_critic_pass = (
            bool(authorized_hashes)
            and critic_analysis.get("target_identity_matches") is True
            and critic_analysis.get("decision") == "ADVANCE_TO_SURFACE_CANDIDATE"
        )
    except (KeyError, TypeError, ValueError) as exc:
        issues.append(f"semantic critic validation failed: {exc}")
    if not semantic_critic_pass:
        issues.append("the current, target-bound semantic critic must review these exact renders and return ADVANCE_TO_SURFACE_CANDIDATE")

    checks = {
        "target_and_revision_binding_pass": target_binding_pass,
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
