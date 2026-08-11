"""Deterministic context-aware retrieval benchmark over the project skill store."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore


CASES = [
    ("boolean_tangent", RetrievalContext("tangent boolean groove degenerates", workflow="boolean", defect="non manifold zero length", modifiers=["BOOLEAN"]), "boolean-groove-cut-topology-cleanup"),
    ("material_orphan", RetrievalContext("unused material slot", workflow="materials", defect="orphan assignment"), "material-slot-orphan-assignment"),
    ("node_color", RetrievalContext("diffuse color not rendered", workflow="materials", defect="principled base color"), "diffuse-color-not-connected-to-bsdf"),
    ("subd_boundary", RetrievalContext("subdivision boundary pinching mismatch", workflow="subdivision", defect="boundary resolution", modifiers=["SUBSURF"]), "subd.boundary_resolution.match_quads_over_triangulate"),
    ("mirror_stack", RetrievalContext("mirror subdivision seam", workflow="modifier-stack", defect="non manifold seam", modifiers=["MIRROR", "SUBSURF"]), "modifier.stack_order.subd_safe_mirror_placement"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-dir", default="knowledge/skills")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    store = StructuredSkillStore(args.skills_dir)
    records = []
    for case_id, context, expected in CASES:
        results = store.search(context, top_k=3)
        actual = results[0]["skill_id"] if results else None
        records.append({
            "case_id": case_id,
            "context": context.__dict__,
            "expected_top_skill": expected,
            "actual_top_skill": actual,
            "pass": actual == expected,
            "top_results": [{"skill_id": item["skill_id"], "score": item["score"], "score_breakdown": item["score_breakdown"]} for item in results],
        })
    report = {"benchmark": "structured_cross_session_skill_retrieval", "records": records, "accuracy": sum(item["pass"] for item in records) / len(records), "pass": all(item["pass"] for item in records)}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("retrieval benchmark failed")


if __name__ == "__main__":
    main()
