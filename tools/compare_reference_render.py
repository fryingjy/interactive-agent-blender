"""Create reproducible strict-frame or normalized reference/render comparison evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.reference_overlay import compare_reference_render, save_mask


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--alignment", choices=("strict", "uniform-bbox", "bbox"), default="strict")
    parser.add_argument("--reference-mask-mode", choices=("auto", "alpha", "light-background", "luminance-range"), default="auto")
    parser.add_argument("--candidate-mask-mode", choices=("auto", "alpha", "light-background", "luminance-range"), default="auto")
    parser.add_argument("--background-threshold", type=int, default=240)
    parser.add_argument("--reference-luminance-min", type=int, default=0)
    parser.add_argument("--reference-luminance-max", type=int, default=255)
    parser.add_argument("--candidate-luminance-min", type=int, default=0)
    parser.add_argument("--candidate-luminance-max", type=int, default=255)
    parser.add_argument("--reference-roi", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    parser.add_argument("--candidate-roi", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    parser.add_argument("--view", default="unknown")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report, images = compare_reference_render(
        args.reference,
        args.candidate,
        alignment=args.alignment,
        reference_mask_mode=args.reference_mask_mode,
        candidate_mask_mode=args.candidate_mask_mode,
        light_background_threshold=args.background_threshold,
        reference_luminance_min=args.reference_luminance_min,
        reference_luminance_max=args.reference_luminance_max,
        candidate_luminance_min=args.candidate_luminance_min,
        candidate_luminance_max=args.candidate_luminance_max,
        reference_roi=tuple(args.reference_roi) if args.reference_roi else None,
        candidate_roi=tuple(args.candidate_roi) if args.candidate_roi else None,
        view=args.view,
    )
    save_mask(images["reference_mask"], output / "reference_mask.png")
    save_mask(images["candidate_mask_aligned"], output / "candidate_mask_aligned.png")
    Image.fromarray(images["overlay"], "RGB").save(output / "overlay.png")
    Image.fromarray(images["contour_error_heatmap"], "RGB").save(output / "contour_error_heatmap.png")
    report_path = output / "comparison.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "metrics": report["metrics"], "alignment": report["alignment"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
