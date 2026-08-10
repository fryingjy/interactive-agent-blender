"""Context-aware skill retrieval across the repository's legacy and promoted schemas."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _tokens(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, dict):
        value = " ".join(f"{key} {item}" for key, item in value.items())
    elif isinstance(value, (list, tuple, set)):
        value = " ".join(map(str, value))
    return set(re.findall(r"[a-z0-9]+", str(value).lower()))


@dataclass
class RetrievalContext:
    query: str
    modeling_stage: str | None = None
    workflow: str | None = None
    surface_type: str | None = None
    defect: str | None = None
    local_topology: list[str] = field(default_factory=list)
    modifiers: list[str] = field(default_factory=list)
    reference_issue: str | None = None
    blender_version: str | None = None


class StructuredSkillStore:
    def __init__(self, skills_dir: str | Path):
        self.skills_dir = Path(skills_dir)

    def load(self) -> list[dict]:
        records = []
        for path in sorted(self.skills_dir.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            record["_path"] = str(path)
            records.append(record)
        return records

    @staticmethod
    def skill_id(skill: dict) -> str:
        return skill.get("skill_id") or skill.get("id") or "unknown"

    @staticmethod
    def _fields(skill: dict) -> dict[str, set[str]]:
        applicability = skill.get("applicability", {})
        return {
            "query": _tokens(
                [
                    skill.get("title"),
                    skill.get("topic_tags"),
                    skill.get("problem"),
                    skill.get("symptom"),
                    skill.get("fix"),
                    skill.get("action_policy"),
                    applicability,
                ]
            ),
            "modeling_stage": _tokens(applicability.get("modeling_stage") if isinstance(applicability, dict) else None),
            "workflow": _tokens(applicability.get("workflow") if isinstance(applicability, dict) else applicability),
            "surface_type": _tokens(applicability.get("surface_type") if isinstance(applicability, dict) else None),
            "defect": _tokens([applicability.get("defect") if isinstance(applicability, dict) else None, skill.get("problem"), skill.get("symptom")]),
            "local_topology": _tokens(applicability.get("local_topology") if isinstance(applicability, dict) else None),
            "modifiers": _tokens(applicability.get("modifiers_involved") if isinstance(applicability, dict) else None),
            "reference_issue": _tokens(applicability.get("reference_issue") if isinstance(applicability, dict) else None),
        }

    @staticmethod
    def _overlap(needle: Any, haystack: set[str]) -> float:
        terms = _tokens(needle)
        if not terms:
            return 0.0
        return len(terms & haystack) / math.sqrt(len(terms))

    @staticmethod
    def _runtime_score(skill: dict) -> float:
        usage = skill.get("runtime_usage", [])
        if not usage:
            return 0.0
        successes = sum(1 for item in usage if item.get("success") is True)
        failures = sum(1 for item in usage if item.get("success") is False)
        return max(-1.0, min(2.0, (successes - failures) / max(1, len(usage)) * 2.0))

    @staticmethod
    def _version_score(requested: str | None, skill: dict) -> float:
        if not requested:
            return 0.0
        version_text = json.dumps(skill.get("version_scope", skill.get("sources", []))).lower()
        major_minor = ".".join(requested.split(".")[:2]).lower()
        if major_minor and major_minor in version_text:
            return 1.0
        if "current" in version_text or not version_text.strip("[]\" "):
            return 0.25
        return -0.25

    def search(self, context: RetrievalContext, top_k: int = 5) -> list[dict]:
        weights = {
            "query": 3.0,
            "modeling_stage": 1.25,
            "workflow": 2.0,
            "surface_type": 1.5,
            "defect": 2.5,
            "local_topology": 1.5,
            "modifiers": 2.0,
            "reference_issue": 1.25,
        }
        scored = []
        for skill in self.load():
            fields = self._fields(skill)
            breakdown = {}
            for key, weight in weights.items():
                value = context.query if key == "query" else getattr(context, key)
                contribution = weight * self._overlap(value, fields[key])
                breakdown[key] = round(contribution, 4)
            semantic_score = sum(breakdown.values())
            if semantic_score <= 0:
                continue
            breakdown["runtime_success"] = round(self._runtime_score(skill), 4)
            breakdown["version_relevance"] = round(self._version_score(context.blender_version, skill), 4)
            score = sum(breakdown.values())
            if score > 0:
                scored.append(
                    {
                        "skill_id": self.skill_id(skill),
                        "score": round(score, 4),
                        "score_breakdown": breakdown,
                        "status": skill.get("status", "UNKNOWN"),
                        "path": skill["_path"],
                        "skill": {key: value for key, value in skill.items() if key != "_path"},
                    }
                )
        return sorted(scored, key=lambda item: (-item["score"], item["skill_id"]))[:top_k]
