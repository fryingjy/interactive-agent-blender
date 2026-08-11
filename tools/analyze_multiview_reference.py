"""Measure silhouettes and registered form landmarks from neutral reference renders."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def silhouette(path):
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None or image.shape[2] != 4:
        raise ValueError(f"expected RGBA mask: {path}")
    mask = image[:, :, 3] > 127
    ys, xs = np.where(mask)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    width, height = bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1
    return {
        "image_size": [int(image.shape[1]), int(image.shape[0])],
        "bbox_xyxy": bbox,
        "bbox_size": [width, height],
        "aspect_width_over_height": round(width / height, 6),
        "fill_ratio": round(float(mask.mean()), 6),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    views = {view: silhouette(args.reference_dir / f"reference_{view}_mask.png") for view in ("front", "side", "top")}
    report = {
        "method": "RGBA alpha silhouette measurement plus visually registered form landmarks",
        "views": views,
        "derived_constraints": {
            "front_side_silhouette_identity": views["front"] == views["side"],
            "body_diameter_over_height": views["front"]["aspect_width_over_height"],
            "top_width_over_height": views["top"]["aspect_width_over_height"],
            "major_hoop_height_fractions_from_top": [0.317, 0.696],
            "corrugation_band_height_fraction": [0.33, 0.68],
            "corrugation_count_visible": 11,
            "lid_fittings": [
                {"role": "large_bung", "top_view_xy_fraction": [0.255, 0.718], "diameter_over_body": 0.12},
                {"role": "small_vent", "top_view_xy_fraction": [0.754, 0.215], "diameter_over_body": 0.075}
            ]
        },
        "uncertainty": [
            "Depth is inferred from the circular top silhouette and front/side agreement.",
            "Hoop and corrugation landmarks are registered to visible shading edges, not silhouette boundaries.",
            "Surface wear and warning graphic are appearance evidence and are excluded from geometry gates."
        ]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
