"""Run the hash-bound Gemini multi-view reference critic."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.gemini_reference_critic import (  # noqa: E402
    DEFAULT_MODEL,
    analyze_reference_candidate,
    analyze_reference_candidate_ensemble,
    build_critic_prompt,
    load_critic_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args()
    manifest = load_critic_manifest(args.manifest)
    if args.dry_run:
        print(json.dumps({
            "target_id": manifest["target_id"],
            "model": args.model,
            "views": [item["view"] for item in manifest["views"]],
            "hash_bound": True,
            "prompt": build_critic_prompt(manifest),
        }, indent=2))
        return 0
    if args.output is None:
        parser.error("--output is required unless --dry-run is used")
    result = (
        analyze_reference_candidate(manifest, model=args.model)
        if args.samples == 1
        else analyze_reference_candidate_ensemble(manifest, model=args.model, samples=args.samples)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
