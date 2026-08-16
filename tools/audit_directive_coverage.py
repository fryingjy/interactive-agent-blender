"""Fail-closed structural audit for the durable directive coverage matrix.

The matrix makes current evidence and outstanding boundaries inspectable.  A
structurally passing audit never upgrades a PARTIAL directive status into a
professional-capability claim.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER_DIRECTIVE = ROOT / "docs" / "MASTER_DIRECTIVE.md"
MATRIX = ROOT / "knowledge" / "foundation" / "directive_coverage_matrix.json"
ALLOWED_STATUSES = {
    "IMPLEMENTED_VERIFIED",
    "PARTIAL",
    "EXTERNAL_REVIEW_REQUIRED",
    "DEFERRED_BY_PRIORITY",
}
HEADING_PATTERN = re.compile(r"^##\s+(\d+[a-z]?)\.\s+(.+)$", re.MULTILINE)


def directive_sections(path: Path = MASTER_DIRECTIVE) -> dict[str, str]:
    return {match.group(1): match.group(2).strip() for match in HEADING_PATTERN.finditer(path.read_text(encoding="utf-8"))}


def is_repository_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = Path(value)
    if candidate.is_absolute():
        return False
    try:
        (ROOT / candidate).resolve().relative_to(ROOT.resolve())
    except ValueError:
        return False
    return (ROOT / candidate).exists()


def audit_matrix(payload: dict[str, object], sections: dict[str, str]) -> dict[str, object]:
    errors: list[str] = []
    requirements = payload.get("requirements")
    if not isinstance(requirements, list):
        return {"structural_status": "FAIL", "errors": ["requirements must be a list"]}

    matrix_ids: list[str] = []
    status_counts = {status: 0 for status in sorted(ALLOWED_STATUSES)}
    for index, record in enumerate(requirements):
        prefix = f"requirements[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        section_id = record.get("id")
        if not isinstance(section_id, str) or not section_id:
            errors.append(f"{prefix}.id must be a non-empty string")
            continue
        matrix_ids.append(section_id)
        if section_id not in sections:
            errors.append(f"{prefix}.id {section_id!r} is not a master-directive heading")
        title = record.get("title")
        if title != sections.get(section_id):
            errors.append(f"{prefix}.title does not match master directive heading for {section_id}")
        status = record.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.status is invalid")
        else:
            status_counts[status] += 1
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.evidence must be a non-empty list")
        else:
            for evidence_index, item in enumerate(evidence):
                if not is_repository_path(item):
                    errors.append(f"{prefix}.evidence[{evidence_index}] must resolve to an existing repository path")
        for field in ("current_boundary", "next_step"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")

    duplicates = sorted({section_id for section_id in matrix_ids if matrix_ids.count(section_id) > 1})
    if duplicates:
        errors.append(f"duplicate matrix IDs: {', '.join(duplicates)}")
    missing = sorted(set(sections) - set(matrix_ids))
    extra = sorted(set(matrix_ids) - set(sections))
    if missing:
        errors.append(f"missing directive sections: {', '.join(missing)}")
    if extra:
        errors.append(f"unknown directive sections: {', '.join(extra)}")

    overall_status = payload.get("overall_status")
    expected_overall = "PARTIAL" if any(status_counts[status] for status in ALLOWED_STATUSES - {"IMPLEMENTED_VERIFIED"}) else "IMPLEMENTED_VERIFIED"
    if overall_status != expected_overall:
        errors.append(f"overall_status must be {expected_overall!r} for the declared section statuses")

    return {
        "structural_status": "PASS" if not errors else "FAIL",
        "directive_status": overall_status,
        "master_sections": len(sections),
        "matrix_sections": len(requirements),
        "status_counts": status_counts,
        "errors": errors,
        "claim_boundary": "A structurally valid coverage matrix only proves evidence traceability. It does not prove professional modeling autonomy or replace external visual review.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--directive", type=Path, default=MASTER_DIRECTIVE)
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "directive-coverage-audit.json")
    args = parser.parse_args()
    payload = json.loads(args.matrix.read_text(encoding="utf-8"))
    result = audit_matrix(payload, directive_sections(args.directive))
    result.update({"matrix": str(args.matrix.relative_to(ROOT)), "directive": str(args.directive.relative_to(ROOT))})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["structural_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
