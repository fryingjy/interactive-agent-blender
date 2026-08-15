"""Measure masks, resolve strategies, and prove planner behavior for the Blender fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.component_strategy import (
    ComponentStrategyEvidence,
    resolve_component_strategy,
)
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.strategy import ModelingBrief
from knowledge_engine.visual_compare import compare_image_files


OUT = ROOT / "runs" / "2026-08-15_secondary-view-component-strategy"


def stage_evidence() -> dict:
    return {
        "component_graph_pass": True,
        "measured_ratio_count": 2,
        "uncertainty_recorded": True,
        "reference_set_audit_pass": True,
        "same_target_identity_pass": True,
        "view_coverage_pass": True,
        "critical_property_coverage_pass": True,
        "conflicts_resolved_pass": True,
        "question_driven_research_pass": True,
    }


def measure(build: dict, family: str, label: str) -> dict[str, dict]:
    metrics = {}
    for view in ("front", "top"):
        target = Path(build["mask_evidence"][family][view]["target"]["retained_path"])
        candidate_record = build["mask_evidence"][family][view][label]
        candidate = (
            target
            if candidate_record["equals_target"]
            else Path(candidate_record["retained_path"])
        )
        metrics[view] = compare_image_files(target, candidate)
    return metrics


def resolution_for(family: str, metrics: dict, fresh: dict, *, secondary: bool) -> dict:
    candidates = []
    for label, policy in (
        ("continuous", "CONTINUOUS_MESH"),
        ("separate", "SEPARATE_COMPONENTS"),
    ):
        topology = fresh["families"][family][label]
        candidates.append(ComponentStrategyEvidence(
            candidate_id=f"{family}-{label}",
            component_policy=policy,
            object_count=topology["object_count"],
            connected_component_count=topology["connected_component_count"],
            view_iou={view: values["silhouette_iou"] for view, values in metrics[label].items()},
        ))
    return resolve_component_strategy(
        candidates,
        primary_view="front",
        secondary_views=("top",) if secondary else (),
        primary_ambiguity_max=0.01,
        secondary_margin_min=0.15,
        secondary_iou_min=0.80,
    )


def planner_records(primary_only: dict, resolved: dict) -> dict:
    research = plan_next_decision(PlannerContext(
        task_id="secondary-view-component-strategy",
        asset_id="controlled-housing",
        stage="REFERENCE_ANALYSIS",
        session_id="controlled-blender-5.2",
        scene_revision=1,
        stage_evidence=stage_evidence(),
        component_strategy_resolution=primary_only,
    )).to_dict()
    action = plan_next_decision(PlannerContext(
        task_id="secondary-view-component-strategy",
        asset_id="controlled-housing",
        stage="PROPORTION_SILHOUETTE",
        session_id="controlled-blender-5.2",
        scene_revision=2,
        active_object="Housing",
        visual_tickets=[{
            "type": "missing_component",
            "target": "front-boundary",
            "priority": 1,
            "severity": 1.0,
        }],
        brief=ModelingBrief(independent_motion_or_material=True),
        component_strategy_resolution=resolved,
    )).to_dict()
    return {"primary_only": research, "secondary_resolved": action}


def main() -> None:
    contract = json.loads((OUT / "experiment_contract.json").read_text(encoding="utf-8"))
    build = json.loads((OUT / "blender_build_report.json").read_text(encoding="utf-8"))
    fresh = json.loads((OUT / "fresh_process_report.json").read_text(encoding="utf-8"))
    gates = contract["frozen_gates"]
    families = {}
    assertions = {}
    for family in ("box", "radial"):
        primary_metrics = {
            label: measure(build, family, label)
            for label in ("continuous", "separate")
        }
        primary_only = resolution_for(family, primary_metrics, fresh, secondary=False)
        resolved = resolution_for(family, primary_metrics, fresh, secondary=True)
        planner = planner_records(primary_only, resolved)
        families[family] = {
            "metrics": primary_metrics,
            "primary_only_resolution": primary_only,
            "multiview_resolution": resolved,
            "planner": planner,
            "topology": fresh["families"][family],
        }
        prefix = f"{family}_"
        assertions.update({
            prefix + "front_continuous_matches": (
                primary_metrics["continuous"]["front"]["silhouette_iou"]
                >= gates["front_iou_each_min"]
            ),
            prefix + "front_separate_matches": (
                primary_metrics["separate"]["front"]["silhouette_iou"]
                >= gates["front_iou_each_min"]
            ),
            prefix + "primary_view_is_ambiguous": primary_only["primary_ambiguous"],
            prefix + "primary_only_requires_research": (
                primary_only["disposition"] == "TARGETED_REFERENCE_RESEARCH"
                and planner["primary_only"]["action"] == gates["planner_primary_only_action"]
            ),
            prefix + "continuous_top_matches": (
                primary_metrics["continuous"]["top"]["silhouette_iou"]
                >= gates["continuous_top_iou_min"]
            ),
            prefix + "separate_top_rejected": (
                primary_metrics["separate"]["top"]["silhouette_iou"]
                <= gates["separate_top_iou_max"]
            ),
            prefix + "secondary_margin_passes": (
                resolved["secondary_margin"] >= gates["secondary_margin_min"]
            ),
            prefix + "continuous_strategy_selected": (
                resolved["disposition"] == "SELECT_STRATEGY"
                and resolved["chosen_policy"] == gates["planner_resolved_component_policy"]
            ),
            prefix + "planner_uses_measured_strategy": (
                planner["secondary_resolved"]["operation_params"]["component_policy"]
                == gates["planner_resolved_component_policy"]
            ),
            prefix + "fresh_masks_reproduce": all(
                fresh["mask_hash_matches"][family][view][label]
                for label in ("target", "continuous", "separate")
                for view in ("front", "top")
            ),
        })
    assertions["fresh_process_structure_passes"] = fresh["pass"] is True
    report = {
        "experiment": contract["experiment"],
        "blender_version": fresh["blender_version"],
        "families": families,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "claim_boundary": contract["claim_boundary"],
    }
    (OUT / "analysis_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    passed = sum(assertions.values())
    (OUT / "session_report.md").write_text(
        "# Secondary-view component-strategy experiment\n\n"
        f"**Status:** {'PASS' if report['pass'] else 'FAIL'} ({passed}/{len(assertions)} checks)\n\n"
        "A rectangular and a 16-sided radial housing each compare one continuous full-depth body "
        "against a narrow body plus a separate full-front faceplate. Both candidates match the "
        "front truth, so the planner refuses to choose from that view. The fixed-frame top view "
        "reveals the depth error, selects the one-object/one-component continuous strategy, and "
        "overrides a generic separate-material prior in the planner.\n\n"
        "The saved Blender file and a fresh Blender process independently preserve object counts, "
        "connected-component counts, dimensions, collection organization, and masks.\n\n"
        "This is controlled synthetic two-family transfer, not photograph inference, a held-out "
        "prop, or professional visual acceptance.\n",
        encoding="utf-8",
    )
    print(json.dumps({"assertions": assertions, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
