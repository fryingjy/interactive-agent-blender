"""Aggregate current evidence without allowing strong technical validity to hide quality gaps."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.quality_review import ReviewChannel, aggregate_professional_review


def main():
    visual = json.loads((ROOT / "runs/2026-08-10_visual-comparison/visual_comparison_report.json").read_text(encoding="utf-8"))
    channels = [
        ReviewChannel("technical_validity", 1.0, 1.2, True, "runs/2026-08-10_visual-comparison/verify_reports/Visual_Corrected_20260810T161916Z.json"),
        ReviewChannel("topology_context", 0.82, 1.0, True, "runs/2026-08-10_topology-subd/topology_subd_report.json"),
        ReviewChannel("surface_highlight_judgment", 0.45, 1.2, False, "knowledge/foundation/foundation_exit_report.md#largest-remaining-gaps"),
        ReviewChannel("reference_fidelity", min(visual["corrected"]["mean_iou"], 1.0), 1.2, False, "runs/2026-08-10_visual-comparison/visual_comparison_report.json (synthetic, not held-out)"),
        ReviewChannel("production_export", 0.8, 0.8, True, "runs/2026-08-10_sculpt-export/sculpt_export_report.json"),
        ReviewChannel("generalization", 0.2, 1.5, False, "knowledge/foundation/benchmark_readiness.json"),
    ]
    report = aggregate_professional_review(channels, threshold=0.85)
    report["audit"] = "current_professional_readiness"
    report["interpretation"] = "FAIL is expected and honest: technical/synthetic evidence cannot override surface and held-out generalization gates."
    out = ROOT / "runs/2026-08-10_stage-quality"
    out.mkdir(parents=True, exist_ok=True)
    (out / "professional_review_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
