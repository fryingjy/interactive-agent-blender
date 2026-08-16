"""Revision-bound human authorization for a machine-ready reference board.

Reference readiness and post-model visual review are separate authorities.  This
module validates the handoff between them without manufacturing a human decision
or allowing a decision for an older board to authorize changed evidence.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any


APPROVE_REVERSIBLE_BLOCKOUT = "APPROVE_REVERSIBLE_BLOCKOUT"
RESEARCH_OR_PLAN_CORRECTION = "RESEARCH_OR_PLAN_CORRECTION"
ALLOWED_DECISIONS = {APPROVE_REVERSIBLE_BLOCKOUT, RESEARCH_OR_PLAN_CORRECTION}


def file_sha256(path: Path) -> str:
    """Return a lowercase SHA-256 digest of the exact file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be non-empty text")
    return value.strip()


def validate_reference_board_gate(
    gate: dict[str, Any], *, audit_path: Path, reference_plan_path: Path
) -> dict[str, Any]:
    """Validate the immutable pending gate against its current evidence files."""
    if not isinstance(gate, dict):
        raise ValueError("reference-board gate must be an object")
    if gate.get("schema_version") != 1 or gate.get("record_type") != "REFERENCE_BOARD_HUMAN_REVIEW_GATE":
        raise ValueError("unsupported reference-board gate schema")
    for key in ("gate_id", "target_id", "target", "review_scope"):
        _require_text(gate, key)
    if gate.get("machine_disposition") != "READY_TO_MODEL":
        raise ValueError("human authorization requires a machine disposition of READY_TO_MODEL")
    if gate.get("human_review_status") != "PENDING_USER_REVIEW":
        raise ValueError("the immutable gate contract must remain PENDING_USER_REVIEW")
    if gate.get("modeling_authorized") is not False:
        raise ValueError("the pending gate contract cannot authorize modeling")
    allowed = gate.get("allowed_decisions")
    if not isinstance(allowed, list) or set(allowed) != ALLOWED_DECISIONS or len(allowed) != 2:
        raise ValueError("allowed_decisions must contain exactly the two supported decisions")
    expected_audit = file_sha256(audit_path)
    expected_plan = file_sha256(reference_plan_path)
    if gate.get("audit_sha256") != expected_audit:
        raise ValueError("reference-board gate is stale: audit_sha256 does not match current audit")
    if gate.get("reference_plan_sha256") != expected_plan:
        raise ValueError("reference-board gate is stale: reference_plan_sha256 does not match current plan")
    try:
        audit_payload = json.loads(audit_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("machine reference audit is not valid JSON") from exc
    reports = audit_payload.get("reports") if isinstance(audit_payload, dict) else None
    if isinstance(reports, list):
        matching = [
            item.get("audit") for item in reports
            if isinstance(item, dict)
            and isinstance(item.get("audit"), dict)
            and item["audit"].get("target_id") == gate["target_id"]
        ]
        if len(matching) != 1:
            raise ValueError("machine reference audit must contain exactly one matching target report")
        audit = matching[0]
    else:
        audit = audit_payload
    if not isinstance(audit, dict) or audit.get("target_id") != gate["target_id"]:
        raise ValueError("machine reference audit target_id does not match the gate")
    if audit.get("pass") is not True or audit.get("disposition") != "READY_TO_MODEL":
        raise ValueError("current machine reference audit is not READY_TO_MODEL")
    return gate


def validate_reference_board_review(
    review: dict[str, Any],
    gate: dict[str, Any],
    *,
    audit_path: Path,
    reference_plan_path: Path,
) -> dict[str, Any]:
    """Validate a human decision against the exact current board contract."""
    validate_reference_board_gate(gate, audit_path=audit_path, reference_plan_path=reference_plan_path)
    if not isinstance(review, dict):
        raise ValueError("reference-board review must be an object")
    if review.get("schema_version") != 1 or review.get("record_type") != "REFERENCE_BOARD_HUMAN_DECISION":
        raise ValueError("unsupported reference-board review schema")
    for key in (
        "gate_id", "target_id", "target", "review_scope", "audit_sha256",
        "reference_plan_sha256", "reviewer_id", "reviewed_at",
    ):
        _require_text(review, key)
    for key in ("gate_id", "target_id", "target", "review_scope", "audit_sha256", "reference_plan_sha256"):
        if review[key] != gate[key]:
            raise ValueError(f"review {key} does not match the current reference-board gate")
    if review.get("reviewer_type") != "human":
        raise ValueError("only a human reviewer can authorize a reference board")
    try:
        reviewed_at = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("reviewed_at must be an ISO-8601 timestamp") from exc
    if reviewed_at.tzinfo is None:
        raise ValueError("reviewed_at must include a timezone")
    decision = review.get("decision")
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"decision must be one of {sorted(ALLOWED_DECISIONS)}")
    notes = review.get("notes", "")
    if not isinstance(notes, str):
        raise ValueError("notes must be text")
    if decision == RESEARCH_OR_PLAN_CORRECTION and not notes.strip():
        raise ValueError("a correction decision requires concrete notes")
    expected_authorization = decision == APPROVE_REVERSIBLE_BLOCKOUT
    if review.get("modeling_authorized") is not expected_authorization:
        raise ValueError("modeling_authorized contradicts the human decision")
    return review


def build_reference_board_handoff(
    review: dict[str, Any],
    gate: dict[str, Any],
    *,
    audit_path: Path,
    reference_plan_path: Path,
) -> dict[str, Any]:
    """Build a deterministic, retainable authorization or correction handoff."""
    validated = validate_reference_board_review(
        review, gate, audit_path=audit_path, reference_plan_path=reference_plan_path
    )
    approved = validated["decision"] == APPROVE_REVERSIBLE_BLOCKOUT
    canonical_review = json.dumps(validated, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": 1,
        "record_type": "REFERENCE_BOARD_HUMAN_REVIEW_HANDOFF",
        "gate_id": gate["gate_id"],
        "target_id": gate["target_id"],
        "review_sha256": hashlib.sha256(canonical_review).hexdigest(),
        "review": validated,
        "disposition": "REFERENCE_BOARD_APPROVED" if approved else "REFERENCE_BOARD_CORRECTION_REQUIRED",
        "modeling_authorized": approved,
        "authorized_stage": "REVERSIBLE_PRIMARY_BLOCKOUT_ONLY" if approved else None,
        "next_action": "BEGIN_REVERSIBLE_PRIMARY_BLOCKOUT" if approved else "REVISE_REFERENCE_SET_OR_CONSTRUCTION_PLAN",
        "limitation": (
            "This record preserves a claimed human decision bound to the exact audited board. "
            "Approval authorizes only the reversible primary blockout described by review_scope; "
            "it does not approve later modeling stages or prove reviewer identity cryptographically."
        ),
    }
