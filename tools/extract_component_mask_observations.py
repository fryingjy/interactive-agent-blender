#!/usr/bin/env python3
"""Extract local normalized bounds from a Blender component-mask diagnostic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from knowledge_engine.component_mask_observations import extract_component_mask_observations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--components", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = extract_component_mask_observations(args.image, args.components)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"observed": sorted(report["observations"]), "missing": report["missing_component_ids"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
