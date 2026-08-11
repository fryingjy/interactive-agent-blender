"""Compare alpha silhouettes after explicitly recorded bbox normalization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def alpha(path):
    return np.asarray(Image.open(path).convert("RGBA"))[..., 3] > 127


def bbox(mask):
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def compare(reference_path, candidate_path):
    reference, candidate = alpha(reference_path), alpha(candidate_path)
    rb, cb = bbox(reference), bbox(candidate)
    rx0, ry0, rx1, ry1 = rb
    cx0, cy0, cx1, cy1 = cb
    crop = Image.fromarray(candidate[cy0:cy1 + 1, cx0:cx1 + 1].astype(np.uint8) * 255, "L")
    resized = np.asarray(crop.resize((rx1 - rx0 + 1, ry1 - ry0 + 1), Image.Resampling.NEAREST)) > 127
    aligned = np.zeros_like(reference)
    aligned[ry0:ry1 + 1, rx0:rx1 + 1] = resized
    intersection = int(np.logical_and(reference, aligned).sum())
    union = int(np.logical_or(reference, aligned).sum())
    reference_count, candidate_count = int(reference.sum()), int(aligned.sum())
    return {
        "reference": str(Path(reference_path).resolve()),
        "candidate": str(Path(candidate_path).resolve()),
        "reference_bbox": rb,
        "candidate_bbox_before_alignment": cb,
        "iou": round(intersection / union, 6),
        "reference_recall": round(intersection / reference_count, 6),
        "candidate_precision": round(intersection / candidate_count, 6),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_dir", type=Path)
    parser.add_argument("candidate_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    views = {
        view: compare(args.reference_dir / f"reference_{view}_mask.png", args.candidate_dir / f"candidate_{view}_mask.png")
        for view in ("front", "side", "top")
    }
    report = {
        "method": "alpha masks; candidate bbox cropped and nearest-neighbor normalized into reference bbox",
        "normalization_warning": "Scores test normalized projected shape, not absolute framing, scale, or translation.",
        "views": views,
        "mean_iou": round(sum(item["iou"] for item in views.values()) / len(views), 6),
        "pass": all(item["iou"] >= 0.97 for item in views.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


main()
