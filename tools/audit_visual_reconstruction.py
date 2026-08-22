#!/usr/bin/env python3
"""Audit an evidence-bound multi-hypothesis visual reconstruction package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.visual_reconstruction import audit_visual_reconstruction


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reconstruction", type=Path)
    parser.add_argument("reference_manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    reconstruction = json.loads(args.reconstruction.read_text(encoding="utf-8"))
    manifest = json.loads(args.reference_manifest.read_text(encoding="utf-8"))
    references = {item["reference_id"]: item for item in manifest.get("items", [])}
    result = audit_visual_reconstruction(reconstruction, references)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
