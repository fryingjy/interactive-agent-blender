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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifests", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    reports = []
    for path in args.manifests:
        payload = json.loads(path.read_text(encoding="utf-8"))
        reports.append({"manifest": str(path), "audit": audit_reference_set(reference_set_from_dict(payload))})
    result = {"schema_version": 1, "reports": reports}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
