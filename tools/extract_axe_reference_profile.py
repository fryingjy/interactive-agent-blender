"""Extract authored 2D profile controls from the supplied tactical-axe image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def points(contour, epsilon):
    approx = cv2.approxPolyDP(contour, epsilon, True)[:, 0, :]
    return [[float(x), float(y)] for x, y in approx]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    image_path = Path(args.image).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    image = cv2.imread(str(image_path))
    if image is None:
        raise SystemExit(f"cannot read {image_path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    outer_index = max(range(len(contours)), key=lambda index: cv2.contourArea(contours[index]))
    outer = contours[outer_index]
    children = [
        index for index, relation in enumerate(hierarchy[0])
        if relation[3] == outer_index and cv2.contourArea(contours[index]) > 500
    ]
    if len(children) != 1:
        raise SystemExit(f"expected one major head cutout, found {len(children)}")
    hole = contours[children[0]]

    # Raised handle scale: erode the source silhouette, then retain its long right-hand region.
    grip_mask = cv2.erode(mask, np.ones((9, 9), np.uint8), iterations=1)
    grip_mask[:, :94] = 0
    grip_mask[:, 530:] = 0
    grip_contours, _ = cv2.findContours(grip_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    grip = max(grip_contours, key=cv2.contourArea)

    # Circular bright fasteners inside the dark silhouette.
    fasteners = []
    for index, contour in enumerate(contours):
        if hierarchy[0][index][3] != outer_index:
            continue
        area = cv2.contourArea(contour)
        if 20 <= area <= 120:
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter else 0
            (x, y), radius = cv2.minEnclosingCircle(contour)
            if circularity > 0.55 and radius < 8:
                fasteners.append([float(x), float(y), float(radius)])

    x, y, width, height = cv2.boundingRect(outer)
    center_x = x + width / 2
    center_y = y + height / 2
    scale = 10.5 / width

    def normalize(raw_points):
        return [[(px - center_x) * scale, -(py - center_y) * scale] for px, py in raw_points]

    report = {
        "source": str(image_path),
        "threshold": 150,
        "image_size": [int(image.shape[1]), int(image.shape[0])],
        "foreground_bbox": [int(x), int(y), int(width), int(height)],
        "pixel_to_blender_scale": scale,
        "outer_profile": normalize(points(outer, 2.0)),
        "head_cutout": normalize(points(hole, 1.5)),
        "grip_scale_profile": normalize(points(grip, 3.0)),
        "fasteners": [[(px - center_x) * scale, -(py - center_y) * scale, radius * scale] for px, py, radius in fasteners],
        "areas_pixels": {
            "outer": cv2.contourArea(outer),
            "head_cutout": cv2.contourArea(hole),
            "grip": cv2.contourArea(grip),
        },
        "limitations": [
            "Thresholding extracts silhouette evidence, not hidden construction or physical dimensions.",
            "The raised grip boundary is an eroded semantic approximation because the source is a single side image.",
            "Depth and bevel hierarchy require explicit modeling judgment."
        ],
    }
    (output / "reference_profile.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    cv2.imwrite(str(output / "reference_threshold_mask.png"), mask)
    print(json.dumps({key: report[key] for key in ("foreground_bbox", "areas_pixels", "fasteners")}, indent=2))


main()
