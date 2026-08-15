"""Verify question-driven reference research and its stage-gate effect."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender_ops.stage_gates import evaluate_stage_gate  # noqa: E402
from knowledge_engine.reference_analysis import (  # noqa: E402
    audit_reference_set,
    build_reference_stage_evidence,
    reference_set_from_dict,
)
from knowledge_engine.planner import PlannerContext, plan_next_decision  # noqa: E402
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore  # noqa: E402


RUN = ROOT / "runs" / "2026-08-15_question-driven-reference-research"
MANIFEST = ROOT / "runs" / "2026-08-15_reference-gathering-bialetti" / "reference_manifest.json"


def audited(payload):
    return audit_reference_set(reference_set_from_dict(payload))


def main() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    baseline = audited(payload)

    open_high = copy.deepcopy(payload)
    envelope = next(
        question
        for question in open_high["research_questions"]
        if question["question_id"] == "q-overall-envelope"
    )
    envelope["status"] = "OPEN"
    envelope["resolution"] = ""
    open_high_audit = audited(open_high)

    broken_link = copy.deepcopy(payload)
    broken_link["research_questions"][0]["candidates"][0]["accepted_reference_id"] = "missing"
    broken_link_audit = audited(broken_link)

    missing_constraint = copy.deepcopy(payload)
    underside = next(
        question
        for question in missing_constraint["research_questions"]
        if question["question_id"] == "q-boiler-underside"
    )
    underside["modeling_constraint"] = ""
    missing_constraint_error = None
    try:
        audited(missing_constraint)
    except ValueError as exc:
        missing_constraint_error = str(exc)

    stage_evidence = build_reference_stage_evidence(
        baseline,
        component_graph_pass=True,
        measured_ratio_count=3,
        uncertainty_recorded=True,
    )
    passing_gate = evaluate_stage_gate("REFERENCE_ANALYSIS", stage_evidence)
    failing_gate = evaluate_stage_gate(
        "REFERENCE_ANALYSIS",
        {**stage_evidence, "question_driven_research_pass": False},
    )
    store = StructuredSkillStore(ROOT / "knowledge" / "skills")
    retrieved = store.search(RetrievalContext(
        query="unknown boiler underside needs targeted evidence search and candidate rejection",
        modeling_stage="REFERENCE_ANALYSIS",
        workflow="reference-driven reconstruction",
        reference_issue="missing underside view and variant conflict",
    ))
    planner = plan_next_decision(PlannerContext(
        task_id="bialetti-reference-research",
        asset_id="bialetti-moka-3cup",
        stage="REFERENCE_ANALYSIS",
        session_id="reference-only",
        scene_revision=0,
        stage_evidence={
            "targeted_research_queries": open_high_audit["targeted_research_queries"]
        },
        retrieved_skills=retrieved,
    ))

    research = baseline["research_audit"]
    checks = {
        "bialetti_reference_set_ready": baseline["pass"] is True,
        "three_questions_recorded": research["question_count"] == 3,
        "candidate_dispositions_exact": research["candidate_counts"] == {
            "ACCEPTED": 2, "REJECTED": 5, "PENDING": 0,
        },
        "two_deferred_constraints_preserved": (
            len(research["deferred_questions"]) == 2
            and len(research["modeling_constraints"]) == 2
        ),
        "no_high_impact_question_open": research["blocking_questions"] == [],
        "open_high_question_blocks_modeling": (
            open_high_audit["disposition"] == "TARGETED_RESEARCH"
            and "q-overall-envelope" in open_high_audit["research_audit"]["blocking_questions"]
            and len(open_high_audit["targeted_research_queries"]) == 2
        ),
        "broken_accepted_link_fails": (
            broken_link_audit["pass"] is False
            and broken_link_audit["research_audit"]["missing_reference_links"]
            == ["q-overall-envelope:missing"]
        ),
        "deferred_without_constraint_rejected": (
            missing_constraint_error is not None
            and "modeling constraint" in missing_constraint_error
        ),
        "stage_gate_accepts_complete_research": passing_gate["pass"] is True,
        "stage_gate_rejects_unaudited_questions": (
            failing_gate["pass"] is False
            and "high-impact reference questions remain open or unaudited" in failing_gate["failures"]
        ),
        "skill_retrieval_ranks_question_driven_research_first": (
            bool(retrieved)
            and retrieved[0]["skill_id"] == "reference.question-driven-targeted-research"
        ),
        "planner_research_contract_retains_skill_provenance": (
            planner.disposition == "RESEARCH"
            and planner.action == "TARGETED_REFERENCE_RESEARCH"
            and "reference.question-driven-targeted-research" in planner.retrieved_skill_ids
        ),
    }
    report = {
        "experiment": "question_driven_reference_research_contract",
        "manifest": str(MANIFEST),
        "baseline": baseline,
        "negative_controls": {
            "open_high_impact_question": open_high_audit,
            "broken_accepted_reference_link": broken_link_audit,
            "missing_deferred_constraint_error": missing_constraint_error,
            "failing_stage_gate": failing_gate,
        },
        "passing_stage_gate": passing_gate,
        "retrieval": retrieved,
        "planner_contract": planner.to_dict(),
        "checks": checks,
        "pass": all(checks.values()),
        "boundary": (
            "This proves executable research provenance and gating behavior. "
            "It does not replace the pending human board review or prove that a model will be accurate."
        ),
    }
    (RUN / "verification_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"checks": checks, "pass": report["pass"]}, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
