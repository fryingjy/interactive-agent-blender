"""Score the fresh-process render and close the frozen runtime gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.visual_compare import compare_masks  # noqa: E402


def bbox(mask):
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def align(reference, candidate):
    rx0, ry0, rx1, ry1 = bbox(reference)
    cx0, cy0, cx1, cy1 = bbox(candidate)
    crop = Image.fromarray((candidate[cy0 : cy1 + 1, cx0 : cx1 + 1] * 255).astype(np.uint8), "L")
    resized = np.asarray(crop.resize((rx1 - rx0 + 1, ry1 - ry0 + 1), Image.Resampling.NEAREST)) > 0
    aligned = np.zeros_like(reference)
    aligned[ry0 : ry1 + 1, rx0 : rx1 + 1] = resized
    return aligned


def main() -> int:
    run = ROOT / "runs" / "2026-08-15_runtime-use-candlestick"
    blend_check = json.loads((run / "independent_blend_verification.json").read_text(encoding="utf-8"))
    evaluation = json.loads((run / "runtime_evaluation.json").read_text(encoding="utf-8"))
    contract = json.loads((run / "experiment_contract.json").read_text(encoding="utf-8"))
    reference = np.asarray(Image.open(run / "reference_silhouette.png").convert("L")) > 0
    fresh = np.asarray(Image.open(run / "independent_candidate_mask.png").convert("RGBA"))[..., 3] > 0
    metrics = compare_masks(reference, align(reference, fresh))
    threshold = contract["frozen_acceptance_gates"]["silhouette"]["final_iou_min"]
    checks = {
        "fresh_blend_geometry_and_render": blend_check["pass_geometry_and_render"] is True,
        "original_frozen_gates": evaluation["pass_before_independent_verifier"] is True,
        "fresh_render_iou_repasses_threshold": metrics["silhouette_iou"] >= threshold,
        "fresh_render_matches_original_score": abs(metrics["silhouette_iou"] - evaluation["candidate"]["metrics"]["silhouette_iou"]) < 1e-9,
    }
    report = {
        "fresh_render_metrics": metrics,
        "frozen_iou_threshold": threshold,
        "checks": checks,
        "pass": all(checks.values()),
    }
    (run / "independent_runtime_verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
