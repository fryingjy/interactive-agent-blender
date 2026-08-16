"""Validate and retain a human visual-review handoff for planner-driven repair.

Usage:
  python tools/record_external_visual_review.py REVIEW.json OUTPUT.json --current-scene-revision 12
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.human_review import build_repair_record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path, help="human-authored JSON review")
    parser.add_argument("output", type=Path, help="repair-handoff JSON to create")
    parser.add_argument("--current-scene-revision", required=True, type=int)
    args = parser.parse_args()
    review = json.loads(args.review.read_text(encoding="utf-8"))
    handoff = build_repair_record(review, current_scene_revision=args.current_scene_revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "asset_id": handoff["asset_id"],
        "scene_revision": handoff["scene_revision"],
        "ticket_count": len(handoff["repair_tickets"]),
        "disposition": handoff["disposition"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
