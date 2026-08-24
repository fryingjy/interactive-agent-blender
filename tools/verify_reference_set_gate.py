"""Audit one or more structured reference-set manifests without Blender."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.reference_analysis import audit_reference_set, reference_set_from_dict


def audit_manifest(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        audit = audit_reference_set(reference_set_from_dict(payload, base_dir=path.parent))
        return {"manifest": str(path), "audit": audit, "pass": audit["pass"] is True}
    except Exception as exc:
        return {"manifest": str(path), "error": str(exc), "pass": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifests", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    reports = [audit_manifest(path) for path in args.manifests]
    result = {"schema_version": 1, "reports": reports, "pass": all(item["pass"] for item in reports)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
