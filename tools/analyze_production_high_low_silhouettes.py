"""Measure fixed-frame high/low silhouette agreement for the production audit lab."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.visual_compare import compare_image_files


OUT = ROOT / "runs" / "2026-08-15_production-high-low-audit"


def main() -> None:
    build = json.loads((OUT / "build_report.json").read_text(encoding="utf-8"))
    scores = {}
    details = {}
    for family, views in build["render_evidence"].items():
        scores[family] = {}
        details[family] = {}
        for view, record in views.items():
            high = Path(record["high_path"])
            low = high if record["equal_masks"] else Path(record["low_path"])
            comparison = compare_image_files(high, low)
            scores[family][view] = comparison["silhouette_iou"]
            details[family][view] = comparison
    report = {
        "scores": scores,
        "details": details,
        "pass": all(
            len(views) >= 3 and min(views.values()) >= 0.90
            for views in scores.values()
        ),
    }
    (OUT / "silhouette_scores.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["scores"], indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
