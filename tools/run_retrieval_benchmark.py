"""Deterministic positive-and-abstention benchmark over the project skill store."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.retrieval import (  # noqa: E402
    DEFAULT_MIN_RETRIEVAL_SCORE,
    RetrievalContext,
    StructuredSkillStore,
)


DEFAULT_CASES = REPO_ROOT / "knowledge" / "foundation" / "retrieval_benchmark_cases.json"


def load_cases(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not cases:
        raise ValueError("retrieval benchmark requires at least one case")
    ids = [case.get("case_id") for case in cases]
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError("every retrieval case needs a unique case_id")
    for case in cases:
        if case.get("kind") not in {"positive", "abstention"}:
            raise ValueError(f"{case['case_id']}: kind must be positive or abstention")
        if case["kind"] == "positive" and not case.get("expected_top_skill"):
            raise ValueError(f"{case['case_id']}: positive case needs expected_top_skill")
        if case["kind"] == "abstention" and case.get("expected_top_skill") is not None:
            raise ValueError(f"{case['case_id']}: abstention case must expect null")
        RetrievalContext(**case.get("context", {}))
    return cases


def run_benchmark(cases: list[dict], skills_dir: Path, min_score: float) -> dict:
    store = StructuredSkillStore(skills_dir)
    records = []
    for case in cases:
        context = RetrievalContext(**case["context"])
        results = store.search(context, top_k=3, min_score=min_score)
        actual = results[0]["skill_id"] if results else None
        expected = case.get("expected_top_skill")
        runner_up_score = results[1]["score"] if len(results) > 1 else 0.0
        margin = round(results[0]["score"] - runner_up_score, 4) if results else None
        required_margin = float(case.get("minimum_top_margin", 0.0))
        identity_pass = actual == expected
        margin_pass = case["kind"] == "abstention" or (
            margin is not None and margin >= required_margin
        )
        records.append({
            "case_id": case["case_id"],
            "kind": case["kind"],
            "context": context.__dict__,
            "expected_top_skill": expected,
            "actual_top_skill": actual,
            "minimum_top_margin": required_margin,
            "actual_top_margin": margin,
            "identity_pass": identity_pass,
            "margin_pass": margin_pass,
            "pass": identity_pass and margin_pass,
            "top_results": [
                {
                    "skill_id": item["skill_id"],
                    "score": item["score"],
                    "score_breakdown": item["score_breakdown"],
                }
                for item in results
            ],
        })

    positives = [record for record in records if record["kind"] == "positive"]
    abstentions = [record for record in records if record["kind"] == "abstention"]
    return {
        "benchmark": "structured_cross_session_skill_retrieval_with_abstention",
        "case_count": len(records),
        "minimum_score": min_score,
        "positive_accuracy": sum(item["pass"] for item in positives) / len(positives),
        "abstention_accuracy": sum(item["pass"] for item in abstentions) / len(abstentions),
        "records": records,
        "pass": all(item["pass"] for item in records),
        "claim_boundary": (
            "A frozen deterministic regression over authored cases; it tests executable retrieval "
            "and abstention, not human-independent judgment or long-term cognitive retention."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-dir", type=Path, default=REPO_ROOT / "knowledge" / "skills")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_RETRIEVAL_SCORE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = run_benchmark(load_cases(args.cases), args.skills_dir, args.min_score)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("retrieval benchmark failed")


if __name__ == "__main__":
    main()
