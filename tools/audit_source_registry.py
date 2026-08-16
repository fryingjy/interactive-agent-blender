"""Fail-closed audit of source-registry evidence paths.

It does not require temporary source media to be retained. It does require any
claimed experiment, skill, or retained local artifact path to resolve inside
the repository before that record can be treated as locally reproducible.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "knowledge" / "foundation" / "source_registry.json"
RETENTION_LEDGER = ROOT / "knowledge" / "foundation" / "source_retention_ledger.json"


def path_check(value: str) -> dict[str, object]:
    path = Path(value)
    candidate = path if path.is_absolute() else ROOT / path
    return {"path": value, "exists": candidate.exists(), "kind": "directory" if candidate.is_dir() else "file" if candidate.is_file() else "missing"}


def classify_reference(field: str, value: str) -> str:
    """Return artifact, non-path reference, or explicitly non-retained.

    Historical registry records use plain strings, so a skill ID or prose note
    must never be mistaken for a filesystem promise.  Conversely, a `runs/`
    path is a reproducibility claim and remains fail-closed when absent.
    """
    text = value.strip()
    if text.upper().startswith("REMOVED"):
        return "explicitly_non_retained"
    if field == "metadata.skills":
        return "non_path_reference"
    if " (" in text:
        return "non_path_reference"
    if text.startswith(("runs/", "knowledge/", "docs/", "tools/")):
        return "artifact"
    return "non_path_reference"


def retention_key(source_id: str, field: str, path: str) -> str:
    return f"{source_id}\u241f{field}\u241f{path}"


def load_retention_ledger(path: Path = RETENTION_LEDGER) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("source retention ledger records must be a list")
    ledger: dict[str, dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("source retention ledger record must be an object")
        source_id = str(record.get("source_id") or "")
        field = str(record.get("field") or "")
        artifact_path = str(record.get("path") or "")
        classification = str(record.get("classification") or "")
        if not source_id or not field or not artifact_path or not classification:
            raise ValueError("source retention ledger record requires source_id, field, path, classification")
        key = retention_key(source_id, field, artifact_path)
        if key in ledger:
            raise ValueError(f"duplicate source retention ledger record: {key}")
        ledger[key] = record
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "source-registry-audit.json")
    args = parser.parse_args()
    records = json.loads(REGISTRY.read_text(encoding="utf-8"))
    findings = []
    non_path_references = []
    intentionally_non_retained = []
    ledger = load_retention_ledger()
    classified_missing = []

    def record_missing(record_id: str, field: str, check: dict[str, object]) -> None:
        entry = {"source_id": record_id, "field": field, **check}
        retention = ledger.get(retention_key(record_id, field, str(check["path"])))
        if retention is None:
            findings.append(entry)
        elif retention.get("classification") == "SOURCE_MEDIA_NOT_RETAINED":
            intentionally_non_retained.append({**entry, "retention": retention})
        else:
            classified_missing.append({**entry, "retention": retention})

    for record in records:
        record_id = record.get("id", "unknown")
        local_path = record.get("local_path")
        if isinstance(local_path, str) and local_path:
            classification = classify_reference("local_path", local_path)
            check = path_check(local_path) if classification == "artifact" else {"path": local_path}
            if classification == "explicitly_non_retained":
                intentionally_non_retained.append({"source_id": record_id, "field": "local_path", **check})
            elif classification == "artifact" and not check["exists"]:
                record_missing(record_id, "local_path", check)
            elif classification == "non_path_reference":
                non_path_references.append({"source_id": record_id, "field": "local_path", **check})
        metadata = record.get("metadata", {})
        for field in ("experiments", "skills"):
            for value in metadata.get(field, []) if isinstance(metadata, dict) else []:
                if isinstance(value, str):
                    classification = classify_reference(f"metadata.{field}", value)
                    if classification == "explicitly_non_retained":
                        intentionally_non_retained.append({"source_id": record_id, "field": f"metadata.{field}", "path": value})
                        continue
                    if classification == "non_path_reference":
                        non_path_references.append({"source_id": record_id, "field": f"metadata.{field}", "path": value})
                        continue
                    check = path_check(value)
                    if not check["exists"]:
                        record_missing(record_id, f"metadata.{field}", check)
    total_missing = len(findings) + len(classified_missing)
    result = {"registry": str(REGISTRY.relative_to(ROOT)), "retention_ledger": str(RETENTION_LEDGER.relative_to(ROOT)), "record_count": len(records), "missing_artifact_count": total_missing, "unclassified_missing_artifact_count": len(findings), "classified_missing_artifact_count": len(classified_missing), "explicitly_non_retained_count": len(intentionally_non_retained), "non_path_reference_count": len(non_path_references), "locally_reproducible": total_missing == 0, "missing_artifacts": findings, "classified_missing_artifacts": classified_missing, "explicitly_non_retained": intentionally_non_retained, "non_path_references": non_path_references, "claim_boundary": "Classified non-retained evidence remains unavailable for local reproduction. The ledger explains its retention state but does not turn it into a passing artifact or prove the external source claim."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
