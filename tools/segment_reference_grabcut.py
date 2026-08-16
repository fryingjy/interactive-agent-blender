"""Create a reproducible foreground silhouette from a difficult photo reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def fill_holes(mask: np.ndarray) -> np.ndarray:
    flood = mask.copy()
    padded = cv2.copyMakeBorder(flood, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    cv2.floodFill(padded, None, (0, 0), 255)
    outside = padded[1:-1, 1:-1]
    return cv2.bitwise_or(mask, cv2.bitwise_not(outside))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--rect", type=int, nargs=4, metavar=("X", "Y", "W", "H"), required=True)
    parser.add_argument("--anchor", type=int, nargs=2, metavar=("X", "Y"))
    parser.add_argument(
        "--symmetric-center",
        type=int,
        help="For a rotational object, reconstruct row half-width around this X coordinate",
    )
    parser.add_argument(
        "--symmetric-mode", choices=("min", "max", "mean", "span"), default="min",
        help="Choose how left/right detected half-widths are combined; min rejects an obstruction, max recovers a faint transparent edge",
    )
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument(
        "--preserve-holes", action="store_true",
        help="Keep enclosed negative spaces (for example a carry-handle opening) instead of filling them.",
    )
    args = parser.parse_args()

    image = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
    if image is None:
        raise SystemExit(f"could not read {args.image}")
    height, width = image.shape[:2]
    x, y, rect_width, rect_height = args.rect
    if x < 0 or y < 0 or x + rect_width > width or y + rect_height > height:
        raise SystemExit("GrabCut rectangle must stay inside the image")

    labels = np.zeros((height, width), np.uint8)
    background_model = np.zeros((1, 65), np.float64)
    foreground_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(
        image,
        labels,
        (x, y, rect_width, rect_height),
        background_model,
        foreground_model,
        args.iterations,
        cv2.GC_INIT_WITH_RECT,
    )
    initial = np.where((labels == cv2.GC_FGD) | (labels == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    count, component_labels, stats, _ = cv2.connectedComponentsWithStats(initial, connectivity=8)
    candidates = []
    for label in range(1, count):
        component_x, component_y, component_width, component_height, area = map(int, stats[label])
        contains_anchor = False
        if args.anchor:
            anchor_x, anchor_y = args.anchor
            contains_anchor = bool(component_labels[anchor_y, anchor_x] == label)
        candidates.append({
            "label": label,
            "area": area,
            "bbox": [component_x, component_y, component_width, component_height],
            "contains_anchor": contains_anchor,
        })
    anchored = [item for item in candidates if item["contains_anchor"]]
    chosen = max(anchored or candidates, key=lambda item: item["area"])
    mask = np.where(component_labels == chosen["label"], 255, 0).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    if not args.preserve_holes:
        mask = fill_holes(mask)
    if args.symmetric_center is not None:
        center = args.symmetric_center
        symmetric = np.zeros_like(mask)
        for row in range(height):
            row_x = np.where(mask[row] > 0)[0]
            if not len(row_x) or mask[row, center] == 0:
                continue
            left_width = center - int(row_x.min())
            right_width = int(row_x.max()) - center
            if args.symmetric_mode == "span":
                half_width = round((int(row_x.max()) - int(row_x.min())) * 0.5)
            elif args.symmetric_mode == "max":
                half_width = max(left_width, right_width)
            elif args.symmetric_mode == "mean":
                half_width = round((left_width + right_width) * 0.5)
            else:
                half_width = min(left_width, right_width)
            if half_width > 0:
                symmetric[row, center - half_width : center + half_width + 1] = 255
        mask = symmetric

    ys, xs = np.where(mask > 0)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    bbox_width = bbox[2] - bbox[0]
    bbox_height = bbox[3] - bbox[1]
    profile = []
    for row in range(bbox[1], bbox[3] + 1):
        row_x = np.where(mask[row] > 0)[0]
        if not len(row_x):
            continue
        profile.append({
            "y_px": row,
            "y_norm_top_to_bottom": (row - bbox[1]) / bbox_height if bbox_height else 0.0,
            "x_min_px": int(row_x.min()),
            "x_max_px": int(row_x.max()),
            "width_px": int(row_x.max() - row_x.min()),
            "width_norm": float((row_x.max() - row_x.min()) / bbox_width) if bbox_width else 0.0,
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    mask_path = args.output_dir / "reference_silhouette.png"
    preview = image.copy()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(preview, contours, -1, (0, 0, 255), 2)
    preview_path = args.output_dir / "reference_segmentation_preview.png"
    cv2.imwrite(str(mask_path), mask)
    cv2.imwrite(str(preview_path), preview)
    report = {
        "source_image": str(args.image.resolve()),
        "algorithm": (
            "OpenCV GrabCut rectangle initialization + anchored/largest connected component + 5x5 close"
            + ("; enclosed negative spaces preserved" if args.preserve_holes else "; hole fill")
        ),
        "parameters": {
            "rect": list(args.rect),
            "anchor": list(args.anchor) if args.anchor else None,
            "iterations": args.iterations,
            "symmetric_center": args.symmetric_center,
            "symmetric_mode": args.symmetric_mode,
            "preserve_holes": args.preserve_holes,
        },
        "image_size": [width, height],
        "selected_component": chosen,
        "silhouette_bbox": bbox,
        "silhouette_size": [bbox_width, bbox_height],
        "aspect_ratio_width_over_height": bbox_width / bbox_height if bbox_height else None,
        "foreground_pixels": int((mask > 0).sum()),
        "row_profile": profile,
        "mask_path": str(mask_path),
        "preview_path": str(preview_path),
        "verification_status": "REQUIRES_VISUAL_REVIEW",
        "assumption": (
            f"Rotational symmetry reconstructed with the {args.symmetric_mode} detected per-row half-width."
            if args.symmetric_center is not None
            else None
        ),
    }
    (args.output_dir / "reference_measurement.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "row_profile"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
