"""Detect and compare opposite-quadrant circular lid fittings in top renders."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2


def detect(path):
    image = cv2.imread(str(path))
    gray = cv2.GaussianBlur(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (5, 5), 1)
    found = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, 1, 30,
        param1=60, param2=15, minRadius=6, maxRadius=25,
    )
    if found is None:
        raise ValueError(f"no fitting circles detected in {path}")
    circles = [[float(x), float(y), float(radius)] for x, y, radius in found[0]]
    center_x, center_y = image.shape[1] / 2, image.shape[0] / 2
    large = max((item for item in circles if item[0] < center_x and item[1] > center_y), key=lambda item: item[2])
    small = min((item for item in circles if item[0] > center_x and item[1] < center_y), key=lambda item: item[2])
    return {"large_bung": large, "small_vent": small, "all_detected": circles}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    reference, candidate = detect(args.reference), detect(args.candidate)
    errors = {}
    for role in ("large_bung", "small_vent"):
        ref, cand = reference[role], candidate[role]
        errors[role] = {
            "center_error_px": round(math.dist(ref[:2], cand[:2]), 6),
            "radius_error_px": round(abs(ref[2] - cand[2]), 6),
        }
    report = {
        "method": "Gaussian blur plus Hough circle detection; role selected by opposite lid quadrant and radius",
        "reference": reference,
        "candidate": candidate,
        "errors": errors,
        "gates": {"max_center_error_px": 10.0, "max_radius_error_px": 2.0},
        "pass": all(item["center_error_px"] <= 10 and item["radius_error_px"] <= 2 for item in errors.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


main()
