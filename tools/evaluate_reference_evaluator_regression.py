"""Evaluate the immutable multi-target real-reference regression anchor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.evaluator_regression import evaluate_anchor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", default="knowledge/foundation/reference_evaluator_regression_anchor.json")
    parser.add_argument("--output", default="runs/2026-09-01_system-gap-audit/reference_evaluator_regression.json")
    args = parser.parse_args()
    root = ROOT
    anchor_path = root / args.anchor
    report = evaluate_anchor(json.loads(anchor_path.read_text(encoding="utf-8")), root=root)
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
