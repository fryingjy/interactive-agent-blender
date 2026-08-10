"""Append-only local telemetry for whether retrieved skills changed outcomes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SkillUsage:
    skill_id: str
    decision_id: str
    asset_id: str
    scene_revision_before: int
    scene_revision_after: int
    problem: str
    action: str
    success: bool
    measured_effect: dict[str, Any] = field(default_factory=dict)
    unexpected_effects: list[str] = field(default_factory=list)
    blender_version: str | None = None
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> None:
        if self.scene_revision_after <= self.scene_revision_before:
            raise ValueError("scene revision must advance")
        for required in (self.skill_id, self.decision_id, self.asset_id, self.problem, self.action):
            if not str(required).strip():
                raise ValueError("usage identity, problem, and action fields are required")


class SkillUsageLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, usage: SkillUsage) -> None:
        usage.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(usage), sort_keys=True) + "\n")

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def summary(self, skill_id: str | None = None) -> dict:
        rows = [row for row in self.read() if skill_id is None or row["skill_id"] == skill_id]
        successes = sum(1 for row in rows if row["success"])
        return {
            "uses": len(rows),
            "successes": successes,
            "failures": len(rows) - successes,
            "success_rate": successes / len(rows) if rows else None,
        }
