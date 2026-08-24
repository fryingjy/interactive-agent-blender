"""Verify or update SHA-256 bindings for local files in reference manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def process_manifest(path: Path, *, write: bool) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    changed: list[str] = []
    errors: list[str] = []
    for item in payload.get("items", []):
        local_file = item.get("local_file")
        if not local_file:
            continue
        artifact = Path(local_file)
        if not artifact.is_absolute():
            artifact = (path.parent / artifact).resolve()
        if not artifact.is_file():
            errors.append(f"{item.get('reference_id', '<unnamed>')}: missing {artifact}")
            continue
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if item.get("local_sha256", "").lower() != digest:
            changed.append(str(item.get("reference_id", "<unnamed>")))
            if write:
                item["local_sha256"] = digest
    if write and changed and not errors:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "manifest": str(path),
        "changed_reference_ids": changed,
        "errors": errors,
        "pass": not errors and (write or not changed),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    reports = [process_manifest(path.resolve(), write=args.write) for path in args.manifests]
    print(json.dumps({"schema_version": 1, "reports": reports}, indent=2))
    return 0 if all(report["pass"] for report in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
