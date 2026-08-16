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
    if text.startswith(("runs/", "knowledge/", "docs/", "tools/")):
        return "artifact"
    return "non_path_reference"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "source-registry-audit.json")
    args = parser.parse_args()
    records = json.loads(REGISTRY.read_text(encoding="utf-8"))
    findings = []
    non_path_references = []
    intentionally_non_retained = []
    for record in records:
        record_id = record.get("id", "unknown")
        local_path = record.get("local_path")
        if isinstance(local_path, str) and local_path:
            classification = classify_reference("local_path", local_path)
            check = path_check(local_path) if classification == "artifact" else {"path": local_path}
            if classification == "explicitly_non_retained":
                intentionally_non_retained.append({"source_id": record_id, "field": "local_path", **check})
            elif classification == "artifact" and not check["exists"]:
                findings.append({"source_id": record_id, "field": "local_path", **check})
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
                        findings.append({"source_id": record_id, "field": f"metadata.{field}", **check})
    result = {"registry": str(REGISTRY.relative_to(ROOT)), "record_count": len(records), "missing_artifact_count": len(findings), "explicitly_non_retained_count": len(intentionally_non_retained), "non_path_reference_count": len(non_path_references), "locally_reproducible": not findings, "missing_artifacts": findings, "explicitly_non_retained": intentionally_non_retained, "non_path_references": non_path_references, "claim_boundary": "A missing local artifact means the registry record is not locally reproducible; it does not prove the external source is false. Non-path references and explicitly non-retained media do not count as missing artifact claims."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
