"""Create a conservative retention ledger for missing source-registry artifacts.

Only missing repository artifacts are listed.  A Git deletion is evidence that an
artifact was intentionally removed from this checkout/history; it never restores
the artifact or upgrades a source claim.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_source_registry import REGISTRY, path_check


def deleted_commits(path: str) -> list[str]:
    if not path.startswith(("runs/", "knowledge/", "docs/", "tools/")):
        return []
    completed = subprocess.run(
        ["git", "log", "--all", "--diff-filter=D", "--format=%H", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in completed.stdout.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "knowledge" / "foundation" / "source_retention_ledger.json",
    )
    args = parser.parse_args()
    records = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = []
    for record in records:
        source_id = record.get("id", "unknown")
        references = [("local_path", record.get("local_path"))]
        metadata = record.get("metadata", {})
        if isinstance(metadata, dict):
            references.extend(
                (f"metadata.{field}", value)
                for field in ("experiments", "skills")
                for value in metadata.get(field, [])
            )
        for field, value in references:
            if not isinstance(value, str) or not value.startswith(("runs/", "knowledge/", "docs/", "tools/")):
                continue
            if path_check(value)["exists"]:
                continue
            commits = deleted_commits(value)
            classification = (
                "HISTORICAL_ARTIFACT_REMOVED_FROM_GIT_HISTORY"
                if commits else "UNRESOLVED_MISSING_ARTIFACT"
            )
            entries.append({
                "source_id": source_id,
                "field": field,
                "path": value,
                "classification": classification,
                "deleted_commits": commits,
                "claim_boundary": "Not locally reproducible; retained only as a historical reference.",
            })
    payload = {
        "schema_version": 1,
        "purpose": "Classify missing source-registry artifact references without treating them as retained evidence.",
        "records": sorted(entries, key=lambda item: (item["source_id"], item["field"], item["path"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(entries), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
