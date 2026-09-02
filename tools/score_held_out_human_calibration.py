"""Validate and score a human response against the frozen calibration anchor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.human_calibration import score_human_calibration


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("response", type=Path)
    parser.add_argument("--manifest", type=Path, default=ROOT / "runs/2026-09-01_human-calibration/public_manifest.json")
    parser.add_argument("--anchor", type=Path, default=ROOT / "knowledge/foundation/held_out_human_calibration_anchor.json")
    parser.add_argument("--output", type=Path, default=ROOT / "runs/2026-09-01_human-calibration/result.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    anchor = json.loads(args.anchor.read_text(encoding="utf-8"))
    response = json.loads(args.response.read_text(encoding="utf-8"))
    result = score_human_calibration(manifest, anchor, response, root=ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
