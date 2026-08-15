"""Compare a corrected rotational silhouette against a retained rejected baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.visual_compare import compare_masks  # noqa: E402
from tools.evaluate_runtime_candlestick import (  # noqa: E402
    align,
    load_candidate,
    load_reference,
    row_width_profile,
    save_overlay,
)


def measure(reference: np.ndarray, candidate_path: Path) -> tuple[dict, np.ndarray]:
    aligned = align(reference, load_candidate(candidate_path))
    metrics = compare_masks(reference, aligned)
    difference = row_width_profile(aligned) - row_width_profile(reference)
    metrics["profile_rmse"] = float(np.sqrt(np.mean(difference * difference)))
    return metrics, aligned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_mask", type=Path)
    parser.add_argument("rejected_baseline_mask", type=Path)
    parser.add_argument("corrected_mask", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    reference = load_reference(args.reference_mask)
    baseline, _ = measure(reference, args.rejected_baseline_mask)
    corrected, corrected_aligned = measure(reference, args.corrected_mask)
    checks = {
        "silhouette_iou_improved": corrected["silhouette_iou"] > baseline["silhouette_iou"],
        "profile_rmse_improved": corrected["profile_rmse"] < baseline["profile_rmse"],
        "contour_error_improved": (
            corrected["symmetric_contour_error_normalized"]
            < baseline["symmetric_contour_error_normalized"]
        ),
    }
    report = {
        "method": "both candidates are foreground-bbox aligned to the same retained reference mask",
        "reference_mask": str(args.reference_mask.resolve()),
        "rejected_baseline_mask": str(args.rejected_baseline_mask.resolve()),
        "corrected_mask": str(args.corrected_mask.resolve()),
        "baseline": baseline,
        "corrected": corrected,
        "improvement": {
            "silhouette_iou_gain": corrected["silhouette_iou"] - baseline["silhouette_iou"],
            "profile_rmse_reduction_percent": 100.0 * (
                1.0 - corrected["profile_rmse"] / baseline["profile_rmse"]
            ),
            "contour_error_reduction_percent": 100.0 * (
                1.0
                - corrected["symmetric_contour_error_normalized"]
                / baseline["symmetric_contour_error_normalized"]
            ),
        },
        "checks": checks,
        "pass_relative_correction": all(checks.values()),
        "limitations": [
            "A better front silhouette does not establish full multi-view or material accuracy.",
            "The original human rejection remains valid until a human accepts the corrected form.",
        ],
    }
    save_overlay(reference, corrected_aligned, output / "corrected_overlay.png")
    (output / "correction_evaluation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["pass_relative_correction"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
