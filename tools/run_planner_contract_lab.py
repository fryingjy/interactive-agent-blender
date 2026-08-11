"""Declared-case regression lab for the next-decision planner."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.reasoning import Diagnosis, RegionRepairHistory
from knowledge_engine.strategy import ModelingBrief


OUT = REPO_ROOT / "runs" / "2026-08-10_planner-contract"


def context(**changes):
    values = dict(
        task_id="planner-lab",
        asset_id="declared-case",
        stage="PROPORTION_SILHOUETTE",
        session_id="lab-session",
        scene_revision=12,
        active_object="Asset",
        base_state={"mesh_health": {}},
        evaluated_state={"mesh_health": {}},
        stage_evidence={},
    )
    values.update(changes)
    return PlannerContext(**values)


def main():
    cases = {
        "ownership_wait": context(control_mode="USER_CONTROL"),
        "external_edit": context(external_edit_detected=True),
        "technical_before_visual": context(
            evaluated_state={"mesh_health": {"non_manifold_edges": 8}},
            visual_tickets=[{"type": "silhouette", "severity": 1.0, "priority": 1}],
        ),
        "rebuild_pressure": context(
            evaluated_state={"mesh_health": {"non_manifold_edges": 8}},
            repair_history=RegionRepairHistory("rim", 3, 0.8, 0.1, 1.0),
        ),
        "low_confidence_research": context(diagnosis=Diagnosis("possible pinch", 0.4, ["healthy curvature", "bad pole"])),
        "missing_path_component": context(
            visual_tickets=[{"type": "missing_component", "target": "cable", "severity": 1.0, "priority": 1}],
            brief=ModelingBrief(follows_path=True, independent_motion_or_material=True),
        ),
        "measured_local_action": context(visual_tickets=[{
            "type": "contour_error", "target": "outer_rim", "severity": 0.7, "priority": 1,
            "suggested_operation": "scale_selection", "operation_params": {"factor": [1.05, 1, 1]},
        }]),
        "unlocalized_visual_inspection": context(visual_tickets=[{"type": "contour_error", "severity": 0.7, "priority": 1}]),
        "stage_advance": context(stage_evidence={"view_count": 3, "worst_view_iou": 0.93, "multiview_regression_pass": True}),
        "missing_gate_evidence": context(stage="TOPOLOGY_SURFACE", stage_evidence={}),
    }
    results = {name: plan_next_decision(item).to_dict() for name, item in cases.items()}
    assertions = {
        "ownership_never_mutates": results["ownership_wait"]["disposition"] == "WAIT" and results["ownership_wait"]["operation"] is None,
        "external_edit_reobserves": results["external_edit"]["action"] == "REOBSERVE_AFTER_EXTERNAL_EDIT",
        "technical_preempts_visual": results["technical_before_visual"]["action"] == "LOCALIZE_NON_MANIFOLD_REGION",
        "repeated_failure_rebuilds": results["rebuild_pressure"]["action"] == "REBUILD_OPEN_REGION",
        "uncertainty_researches": results["low_confidence_research"]["disposition"] == "RESEARCH",
        "path_component_uses_curve": results["missing_path_component"]["operation"] == "create_curve",
        "ticket_can_drive_one_typed_action": results["measured_local_action"]["operation"] == "scale_selection",
        "unlocalized_ticket_inspects": results["unlocalized_visual_inspection"]["disposition"] == "INSPECT",
        "passed_gate_advances": results["stage_advance"]["next_stage"] == "SECONDARY_FORMS",
        "unsupported_gate_collects_evidence": results["missing_gate_evidence"]["action"] == "COLLECT_STAGE_GATE_EVIDENCE",
        "every_contract_has_one_disposition": all(bool(item["disposition"]) and bool(item["action"]) for item in results.values()),
        "every_contract_is_revision_bound": all(item["observed_revision"] == 12 for item in results.values()),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"cases": results, "assertions": assertions, "pass": all(assertions.values())}
    (OUT / "planner_contract_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "session_report.md").write_text(
        "# Planner decision-contract lab\n\n"
        f"Result: {'PASS' if report['pass'] else 'FAIL'} ({sum(assertions.values())}/{len(assertions)} assertions).\n\n"
        "The lab verifies authority, stale-state recovery, technical-before-visual priority, "
        "rebuild pressure, uncertainty-driven research, strategy selection, local visual-ticket "
        "actions, and evidence-bound stage advancement. It is a declared-case regression lab, "
        "not held-out asset evidence.\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(OUT), "assertions": assertions, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
