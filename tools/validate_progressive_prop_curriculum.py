"""Validate ordering, gates, authority boundaries, and active state of the prop ladder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "knowledge" / "foundation" / "progressive_prop_benchmark_curriculum.json"


def validate(data):
    errors = []
    props = [prop for tier in data.get("tiers", []) for prop in tier.get("props", [])]
    malformed = [index for index, prop in enumerate(props) if not isinstance(prop, dict)]
    if malformed:
        errors.append(f"every prop must be an object; malformed indexes: {malformed}")
    valid_props = [prop for prop in props if isinstance(prop, dict)]
    ids = [prop.get("id") for prop in valid_props]
    titles = [prop.get("title") for prop in valid_props]
    if any(not isinstance(title, str) or not title.strip() for title in titles):
        errors.append("every prop requires a non-empty title")
    if any(not isinstance(prop.get("difficulty_reason"), str) or not prop["difficulty_reason"].strip() for prop in valid_props):
        errors.append("every prop requires a non-empty difficulty_reason")
    if ids != list(range(1, 31)):
        errors.append(f"prop IDs must be exactly 1..30 in order; got {ids}")
    if len(titles) != len(set(titles)):
        errors.append("prop titles must be unique")
    tier_ids = [tier.get("tier") for tier in data.get("tiers", [])]
    if tier_ids != list(range(1, 7)):
        errors.append(f"tier IDs must be exactly 1..6; got {tier_ids}")
    gate_ids = [gate.get("id") for gate in data.get("gates", [])]
    if gate_ids != list("ABCDEFG"):
        errors.append(f"gate IDs must be A..G; got {gate_ids}")
    if any(not gate.get("criteria") for gate in data.get("gates", [])):
        errors.append("every gate requires at least one criterion")
    provenance = data.get("provenance", {})
    if provenance.get("role") != "user_supplied_project_guidance":
        errors.append("curriculum must remain labeled user-supplied guidance")
    if provenance.get("does_not_override_direct_user_instructions") is not True:
        errors.append("authority boundary must preserve direct user instructions")
    policy = data.get("promotion_policy", {})
    if policy.get("human_review_required") is not True:
        errors.append("promotion must require human review")
    active = data.get("active_state", {})
    active_id = active.get("active_prop_id")
    paused = (
        active_id is None
        and active.get("active_prop") is None
        and active.get("active_target_variant") is None
        and active.get("authorization") == "LADDER_PAUSED"
        and active.get("modeling_authorized") is False
    )
    active_prop_valid = (
        isinstance(active_id, int)
        and active_id in ids
        and len(titles) == 30
        and active.get("active_prop") == titles[active_id - 1]
    )
    if not (paused or active_prop_valid):
        errors.append("active state must point to one declared prop ID and matching title")
    authorization = active.get("authorization")
    modeling_authorized = active.get("modeling_authorized")
    valid_locked = authorization in {"REFERENCE_ANALYSIS_REQUIRED", "EXTERNAL_REVIEW_REQUIRED"} and modeling_authorized is False
    valid_direct = authorization == "DIRECT_USER_AUTHORIZATION" and modeling_authorized is True
    if not (paused or valid_locked or valid_direct):
        errors.append("active authorization and modeling_authorized must form a supported paused, locked, or direct-user pair")
    if len(data.get("evidence_required", [])) < 15:
        errors.append("evidence contract is incomplete")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    errors = validate(data)
    props = [prop for tier in data["tiers"] for prop in tier["props"]]
    report = {
        "validator": "progressive_prop_benchmark_curriculum",
        "input": str(args.input.relative_to(ROOT)),
        "tier_count": len(data["tiers"]),
        "prop_count": len(props),
        "gate_count": len(data["gates"]),
        "active_prop_id": data["active_state"]["active_prop_id"],
        "modeling_authorized": data["active_state"]["modeling_authorized"],
        "errors": errors,
        "pass": not errors,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__":
    main()
