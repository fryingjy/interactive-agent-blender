"""Normalize a transparent candidate silhouette into a measured reference box.

This intentionally removes global scale and translation so the score tests
shape proportions. The report records that normalization and must not be
misrepresented as an unaligned image match.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.visual_compare import compare_masks


def bbox(mask):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError("empty mask")
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def save_alpha(mask, path):
    rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = mask.astype(np.uint8) * 255
    Image.fromarray(rgba, "RGBA").save(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("output_dir")
    parser.add_argument("--background-threshold", type=int, default=240)
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    reference_image = np.asarray(Image.open(args.reference).convert("RGB"))
    reference_mask = ~np.all(reference_image > args.background_threshold, axis=2)
    candidate_rgba = np.asarray(Image.open(args.candidate).convert("RGBA"))
    candidate_mask = candidate_rgba[..., 3] > 0
    ref_box = bbox(reference_mask)
    cand_box = bbox(candidate_mask)
    rx0, ry0, rx1, ry1 = ref_box
    cx0, cy0, cx1, cy1 = cand_box
    candidate_crop = Image.fromarray((candidate_mask[cy0 : cy1 + 1, cx0 : cx1 + 1] * 255).astype(np.uint8), "L")
    resized = np.asarray(candidate_crop.resize((rx1 - rx0 + 1, ry1 - ry0 + 1), Image.Resampling.NEAREST)) > 0
    aligned = np.zeros_like(reference_mask)
    aligned[ry0 : ry1 + 1, rx0 : rx1 + 1] = resized
    result = compare_masks(reference_mask, aligned)
    report = {
        "method": "candidate alpha cropped to foreground bounding box and nearest-neighbor resized into measured reference foreground bounding box",
        "reference": str(Path(args.reference).resolve()),
        "candidate": str(Path(args.candidate).resolve()),
        "reference_bbox": ref_box,
        "candidate_bbox_before_alignment": cand_box,
        "metrics": result,
    }
    save_alpha(reference_mask, output / "reference_mask.png")
    save_alpha(aligned, output / "candidate_mask_aligned.png")
    overlay = np.full((*reference_mask.shape, 3), 18, dtype=np.uint8)
    overlay[reference_mask & ~aligned] = (235, 70, 70)
    overlay[aligned & ~reference_mask] = (55, 210, 235)
    overlay[reference_mask & aligned] = (240, 240, 240)
    Image.fromarray(overlay, "RGB").save(output / "silhouette_overlay.png")
    (output / "silhouette_comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


main()
