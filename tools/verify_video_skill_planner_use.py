"""Prove that a transfer-validated video skill changes a matching planner decision."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.planner import PlannerContext, plan_next_decision  # noqa: E402
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore  # noqa: E402


def main() -> int:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
        ROOT / "runs" / "2026-08-15_video-transfer-uniform-deformation" / "planner_use_verification.json"
    )
    store = StructuredSkillStore(ROOT / "knowledge" / "skills")
    query = RetrievalContext(
        query="stepped wavy profile from uneven loop spacing before deformation",
        modeling_stage="PROPORTION_SILHOUETTE",
        workflow="subdivision deformation",
        surface_type="smooth concave taper",
        defect="uneven deformation density",
        local_topology=["connected quad rings", "uneven axial spacing"],
        modifiers=["SUBSURF"],
        blender_version="5.2",
    )
    retrieved = store.search(query, top_k=5)
    ticket = {
        "type": "uneven_deformation_density",
        "target": "lamp_pedestal_waist",
        "priority": 1,
        "severity": 0.74,
        "operation_params": {"edge_ids": [101, 102], "cuts": 6},
    }
    base_context = dict(
        task_id="planner-transfer-proof",
        asset_id="unseen-lamp-pedestal",
        stage="PROPORTION_SILHOUETTE",
        session_id="offline-planner-proof",
        scene_revision=7,
        active_object="Pedestal",
        base_state={"mesh_health": {}},
        evaluated_state={"mesh_health": {}},
        visual_tickets=[ticket],
    )
    without_skill = plan_next_decision(PlannerContext(**base_context)).to_dict()
    with_skill = plan_next_decision(PlannerContext(**base_context, retrieved_skills=retrieved)).to_dict()
    expected_skill = "deformation.topology.uniform_rings_before_shaping"
    checks = {
        "expected_skill_retrieved_first": bool(retrieved and retrieved[0]["skill_id"] == expected_skill),
        "expected_skill_is_transfer_validated": bool(retrieved and retrieved[0]["status"] == "TRANSFER_VALIDATED"),
        "without_skill_remains_inspection": without_skill["disposition"] == "INSPECT",
        "with_skill_changes_to_scoped_action": (
            with_skill["disposition"] == "ACT"
            and with_skill["action"] == "ESTABLISH_UNIFORM_DEFORMATION_RINGS"
            and with_skill["operation"] == "loop_cut_selection"
        ),
        "scene_owned_target_and_parameters_preserved": (
            with_skill["target_region"] == ticket["target"]
            and with_skill["operation_params"] == ticket["operation_params"]
        ),
        "skill_provenance_reaches_contract": expected_skill in with_skill["retrieved_skill_ids"],
        "technical_priority_not_bypassed": (
            plan_next_decision(PlannerContext(
                **{**base_context, "evaluated_state": {"mesh_health": {"non_manifold_edges": 3}}},
                retrieved_skills=retrieved,
            )).action
            == "LOCALIZE_NON_MANIFOLD_REGION"
        ),
    }
    result = {
        "query": query.__dict__,
        "retrieved": [
            {
                "skill_id": item["skill_id"],
                "score": item["score"],
                "score_breakdown": item["score_breakdown"],
                "status": item["status"],
            }
            for item in retrieved
        ],
        "ticket": ticket,
        "without_skill": without_skill,
        "with_skill": with_skill,
        "checks": checks,
        "pass": all(checks.values()),
        "boundary": "Controlled planner proof only; runtime_usage remains empty until a real asset transaction uses and verifies this skill.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
