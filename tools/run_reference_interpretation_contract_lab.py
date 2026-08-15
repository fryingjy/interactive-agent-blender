"""Declared-case lab for evidence-bound reference interpretation and planning.

This is a pure-Python policy experiment. It proves that typed reference claims
change planner output across two object families; it does not prove visual
inference, Blender execution, or held-out modeling quality.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.scene_decomposition import (
    Component,
    ReferenceClaim,
    Relationship,
    SceneDecomposition,
    StrategyCandidate,
)
from knowledge_engine.strategy import ModelingBrief, choose_strategy


OUT = REPO_ROOT / "runs" / "2026-08-15_reference-interpretation-contract"


def _component(name: str, role: str = "primary", *, separate: bool | None = None) -> Component:
    return Component(
        name=name,
        role=role,
        manufacture="structural",
        separately_manufactured=separate,
        evidence_status="OBSERVED",
        confidence=0.9,
        evidence=[f"declared reference observation: {name} has a distinct visible silhouette"],
    )


def _path_lamp(*, unknown_depth: bool = False, conflicting_path: bool = False) -> SceneDecomposition:
    claims = [
        ReferenceClaim(
            "lamp-primary", "primary_forms", "The shade is the dominant enclosing form.",
            "OBSERVED", 0.95,
            evidence=["front view: shade occupies the dominant silhouette area"],
            modeling_consequence="Block the shade before fittings.", impact="high",
            component_refs=["shade"],
        ),
        ReferenceClaim(
            "cable-path", "continuous_surfaces", "The hanging cable follows one continuous path.",
            "STRONGLY_INFERRED", 0.85,
            evidence=["front and side views: uninterrupted curved cable contour"],
            modeling_consequence="Represent the cable with an editable curve.", impact="high",
            component_refs=["cable"], modeling_signals={"follows_path": True},
        ),
        ReferenceClaim(
            "cable-separate", "separate_parts", "The cable is separate from the shade.",
            "OBSERVED", 0.95,
            evidence=["front view: visible socket boundary and independent material"],
            modeling_consequence="Keep the cable as a separate component.", impact="high",
            component_refs=["shade", "cable"],
            modeling_signals={"independent_motion_or_material": True},
        ),
        ReferenceClaim(
            "lamp-construction", "construction_hypotheses",
            "Use a mesh shade, separate socket, and curve cable.",
            "STRONGLY_INFERRED", 0.85,
            evidence=["lamp-primary", "cable-path", "cable-separate"],
            modeling_consequence="Preserve three editable construction units.", impact="high",
            component_refs=["shade", "cable"],
        ),
    ]
    if unknown_depth:
        claims.append(ReferenceClaim(
            "socket-depth", "depth_order", "The rear socket projection is not visible.",
            "UNKNOWN", 0.1, impact="high", component_refs=["shade"],
        ))
    if conflicting_path:
        claims.append(ReferenceClaim(
            "cable-segmented", "ambiguities", "A detail view depicts a rigid segmented cable.",
            "OBSERVED", 0.9,
            evidence=["detail view: three straight rigid segments are visible"],
            modeling_consequence="Resolve the conflict before selecting a representation.",
            component_refs=["cable"], modeling_signals={"follows_path": False},
        ))
    return SceneDecomposition(
        object_name="pendant lamp",
        object_class="lighting fixture",
        reference_style="mixed",
        components=[_component("shade"), _component("cable", separate=True)],
        relationships=[Relationship(
            "cable", "shade", "attached_to", evidence_status="OBSERVED", confidence=0.9,
            evidence=["front view: cable terminates at shade socket"],
        )],
        claims=claims,
        strategies=[
            StrategyCandidate(
                "mesh-shade-curve-cable", "BOX_MESH + CURVE",
                ["lamp-primary", "cable-path", "cable-separate", "lamp-construction"],
            ),
            StrategyCandidate(
                "monolithic-lamp", "CONTINUOUS_MESH", ["cable-separate"], status="rejected",
                rejection_reason="Contradicts the observed socket boundary and independent cable.",
            ),
        ],
        require_evidence_bindings=True,
    )


def _control_panel() -> SceneDecomposition:
    return SceneDecomposition(
        object_name="appliance control panel",
        object_class="manufactured enclosure",
        reference_style="photo",
        components=[_component("housing"), _component("control_panel", separate=True)],
        relationships=[Relationship(
            "control_panel", "housing", "inset_into", evidence_status="OBSERVED", confidence=0.92,
            evidence=["oblique view: panel border sits behind the housing rim"],
        )],
        claims=[
            ReferenceClaim(
                "housing-primary", "primary_forms", "The housing is a planar box-like enclosure.",
                "OBSERVED", 0.96, evidence=["front and side views: planar panels and straight edges"],
                modeling_consequence="Use a box mesh for the primary enclosure.", impact="high",
                component_refs=["housing"],
            ),
            ReferenceClaim(
                "panel-separate", "separate_parts", "The inset control panel is a separate part.",
                "STRONGLY_INFERRED", 0.82,
                evidence=["oblique view: continuous reveal gap surrounds the panel"],
                modeling_consequence="Keep the inset panel independently editable.", impact="high",
                component_refs=["housing", "control_panel"],
                modeling_signals={"independent_motion_or_material": True},
            ),
            ReferenceClaim(
                "panel-construction", "construction_hypotheses",
                "Use a box-modeled housing and a separate inset panel.",
                "STRONGLY_INFERRED", 0.86,
                evidence=["housing-primary", "panel-separate"],
                modeling_consequence="Preserve the reveal gap and separate panel boundary.", impact="high",
                component_refs=["housing", "control_panel"],
            ),
            ReferenceClaim(
                "weak-curvature", "ambiguities", "Reflections may imply a curved housing path.",
                "WEAKLY_INFERRED", 0.3, evidence=["single specular highlight"],
                modeling_consequence="Do not convert the highlight into geometry without another view.",
                component_refs=["housing"], modeling_signals={"follows_path": True},
            ),
        ],
        strategies=[StrategyCandidate(
            "box-housing-separate-panel", "BOX_MESH + SEPARATE_COMPONENT",
            ["housing-primary", "panel-separate", "panel-construction"],
        )],
        require_evidence_bindings=True,
    )


def _planner_context(decomposition: SceneDecomposition, *, stage: str, tickets=None, health=None):
    return PlannerContext(
        task_id="reference-contract-lab",
        asset_id=decomposition.object_name.replace(" ", "-"),
        stage=stage,
        session_id="declared-policy-cases",
        scene_revision=7,
        active_object=decomposition.object_name,
        base_state={"mesh_health": {}},
        evaluated_state={"mesh_health": health or {}},
        visual_tickets=tickets or [],
        reference_decomposition=decomposition,
        brief=ModelingBrief(),
    )


def main() -> None:
    lamp = _path_lamp()
    panel = _control_panel()
    unresolved = _path_lamp(unknown_depth=True)
    conflict = _path_lamp(conflicting_path=True)

    baseline = choose_strategy(ModelingBrief())
    lamp_decision = plan_next_decision(_planner_context(
        lamp,
        stage="PROPORTION_SILHOUETTE",
        tickets=[{"type": "missing_component", "target": "cable", "priority": 1, "severity": 1.0}],
    )).to_dict()
    panel_decision = plan_next_decision(_planner_context(
        panel,
        stage="PROPORTION_SILHOUETTE",
        tickets=[{"type": "missing_component", "target": "control_panel", "priority": 1, "severity": 1.0}],
    )).to_dict()
    unresolved_decision = plan_next_decision(_planner_context(
        unresolved, stage="REFERENCE_ANALYSIS",
    )).to_dict()
    technical_decision = plan_next_decision(_planner_context(
        unresolved, stage="PRIMARY_BLOCKOUT", health={"non_manifold_edges": 3},
    )).to_dict()

    cases = {
        "baseline_without_reference_claims": baseline,
        "path_lamp": {
            "readiness": lamp.blockout_readiness(),
            "derived_brief": lamp.to_modeling_brief().__dict__,
            "decision": lamp_decision,
        },
        "control_panel": {
            "readiness": panel.blockout_readiness(),
            "derived_brief": panel.to_modeling_brief().__dict__,
            "decision": panel_decision,
        },
        "unresolved_depth": {
            "readiness": unresolved.blockout_readiness(),
            "decision": unresolved_decision,
        },
        "conflicting_supported_claims": {
            "readiness": conflict.blockout_readiness(),
        },
        "technical_preemption": technical_decision,
    }
    assertions = {
        "reference_claim_changes_lamp_representation": (
            baseline["representation"]["choice"] == "BOX_MESH"
            and lamp_decision["operation_params"]["representation"] == "CURVE"
        ),
        "lamp_boundary_changes_component_policy": (
            lamp_decision["operation_params"]["component_policy"] == "SEPARATE_COMPONENTS"
        ),
        "second_family_keeps_box_representation": (
            panel_decision["operation_params"]["representation"] == "BOX_MESH"
        ),
        "weak_highlight_claim_does_not_force_curve": (
            panel.to_modeling_brief().follows_path is False
        ),
        "second_family_uses_separate_panel_policy": (
            panel_decision["operation_params"]["component_policy"] == "SEPARATE_COMPONENTS"
        ),
        "high_impact_unknown_becomes_research": (
            unresolved_decision["action"] == "RESOLVE_REFERENCE_UNCERTAINTY"
            and unresolved_decision["operation_params"]["claim_ids"] == ["socket-depth"]
        ),
        "supported_conflict_blocks_blockout": (
            conflict.blockout_readiness()["conflicting_modeling_signals"] == ["follows_path"]
            and not conflict.blockout_readiness()["ready_for_blockout"]
        ),
        "technical_breakage_retains_priority": (
            technical_decision["action"] == "LOCALIZE_NON_MANIFOLD_REGION"
        ),
    }
    report = {
        "experiment": "evidence-bound reference interpretation contract",
        "scope": "declared synthetic policy cases; no Blender, image inference, or held-out quality claim",
        "object_families": ["pendant lamp", "appliance control panel"],
        "cases": cases,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reference_interpretation_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (OUT / "session_report.md").write_text(
        "# Reference-interpretation contract lab\n\n"
        f"Result: **{'PASS' if report['pass'] else 'FAIL'}** "
        f"({sum(assertions.values())}/{len(assertions)} assertions).\n\n"
        "Two declared object families test the operational bridge from typed evidence to planning. "
        "Supported path and separation claims change the lamp plan to a curve plus separate component; "
        "a weak reflection-based claim cannot force the control panel into a curve; an important unknown "
        "becomes a research contract; contradictory supported claims block blockout; and technical breakage "
        "still preempts interpretation work.\n\n"
        "This is policy-level experimental evidence only. It does **not** prove automated image "
        "understanding, Blender execution, reference fidelity, transfer to unseen images, or professional "
        "modeling quality. Those remain separate gates.\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(OUT), "assertions": assertions, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
