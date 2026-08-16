"""Build the evidence-traceable reference-to-blockout contract required before modeling.

Usage:
  python tools/build_reference_to_blockout_contract.py DECOMPOSITION.json REFERENCE_SET_ID OUTPUT.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.scene_decomposition import scene_decomposition_from_dict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decomposition", type=Path)
    parser.add_argument("reference_set_id")
    parser.add_argument("output", type=Path)
    parser.add_argument("--selected-strategy")
    args = parser.parse_args()
    decomposition = scene_decomposition_from_dict(
        json.loads(args.decomposition.read_text(encoding="utf-8"))
    )
    contract = decomposition.to_reference_to_blockout_contract(
        reference_set_id=args.reference_set_id,
        selected_strategy_name=args.selected_strategy,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "target": contract["target"],
        "reference_set_id": contract["reference_set_id"],
        "selected_strategy": contract["selected_strategy"]["name"],
        "ready_for_blockout": contract["reference_readiness"]["ready_for_blockout"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
