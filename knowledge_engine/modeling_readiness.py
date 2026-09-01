"""Repository-wide hold gate for reference-driven asset construction.

The hold is deliberately separate from per-target reference authorization.  A target can have
valid source hashes and still be unsafe to model when the perception/evaluator system is known to
misattribute camera, segmentation, or pose error to geometry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


VALID_STATUSES = {"ACTIVE", "CLEARED"}
VALID_SCOPES = {"SYSTEM_VALIDATION_FIXTURE", "REPLAY_EXISTING_TARGET", "NEW_REFERENCE_PROP"}


def load_modeling_readiness(path: str | Path) -> dict[str, Any]:
    policy_path = Path(path)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    validate_modeling_readiness_policy(policy)
    return policy


def validate_modeling_readiness_policy(policy: dict[str, Any]) -> None:
    if not isinstance(policy, dict) or policy.get("schema_version") != 1:
        raise ValueError("modeling readiness policy must be a schema-version 1 object")
    if policy.get("record_type") != "REFERENCE_MODELING_READINESS":
        raise ValueError("modeling readiness policy has the wrong record_type")
    status = policy.get("status")
    if status not in VALID_STATUSES:
        raise ValueError(f"modeling readiness status must be one of {sorted(VALID_STATUSES)}")
    allowed = policy.get("allowed_scopes")
    if not isinstance(allowed, list) or any(item not in VALID_SCOPES for item in allowed):
        raise ValueError("allowed_scopes contains an unknown modeling scope")
    gates = policy.get("clearance_gates")
    if not isinstance(gates, list) or not gates:
        raise ValueError("modeling readiness policy requires clearance_gates")
    ids = []
    for gate in gates:
        if not isinstance(gate, dict) or not isinstance(gate.get("id"), str):
            raise ValueError("each clearance gate requires an id")
        if gate.get("status") not in {"PASS", "FAIL", "NOT_RUN"}:
            raise ValueError("clearance gate status must be PASS, FAIL, or NOT_RUN")
        ids.append(gate["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("clearance gate ids must be unique")
    if status == "CLEARED" and any(gate["status"] != "PASS" for gate in gates):
        raise ValueError("a CLEARED policy requires every clearance gate to pass")


def evaluate_modeling_scope(policy: dict[str, Any], scope: str) -> dict[str, Any]:
    validate_modeling_readiness_policy(policy)
    if scope not in VALID_SCOPES:
        raise ValueError(f"unknown modeling scope: {scope}")
    allowed = policy["status"] == "CLEARED" or scope in policy["allowed_scopes"]
    failing = [gate["id"] for gate in policy["clearance_gates"] if gate["status"] != "PASS"]
    return {
        "schema_version": 1,
        "record_type": "REFERENCE_MODELING_SCOPE_DECISION",
        "policy_status": policy["status"],
        "scope": scope,
        "allowed": allowed,
        "open_clearance_gates": failing,
        "reason": (
            "Scope is explicitly allowed for system validation while the hold remains active."
            if allowed and policy["status"] == "ACTIVE"
            else "All system-readiness gates have passed."
            if allowed
            else "Reference-driven asset construction remains blocked by the active system-repair hold."
        ),
    }
