"""Explicit uncertainty and evidence-based rebuild-versus-patch decisions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Diagnosis:
    diagnosis: str
    confidence: float
    alternatives: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.diagnosis.strip():
            raise ValueError("diagnosis is required")

    def next_action(self, research_threshold: float = 0.65) -> str:
        self.validate()
        if self.confidence < research_threshold:
            return "INSPECT_OR_RESEARCH"
        return "TEST_LOCAL_ACTION"


@dataclass
class RegionRepairHistory:
    region_id: str
    failed_repairs: int = 0
    topology_degradation: float = 0.0
    visual_improvement: float = 0.0
    complexity_growth: float = 0.0

    def decision(self) -> dict:
        pressure = (
            self.failed_repairs * 1.0
            + max(0.0, self.topology_degradation) * 2.0
            + max(0.0, self.complexity_growth)
            - max(0.0, self.visual_improvement) * 1.5
        )
        rebuild = self.failed_repairs >= 2 and pressure >= 3.0
        return {
            "region_id": self.region_id,
            "decision": "REBUILD_REGION" if rebuild else "PATCH_OR_INSPECT",
            "pressure": round(pressure, 4),
            "evidence": {
                "failed_repairs": self.failed_repairs,
                "topology_degradation": self.topology_degradation,
                "visual_improvement": self.visual_improvement,
                "complexity_growth": self.complexity_growth,
            },
        }


def validate_multiview_metrics(before: dict[str, float], after: dict[str, float], tolerance: float = 0.0) -> dict:
    missing = sorted(set(before) - set(after))
    regressions = {
        view: after[view] - score
        for view, score in before.items()
        if view in after and after[view] > score + tolerance
    }
    return {
        "checked_views": sorted(set(before) & set(after)),
        "missing_views": missing,
        "regressions": regressions,
        "pass": not missing and not regressions,
    }


def validate_component_graph(components: list[dict], relationships: list[dict]) -> dict:
    names = [item.get("id") for item in components]
    duplicate_ids = sorted({name for name in names if names.count(name) > 1})
    missing_ids = sorted({name for name in names if not name})
    known = set(names) - {None, ""}
    dangling = [
        item
        for item in relationships
        if item.get("from") not in known or item.get("to") not in known
    ]
    return {
        "component_count": len(components),
        "duplicate_ids": duplicate_ids,
        "missing_ids": missing_ids,
        "dangling_relationships": dangling,
        "pass": not duplicate_ids and not missing_ids and not dangling,
    }
