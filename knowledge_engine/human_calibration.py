"""Frozen human calibration for semantic reference-review decisions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from knowledge_engine.gemini_reference_critic import validate_critic_record


HUMAN_VERDICTS = {"ACCEPT_VISIBLE_MATCH", "REJECT_MAJOR_FORM"}
AUTOMATED_TO_HUMAN = {
    "ADVANCE_TO_SURFACE_CANDIDATE": "ACCEPT_VISIBLE_MATCH",
    "CORRECT_PRIMARY_FORM": "REJECT_MAJOR_FORM",
    "REBUILD_REPRESENTATION": "REJECT_MAJOR_FORM",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_calibration_package(
    public_manifest: dict[str, Any], anchor: dict[str, Any], *, root: Path
) -> dict[str, Any]:
    cases = public_manifest.get("cases")
    expected = anchor.get("expected_cases")
    if not isinstance(cases, list) or len(cases) < 4:
        raise ValueError("human calibration requires at least four cases")
    if not isinstance(expected, list) or len(expected) != len(cases):
        raise ValueError("calibration anchor must cover every public case")
    public_ids = [case.get("case_id") for case in cases]
    expected_ids = [case.get("case_id") for case in expected]
    if len(public_ids) != len(set(public_ids)) or set(public_ids) != set(expected_ids):
        raise ValueError("calibration case ids must be unique and agree across manifest and anchor")
    non_control_targets = {
        case.get("target_id") for case in cases if case.get("case_kind") == "REAL_MODEL_REVIEW"
    }
    if None in non_control_targets or len(non_control_targets) < 3:
        raise ValueError("calibration requires three real-model target families")

    results = []
    expected_by_id = {case["case_id"]: case for case in expected}
    expected_verdicts = set()
    for case in cases:
        expected_case = expected_by_id[case["case_id"]]
        critic_path = root / expected_case["critic_artifact"]
        critic_hash = sha256_file(critic_path)
        run = json.loads(critic_path.read_text(encoding="utf-8"))
        for record in run.get("records", []):
            validate_critic_record(record, expected_target_id=expected_case["target_id"])
        critic_role_hashes = {
            role: {
                view[f"{role}_sha256"]
                for record in run.get("records", [])
                for view in record["provenance"]["view_artifacts"]
            }
            for role in ("reference", "candidate")
        }
        artifact_checks = []
        for role in ("reference", "candidate"):
            path = root / case[role]
            wanted = case[f"{role}_sha256"]
            if path.is_file():
                actual = sha256_file(path)
                check = {
                    "role": role,
                    "path": case[role],
                    "availability": "LOCAL_FILE",
                    "actual": actual,
                    "pass": actual == wanted and wanted in critic_role_hashes[role],
                }
            else:
                explicitly_non_retained = (
                    role == "reference"
                    and case.get("reference_retention") == "SOURCE_MEDIA_NOT_RETAINED"
                )
                check = {
                    "role": role,
                    "path": case[role],
                    "availability": "NON_RETAINED_HASH_BOUND" if explicitly_non_retained else "MISSING",
                    "actual": None,
                    "pass": explicitly_non_retained and wanted in critic_role_hashes[role],
                }
            artifact_checks.append(check)
        automated_decision = run["consensus"]["decision"]
        expected_verdict = AUTOMATED_TO_HUMAN.get(automated_decision)
        if expected_verdict is None:
            raise ValueError(f"case {case['case_id']} has non-calibratable evaluator decision {automated_decision}")
        expected_verdicts.add(expected_verdict)
        checks_pass = (
            all(check["pass"] for check in artifact_checks)
            and critic_hash == expected_case["critic_sha256"]
            and automated_decision == expected_case["automated_decision"]
        )
        results.append({
            "case_id": case["case_id"],
            "target_id": case["target_id"],
            "artifact_checks": artifact_checks,
            "critic_hash_pass": critic_hash == expected_case["critic_sha256"],
            "automated_decision": automated_decision,
            "expected_human_verdict": expected_verdict,
            "pass": checks_pass,
        })
    if expected_verdicts != HUMAN_VERDICTS:
        raise ValueError("calibration must contain both positive and rejection decisions")
    return {
        "schema_version": 1,
        "record_type": "HUMAN_CALIBRATION_PACKAGE_VALIDATION",
        "case_count": len(results),
        "real_target_count": len(non_control_targets),
        "results": results,
        "pass": all(result["pass"] for result in results),
    }


def score_human_calibration(
    public_manifest: dict[str, Any],
    anchor: dict[str, Any],
    response: dict[str, Any],
    *,
    root: Path,
) -> dict[str, Any]:
    package = validate_calibration_package(public_manifest, anchor, root=root)
    if response.get("reviewer_type") != "human":
        raise ValueError("calibration authority must come from a human reviewer")
    reviewer_id = response.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError("calibration response requires reviewer_id")
    answers = response.get("cases")
    if not isinstance(answers, list):
        raise ValueError("calibration response cases must be a list")
    answer_by_id = {item.get("case_id"): item for item in answers if isinstance(item, dict)}
    expected_ids = {item["case_id"] for item in package["results"]}
    if len(answer_by_id) != len(answers) or set(answer_by_id) != expected_ids:
        raise ValueError("calibration response must answer every case exactly once")

    results = []
    for expected in package["results"]:
        answer = answer_by_id[expected["case_id"]]
        verdict = answer.get("verdict")
        if verdict not in HUMAN_VERDICTS:
            raise ValueError(f"invalid human verdict for {expected['case_id']}")
        notes = answer.get("notes", "")
        if not isinstance(notes, str) or (verdict == "REJECT_MAJOR_FORM" and not notes.strip()):
            raise ValueError("a human rejection requires concrete notes")
        agrees = verdict == expected["expected_human_verdict"]
        results.append({
            "case_id": expected["case_id"],
            "target_id": expected["target_id"],
            "automated_decision": expected["automated_decision"],
            "human_verdict": verdict,
            "notes": notes,
            "agreement": agrees,
        })
    passed = package["pass"] and all(result["agreement"] for result in results)
    return {
        "schema_version": 1,
        "record_type": "HELD_OUT_HUMAN_VISUAL_CALIBRATION_RESULT",
        "reviewer_type": "human",
        "reviewer_id": reviewer_id,
        "results": results,
        "agreement_count": sum(result["agreement"] for result in results),
        "case_count": len(results),
        "decision": "PASS" if passed else "EVALUATOR_HUMAN_DISAGREEMENT",
        "pass": passed,
        "claim_boundary": "This calibrates frozen semantic accept/reject decisions on retained images. It does not establish professional modeling skill, hidden-form correctness, topology quality, or unfamiliar-prop generalization.",
    }
