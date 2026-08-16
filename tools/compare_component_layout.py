"""Compare a declared reference component layout with controlled candidate mask observations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.component_layout import compare_component_layout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_layout", type=Path)
    parser.add_argument("candidate_observations", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    reference = json.loads(args.reference_layout.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate_observations.read_text(encoding="utf-8"))
    report = compare_component_layout(reference["components"], candidate["observations"])
    report["reference_layout"] = str(args.reference_layout.resolve())
    report["candidate_observations"] = str(args.candidate_observations.resolve())
    report["reference_uncertainty"] = reference.get("uncertainty", [])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "tickets": report["tickets"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
