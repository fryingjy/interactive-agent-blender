"""Compare one candidate and optional baseline against named reference silhouettes.

Reference canvases and Blender diagnostic renders often use opposite background
conventions.  This tool requires those conventions explicitly and performs
foreground-bbox normalization without destroying object aspect ratio.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.visual_compare import (  # noqa: E402
    compare_masks,
    load_foreground_mask,
    normalize_foreground_bbox,
)


def named_path(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("reference must use VIEW=PATH")
    name, path = value.split("=", 1)
    if not name.strip() or not path.strip():
        raise argparse.ArgumentTypeError("reference must use non-empty VIEW=PATH")
    return name.strip(), Path(path).resolve()


def compare(reference: Path, candidate_mask, size: int, reference_mode: str) -> dict:
    reference_mask = normalize_foreground_bbox(
        load_foreground_mask(reference, mode=reference_mode), size=size
    )
    return compare_masks(reference_mask, candidate_mask)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reference", action="append", type=named_path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--reference-mode",
        choices=("alpha", "light_on_dark", "dark_on_light", "auto"),
        default="alpha",
        help="Explicit foreground convention for every supplied reference mask.",
    )
    parser.add_argument("--minimum-iou", type=float, default=0.9)
    parser.add_argument("--size", type=int, default=512)
    args = parser.parse_args()
    references = dict(args.reference)
    if len(references) != len(args.reference):
        raise SystemExit("reference view names must be unique")
    candidate_path = args.candidate.resolve()
    candidate_mask = normalize_foreground_bbox(
        load_foreground_mask(candidate_path, mode="light_on_dark"), size=args.size
    )
    candidate = {
        view: compare(path, candidate_mask, args.size, args.reference_mode)
        for view, path in references.items()
    }
    baseline = None
    improvements = None
    if args.baseline:
        baseline_path = args.baseline.resolve()
        baseline_mask = normalize_foreground_bbox(
            load_foreground_mask(baseline_path, mode="light_on_dark"), size=args.size
        )
        baseline = {
            view: compare(path, baseline_mask, args.size, args.reference_mode)
            for view, path in references.items()
        }
        improvements = {
            view: candidate[view]["silhouette_iou"] - baseline[view]["silhouette_iou"]
            for view in references
        }
    worst_iou = min(record["silhouette_iou"] for record in candidate.values())
    report = {
        "schema_version": 1,
        "record_type": "NORMALIZED_REFERENCE_SILHOUETTE_COMPARISON",
        "method": "explicit foreground modes; bbox translation/scale normalized; aspect ratio preserved",
        "reference_foreground_mode": args.reference_mode,
        "candidate": str(candidate_path),
        "baseline": str(args.baseline.resolve()) if args.baseline else None,
        "references": {view: str(path) for view, path in references.items()},
        "normalization_size": args.size,
        "minimum_iou_frozen_before_result": args.minimum_iou,
        "views": candidate,
        "baseline_views": baseline,
        "iou_gain_by_view": improvements,
        "worst_view_iou": worst_iou,
        "all_views_improved": improvements is None or all(value > 0 for value in improvements.values()),
        "pass": worst_iou >= args.minimum_iou,
        "limitations": [
            "Silhouette overlap does not establish material, topology, depth, or human visual acceptance.",
            "The front/back product images are independent same-target renders but this radial target has nearly identical outer contours in those views.",
        ],
    }
    args.output.resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
