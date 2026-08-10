"""Mine decision evidence while preventing untested self-generated rules from promotion."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


SUCCESS = {"accepted", "repaired"}
FAILURE = {"rejected", "mistake_detected", "reverted"}


def read_decision_logs(paths: list[str | Path]) -> list[dict]:
    events = []
    for source in paths:
        path = Path(source)
        for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            item["_source"] = str(path)
            item["_line"] = line_number
            events.append(item)
    return events


def _operation(item: dict) -> str:
    action = item.get("chosen_action") or item.get("action") or {}
    if isinstance(action, str):
        return action
    return str(action.get("op") or action.get("operation") or "UNKNOWN")


def mine_session_events(events: list[dict], *, min_assets: int = 2, min_successes: int = 3) -> dict:
    evaluations = Counter(str(item.get("evaluation", "unknown")) for item in events)
    by_operation = defaultdict(lambda: {"successes": 0, "failures": 0, "assets": set(), "examples": []})
    for item in events:
        operation = _operation(item)
        evaluation = str(item.get("evaluation", "unknown"))
        bucket = by_operation[operation]
        asset = str(item.get("asset_id") or item.get("target") or item.get("session_id") or "unknown")
        bucket["assets"].add(asset)
        bucket["successes"] += int(evaluation in SUCCESS)
        bucket["failures"] += int(evaluation in FAILURE)
        if len(bucket["examples"]) < 5:
            bucket["examples"].append({"source": item.get("_source"), "line": item.get("_line"), "evaluation": evaluation})

    candidates = []
    for operation, bucket in sorted(by_operation.items()):
        if bucket["successes"] < min_successes or len(bucket["assets"]) < min_assets:
            continue
        confidence = bucket["successes"] / max(1, bucket["successes"] + bucket["failures"])
        candidates.append({
            "operation": operation,
            "successes": bucket["successes"],
            "failures": bucket["failures"],
            "asset_count": len(bucket["assets"]),
            "confidence": round(confidence, 4),
            "status": "CANDIDATE_REQUIRES_REPLAY",
            "examples": bucket["examples"],
        })
    return {
        "event_count": len(events),
        "evaluation_counts": dict(sorted(evaluations.items())),
        "operation_count": len(by_operation),
        "candidates": candidates,
        "promoted": [],
        "promotion_policy": "No session-mined candidate is promoted until a separately declared replay/transfer test passes.",
    }


def apply_replay_result(candidate: dict, replay: dict) -> dict:
    required = {"replay_id", "different_asset", "expected", "observed", "pass", "evidence_path"}
    missing = sorted(required - set(replay))
    if missing:
        raise ValueError(f"replay result missing fields: {missing}")
    if not replay["different_asset"]:
        status = "CANDIDATE_REQUIRES_TRANSFER"
    elif not replay["pass"]:
        status = "CONTRADICTED_BY_REPLAY"
    else:
        status = "REPLAY_VALIDATED"
    return {**candidate, "status": status, "replay": replay}
