#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.retrieval import (
    DEFAULT_MIN_RETRIEVAL_SCORE,
    RetrievalContext,
    StructuredSkillStore,
)

SKILLS_DIR = REPO_ROOT / "knowledge" / "skills"

REQUIRED_FIELDS = {
    "id", "title", "topic_tags", "problem", "symptom", "fix",
    "evidence", "learned_at", "learned_during", "source_session", "applicability",
}


def _load_all():
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    return [json.loads(p.read_text()) for p in SKILLS_DIR.glob("*.json")]


def add(skill: dict):
    missing = REQUIRED_FIELDS - skill.keys()
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    path = SKILLS_DIR / f"{skill['id']}.json"
    path.write_text(json.dumps(skill, indent=2))
    return path


def get(skill_id):
    path = SKILLS_DIR / f"{skill_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def search(query, top_k=5):
    terms = [t.lower() for t in query.split()]
    scored = []
    for skill in _load_all():
        tags = [t.lower() for t in skill.get("topic_tags", [])]
        haystack = " ".join([
            skill.get("title", ""),
            " ".join(tags),
            skill.get("problem", ""),
            skill.get("symptom", ""),
            skill.get("applicability", ""),
        ]).lower()
        score = 0
        for t in terms:
            if t in tags:
                score += 3
            score += haystack.count(t)
        if score > 0:
            scored.append((score, skill))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:top_k]]


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--top-k", type=int, default=5)

    p_structured = sub.add_parser("search-structured")
    p_structured.add_argument("query")
    p_structured.add_argument("--top-k", type=int, default=5)
    p_structured.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_RETRIEVAL_SCORE,
    )
    p_structured.add_argument("--modeling-stage")
    p_structured.add_argument("--workflow")
    p_structured.add_argument("--surface-type")
    p_structured.add_argument("--defect")
    p_structured.add_argument("--local-topology", action="append", default=[])
    p_structured.add_argument("--modifier", action="append", default=[])
    p_structured.add_argument("--reference-issue")
    p_structured.add_argument("--blender-version")

    p_get = sub.add_parser("get")
    p_get.add_argument("skill_id")

    p_add = sub.add_parser("add")
    p_add.add_argument("--data-file", required=True)

    args = parser.parse_args()
    if args.cmd == "search":
        results = search(args.query, args.top_k)
        print(json.dumps([{"id": s["id"], "title": s["title"]} for s in results], indent=2))
    elif args.cmd == "search-structured":
        context = RetrievalContext(
            query=args.query,
            modeling_stage=args.modeling_stage,
            workflow=args.workflow,
            surface_type=args.surface_type,
            defect=args.defect,
            local_topology=args.local_topology,
            modifiers=args.modifier,
            reference_issue=args.reference_issue,
            blender_version=args.blender_version,
        )
        results = StructuredSkillStore(SKILLS_DIR).search(
            context,
            top_k=args.top_k,
            min_score=args.min_score,
        )
        print(json.dumps([
            {
                "skill_id": result["skill_id"],
                "score": result["score"],
                "score_breakdown": result["score_breakdown"],
                "status": result["status"],
            }
            for result in results
        ], indent=2))
    elif args.cmd == "get":
        skill = get(args.skill_id)
        if skill is None:
            print(f"ERROR: skill '{args.skill_id}' not found", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(skill, indent=2))
    elif args.cmd == "add":
        skill = json.loads(Path(args.data_file).read_text())
        path = add(skill)
        print(f"added skill '{skill['id']}' -> {path}")


if __name__ == "__main__":
    main()
