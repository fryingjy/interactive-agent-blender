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
from blender_ops.modeler_server import ModelerServer
from blender_ops import decision_state
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.scene_decomposition import Component, ReferenceClaim, SceneDecomposition, StrategyCandidate


def main():
    out = ROOT / "runs" / "2026-08-10_stage-quality"
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = "StageGateAsset"
    server = ModelerServer()
    decomposition = SceneDecomposition(
        object_name="stage gate asset",
        components=[Component(
            "stage_gate_asset", "primary", "structural", False,
            evidence_status="OBSERVED", confidence=0.9,
            evidence=["fixture observation: one visible blockout component"],
        )],
        claims=[
            ReferenceClaim(
                "fixture-primary", "primary_forms", "One box-like primary form is visible.",
                "OBSERVED", 0.9, evidence=["fixture observation"], impact="high",
                component_refs=["stage_gate_asset"],
                modeling_consequence="Start from the observed primary component.",
            ),
            ReferenceClaim(
                "fixture-construction", "construction_hypotheses", "A single mesh is sufficient for this fixture.",
                "STRONGLY_INFERRED", 0.8, evidence=["one visible component"], impact="high",
                component_refs=["stage_gate_asset"],
                modeling_consequence="Keep the test asset as one editable mesh.",
            ),
        ],
        strategies=[StrategyCandidate(
            "single-editable-box", "BOX_MESH", ["fixture-primary", "fixture-construction"],
        )],
        require_evidence_bindings=True,
    )

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
    planned_capture = plan_next_decision(PlannerContext(
        task_id="stage-gate-lab", asset_id="stage-gate-asset", stage="PRIMARY_BLOCKOUT",
        session_id=server.session_id, scene_revision=decision_state.current_revision(),
        active_object=obj.name, reference_decomposition=decomposition,
    )).to_dict()
    live_coverage = server.cmd_check_scene_component_coverage(decomposition.to_dict())
    coverage = live_coverage
    weak_visual = advance_stage(obj.name, "PROPORTION_SILHOUETTE", {
        "dimensions_checked": True, "primary_components_present": True,
        "component_coverage": {**coverage, "pass": False},
    })
    state_after_weak_visual = {"stage": get_stage(obj.name), "log_count": len(get_stage_log(obj.name))}
    decision_state.advance_revision(live_coverage["scene_revision"])
    stale_visual = advance_stage(obj.name, "PROPORTION_SILHOUETTE", {
        "dimensions_checked": True, "primary_components_present": True,
        "component_coverage": coverage,
    })
    state_after_stale = {"stage": get_stage(obj.name), "log_count": len(get_stage_log(obj.name))}
    live_coverage = server.cmd_check_scene_component_coverage(decomposition.to_dict())
    coverage = live_coverage
    strong_visual = advance_stage(obj.name, "PROPORTION_SILHOUETTE", {
        "dimensions_checked": True, "primary_components_present": True,
        "component_coverage": coverage,
    })
    final_log = get_stage_log(obj.name)
    assertions = {
        "open_reference_question_rejected": not weak_primary["advanced"],
        "rejection_did_not_mutate": state_after_weak == {"stage": "REFERENCE_ANALYSIS", "log_count": 0},
        "primary_advanced": strong_primary["advanced"],
        "planner_requested_live_coverage": (
            planned_capture["action"] == "CAPTURE_LIVE_COMPONENT_COVERAGE"
            and planned_capture["operation"] == "check_scene_component_coverage"
        ),
        "incomplete_primary_blockout_rejected": not weak_visual["advanced"],
        "visual_rejection_did_not_mutate": state_after_weak_visual == {"stage": "PRIMARY_BLOCKOUT", "log_count": 1},
        "stale_coverage_rejected": (
            not stale_visual["advanced"]
            and any("recapture after the edit" in failure for failure in stale_visual["gate"]["failures"])
        ),
        "stale_rejection_did_not_mutate": state_after_stale == {"stage": "PRIMARY_BLOCKOUT", "log_count": 1},
        "complete_primary_blockout_advanced": strong_visual["advanced"],
        "coverage_captured_from_live_modeler": (
            live_coverage["capture_type"] == "LIVE_MODELER_RUNTIME"
            and live_coverage["pass"]
            and live_coverage["mesh_object_names"] == [obj.name]
        ),
        "only_accepted_transitions_logged": len(final_log) == 2,
    }
    report = {
        "lab": "machine_enforced_modeling_stage_gates",
        "attempts": [weak_primary, strong_primary, weak_visual, stale_visual, strong_visual],
        "planned_capture": planned_capture,
        "live_component_coverage": live_coverage,
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
