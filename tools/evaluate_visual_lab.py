"""Evaluate whether the corrected candidate improves every controlled view."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("initial")
    parser.add_argument("corrected")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    initial = json.loads(Path(args.initial).read_text(encoding="utf-8"))
    corrected = json.loads(Path(args.corrected).read_text(encoding="utf-8"))
    views = sorted(set(initial["views"]) & set(corrected["views"]))
    assertions = {
        "corrected_mean_iou_improves": corrected["mean_iou"] > initial["mean_iou"],
        "corrected_worst_view_improves": corrected["worst_view_iou"] > initial["worst_view_iou"],
        "corrected_contour_error_improves": corrected["mean_contour_error_normalized"] < initial["mean_contour_error_normalized"],
        "every_view_iou_improves": all(corrected["views"][view]["silhouette_iou"] > initial["views"][view]["silhouette_iou"] for view in views),
    }
    report = {"lab": "fixed_frame_multiview_visual_comparison", "initial": initial, "corrected": corrected, "assertions": assertions, "pass": all(assertions.values())}
    output = Path(args.output)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("visual correction did not improve all required metrics")


if __name__ == "__main__":
    main()
