"""Validate and retain a human reference-board decision.

Usage:
  python tools/record_reference_board_review.py REVIEW.json OUTPUT.json \
    --gate GATE.json --audit AUDIT.json --reference-plan PLAN.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.reference_board_review import build_reference_board_handoff


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path, help="human-authored decision JSON")
    parser.add_argument("output", type=Path, help="validated handoff JSON to create")
    parser.add_argument("--gate", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--reference-plan", required=True, type=Path)
    args = parser.parse_args()
    review = json.loads(args.review.read_text(encoding="utf-8"))
    gate = json.loads(args.gate.read_text(encoding="utf-8"))
    handoff = build_reference_board_handoff(
        review, gate, audit_path=args.audit, reference_plan_path=args.reference_plan
    )
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        if existing != handoff:
            raise FileExistsError(f"refusing to overwrite a different review handoff: {args.output}")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "gate_id": handoff["gate_id"],
        "disposition": handoff["disposition"],
        "modeling_authorized": handoff["modeling_authorized"],
        "authorized_stage": handoff["authorized_stage"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
