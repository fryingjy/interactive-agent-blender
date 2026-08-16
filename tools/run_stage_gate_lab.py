"""Prove strict Blender object stage transitions reject weak evidence without mutation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender_ops.modeling_stage import advance_stage, get_stage, get_stage_log


def main():
    out = ROOT / "runs" / "2026-08-10_stage-quality"
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = "StageGateAsset"

    reference_evidence = {
        "component_graph_pass": True, "measured_ratio_count": 3, "uncertainty_recorded": True,
        "reference_set_audit_pass": True, "same_target_identity_pass": True,
        "view_coverage_pass": True, "critical_property_coverage_pass": True,
        "conflicts_resolved_pass": True, "question_driven_research_pass": True,
    }
    weak_primary = advance_stage(
        obj.name, "PRIMARY_BLOCKOUT",
        {**reference_evidence, "question_driven_research_pass": False},
    )
    state_after_weak = {"stage": get_stage(obj.name), "log_count": len(get_stage_log(obj.name))}
    strong_primary = advance_stage(obj.name, "PRIMARY_BLOCKOUT", reference_evidence)
    coverage = {
        "declared_primary_components": ["stage_gate_asset"],
        "built_object_names": [obj.name],
        "component_matches": {"stage_gate_asset": obj.name},
        "unmatched_primary_components": [],
        "coverage_ok": True,
    }
    weak_visual = advance_stage(obj.name, "PROPORTION_SILHOUETTE", {
        "dimensions_checked": True, "primary_components_present": True,
        "component_coverage": {**coverage, "coverage_ok": False},
    })
    state_after_weak_visual = {"stage": get_stage(obj.name), "log_count": len(get_stage_log(obj.name))}
    strong_visual = advance_stage(obj.name, "PROPORTION_SILHOUETTE", {
        "dimensions_checked": True, "primary_components_present": True,
        "component_coverage": coverage,
    })
    final_log = get_stage_log(obj.name)
    assertions = {
        "open_reference_question_rejected": not weak_primary["advanced"],
        "rejection_did_not_mutate": state_after_weak == {"stage": "REFERENCE_ANALYSIS", "log_count": 0},
        "primary_advanced": strong_primary["advanced"],
        "incomplete_primary_blockout_rejected": not weak_visual["advanced"],
        "visual_rejection_did_not_mutate": state_after_weak_visual == {"stage": "PRIMARY_BLOCKOUT", "log_count": 1},
        "complete_primary_blockout_advanced": strong_visual["advanced"],
        "only_accepted_transitions_logged": len(final_log) == 2,
    }
    report = {
        "lab": "machine_enforced_modeling_stage_gates",
        "attempts": [weak_primary, strong_primary, weak_visual, strong_visual],
        "final_stage": get_stage(obj.name),
        "stage_log": final_log,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (out / "stage_gate_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "stage_gate_lab.blend"))
    print("STAGE_GATE_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
