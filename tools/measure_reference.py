#!/usr/bin/env python3
"""Measure real proportions from a reference image via pixel-color
segmentation, instead of eyeballing them.

Built after a real, documented failure: the first pass at
reference/omnitrix_gadget/ blocked out primitives by eye from looking at
the reference image once, with no actual measurement -- button placement,
band proportions, and overall aspect ratio were all substantially wrong
(see runs/2026-08-07_omnitrix-gadget-blockout-v2/note.md for the specific
numbers). This is the fix: a reusable tool, not a one-off script, so every
future image-reference milestone measures first.

Usage:
    python tools/measure_reference.py <image_path> [--bg-threshold 240]

Prints the overall non-background bounding box (in image pixels) and a
row-by-row silhouette width profile, which is what actually matters for
blocking out a prop's vertical proportions (where does the silhouette
flare out or narrow -- that's where a real component boundary is, not a
guess). Does not attempt automatic component segmentation by color, since
that's reference-specific (this tool's own analysis of the gadget image
hand-picked green-channel thresholds for its band, which won't generalize)
-- print the width profile and let the caller reason about it, the same
way a modeler would trace a reference image by eye but with real numbers
instead of a guess.
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image


def measure(image_path, bg_threshold=240):
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img).astype(int)
    is_bg = np.all(arr > bg_threshold, axis=2)
    mask = ~is_bg
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {"error": "no non-background pixels found"}

    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    width, height = x1 - x0, y1 - y0

    profile = []
    for y in range(y0, y1 + 1):
        row = np.where(mask[y])[0]
        if len(row):
            row_min, row_max = int(row.min()), int(row.max())
            profile.append({
                "y_px": y,
                "y_norm": round((y - y0) / height, 4) if height else 0.0,
                "x_min_px": row_min, "x_max_px": row_max,
                "width_px": row_max - row_min,
                "width_norm": round((row_max - row_min) / width, 4) if width else 0.0,
            })

    return {
        "image_size_px": list(img.size),
        "silhouette_bbox_px": {"x": [x0, x1], "y": [y0, y1]},
        "silhouette_size_px": {"width": width, "height": height},
        "aspect_ratio_w_over_h": round(width / height, 4) if height else None,
        "row_profile": profile,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path")
    parser.add_argument("--bg-threshold", type=int, default=240)
    parser.add_argument("--every", type=int, default=15, help="print every Nth profile row")
    args = parser.parse_args()

    result = measure(args.image_path, args.bg_threshold)
    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"image_size_px: {result['image_size_px']}")
    print(f"silhouette_bbox_px: {result['silhouette_bbox_px']}")
    print(f"silhouette_size_px: {result['silhouette_size_px']}")
    print(f"aspect_ratio_w_over_h: {result['aspect_ratio_w_over_h']}")
    print("row_profile (y_norm, width_norm, x_min_px, x_max_px):")
    for row in result["row_profile"][::args.every]:
        print(f"  {row['y_norm']:.3f}  {row['width_norm']:.3f}  "
              f"[{row['x_min_px']:4d}, {row['x_max_px']:4d}]")

    out_path = args.image_path.rsplit(".", 1)[0] + "_measurement.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nfull profile saved to {out_path}")


if __name__ == "__main__":
    main()
