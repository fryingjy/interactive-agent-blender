"""Strict replay of immutable, real-reference evaluator failures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from knowledge_engine.gemini_reference_critic import validate_critic_record


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(record: Any, dotted_path: str) -> Any:
    value = record
    for part in dotted_path.split("."):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def _assertion_passes(actual: Any, assertion: dict[str, Any]) -> bool:
    operator = assertion["operator"]
    expected = assertion["expected"]
    if operator == "eq":
        return actual == expected
    if operator == "contains":
        return expected in actual
    if operator == "min":
        return float(actual) >= float(expected)
    if operator == "max":
        return float(actual) <= float(expected)
    raise ValueError(f"unsupported assertion operator: {operator}")


def evaluate_anchor(anchor: dict[str, Any], *, root: Path) -> dict[str, Any]:
    cases = anchor.get("cases")
    if not isinstance(cases, list) or len(cases) < 3:
        raise ValueError("real-reference evaluator anchor requires at least three cases")
    target_ids = {case.get("target_id") for case in cases}
    if None in target_ids or len(target_ids) < 3:
        raise ValueError("real-reference evaluator anchor requires at least three target families")

    results = []
    for case in cases:
        path = root / case["artifact"]
        artifact_hash = _sha256(path)
        hash_pass = artifact_hash == case["artifact_sha256"]
        record = json.loads(path.read_text(encoding="utf-8"))
        validation_error = None
        if case["kind"] == "semantic_critic":
            try:
                validate_critic_record(record, expected_target_id=case["target_id"])
            except (KeyError, TypeError, ValueError) as exc:
                validation_error = str(exc)
        elif case["kind"] == "semantic_critic_ensemble":
            try:
                for critic_record in record["records"]:
                    validate_critic_record(critic_record, expected_target_id=case["target_id"])
            except (KeyError, TypeError, ValueError) as exc:
                validation_error = str(exc)
        elif case["kind"] != "deterministic_comparison":
            raise ValueError(f"unsupported evaluator case kind: {case['kind']}")

        assertion_results = []
        for assertion in case["assertions"]:
            actual = _resolve(record, assertion["path"])
            assertion_results.append({
                **assertion,
                "actual": actual,
                "pass": _assertion_passes(actual, assertion),
            })
        case_pass = hash_pass and validation_error is None and all(
            result["pass"] for result in assertion_results
        )
        results.append({
            "id": case["id"],
            "target_id": case["target_id"],
            "kind": case["kind"],
            "artifact": case["artifact"],
            "artifact_sha256": artifact_hash,
            "hash_pass": hash_pass,
            "validation_error": validation_error,
            "assertions": assertion_results,
            "pass": case_pass,
        })
    return {
        "schema_version": 1,
        "record_type": "REAL_REFERENCE_EVALUATOR_REGRESSION",
        "case_count": len(results),
        "target_count": len(target_ids),
        "results": results,
        "pass": all(result["pass"] for result in results),
        "claim_boundary": "This replays three immutable historical real-reference failures. It protects evaluator rejection/localization behavior but does not prove successful modeling or replace held-out human calibration.",
    }
