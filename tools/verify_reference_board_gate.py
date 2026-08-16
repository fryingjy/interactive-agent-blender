"""Verify that a pending human reference-board gate matches its current evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.reference_board_review import validate_reference_board_gate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--reference-plan", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    gate = json.loads(args.gate.read_text(encoding="utf-8"))
    validate_reference_board_gate(gate, audit_path=args.audit, reference_plan_path=args.reference_plan)
    result = {
        "schema_version": 1,
        "record_type": "REFERENCE_BOARD_GATE_VALIDATION",
        "gate_id": gate["gate_id"],
        "pass": True,
        "human_review_status": gate["human_review_status"],
        "modeling_authorized": False,
        "evidence_binding": {
            "audit_sha256": gate["audit_sha256"],
            "reference_plan_sha256": gate["reference_plan_sha256"],
        },
        "limitation": "This validates the pending handoff contract; it is not a human decision.",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
