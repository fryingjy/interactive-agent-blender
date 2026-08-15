"""Structured readiness checks for reference-driven modeling.

The audit measures information coverage, not image count.  It deliberately keeps
view diversity, provenance diversity, target identity, and evidentiary purpose as
separate concepts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


FACTUAL_PURPOSES = {
    "PRIMARY_FORM", "ORTHOGRAPHIC", "DETAIL", "CONSTRUCTION", "DIMENSION",
    "FUNCTIONAL", "MATERIAL", "CONTEXT",
}
VALID_PROJECTIONS = {"ORTHOGRAPHIC", "PERSPECTIVE", "UNKNOWN"}


@dataclass(frozen=True)
class PropertyClaim:
    property_id: str
    purpose: str
    observation: str
    confidence: str = "MEDIUM"

    def validate(self) -> None:
        if not self.property_id or not self.observation:
            raise ValueError("property claims require property_id and observation")
        if self.purpose not in FACTUAL_PURPOSES | {"INSPIRATION"}:
            raise ValueError(f"unknown reference purpose: {self.purpose}")
        if self.confidence not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValueError(f"unknown confidence: {self.confidence}")


@dataclass(frozen=True)
class ReferenceItem:
    reference_id: str
    source_id: str
    target_id: str
    target_variant: str
    purposes: tuple[str, ...]
    view: str
    projection: str
    source_tier: str
    claims: tuple[PropertyClaim, ...] = ()
    dimensional_anchors: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        if not all((self.reference_id, self.source_id, self.target_id, self.target_variant)):
            raise ValueError("reference identity and provenance fields are required")
        if self.projection not in VALID_PROJECTIONS:
            raise ValueError(f"unknown projection: {self.projection}")
        unknown = set(self.purposes) - FACTUAL_PURPOSES - {"INSPIRATION"}
        if unknown:
            raise ValueError(f"unknown reference purposes: {sorted(unknown)}")
        for claim in self.claims:
            claim.validate()


@dataclass(frozen=True)
class ReferenceConflict:
    property_id: str
    reference_ids: tuple[str, ...]
    description: str
    resolution: str = ""
    status: str = "OPEN"


@dataclass(frozen=True)
class ReferenceSet:
    target_id: str
    target_variant: str
    items: tuple[ReferenceItem, ...]
    required_views: tuple[str, ...]
    critical_properties: tuple[str, ...]
    orthographic_required_views: tuple[str, ...] = ()
    require_dimensional_anchor: bool = False
    minimum_independent_sources: int = 1
    conflicts: tuple[ReferenceConflict, ...] = ()


def audit_reference_set(reference_set: ReferenceSet) -> dict[str, Any]:
    """Return a deterministic, JSON-safe readiness decision and research prompts."""
    if not reference_set.target_id or not reference_set.target_variant:
        raise ValueError("target_id and target_variant are required")
    if reference_set.minimum_independent_sources < 1:
        raise ValueError("minimum_independent_sources must be positive")
    for item in reference_set.items:
        item.validate()
    reference_ids = [item.reference_id for item in reference_set.items]
    if len(set(reference_ids)) != len(reference_ids):
        raise ValueError("reference_id values must be unique")
    for conflict in reference_set.conflicts:
        if conflict.status not in {"OPEN", "RESOLVED"}:
            raise ValueError(f"unknown conflict status: {conflict.status}")

    issues: list[str] = []
    queries: list[str] = []
    matching = [
        item for item in reference_set.items
        if item.target_id == reference_set.target_id
        and item.target_variant == reference_set.target_variant
    ]
    mismatched = [item.reference_id for item in reference_set.items if item not in matching]
    if mismatched:
        issues.append(f"mixed target identity or variant: {', '.join(mismatched)}")

    views = {item.view.lower() for item in matching}
    missing_views = sorted(set(map(str.lower, reference_set.required_views)) - views)
    for view in missing_views:
        issues.append(f"missing required view: {view}")
        queries.append(f"{reference_set.target_id} {reference_set.target_variant} {view} view")

    missing_ortho: list[str] = []
    for view in map(str.lower, reference_set.orthographic_required_views):
        if not any(item.view.lower() == view and item.projection == "ORTHOGRAPHIC" for item in matching):
            missing_ortho.append(view)
            issues.append(f"missing orthographic evidence: {view}")
            queries.append(f"{reference_set.target_id} {reference_set.target_variant} {view} orthographic blueprint")

    source_ids = {item.source_id for item in matching}
    if len(source_ids) < reference_set.minimum_independent_sources:
        issues.append(
            f"only {len(source_ids)} independent provenance source(s); "
            f"{reference_set.minimum_independent_sources} required"
        )
        queries.append(f"{reference_set.target_id} {reference_set.target_variant} manufacturer dimensions")

    covered_properties: dict[str, list[str]] = {}
    invalid_claims: list[str] = []
    for item in matching:
        for claim in item.claims:
            if claim.purpose not in item.purposes or claim.purpose == "INSPIRATION":
                invalid_claims.append(f"{item.reference_id}:{claim.property_id}")
                continue
            covered_properties.setdefault(claim.property_id, []).append(item.reference_id)
    if invalid_claims:
        issues.append("claims lack matching factual purpose: " + ", ".join(invalid_claims))

    missing_properties = sorted(set(reference_set.critical_properties) - set(covered_properties))
    for property_id in missing_properties:
        issues.append(f"critical property has no authoritative claim: {property_id}")
        queries.append(f"{reference_set.target_id} {reference_set.target_variant} {property_id.replace('_', ' ')}")

    anchors = [
        anchor for item in matching if "DIMENSION" in item.purposes
        for anchor in item.dimensional_anchors
    ]
    if reference_set.require_dimensional_anchor and not anchors:
        issues.append("no dimensional anchor")
        queries.append(f"{reference_set.target_id} {reference_set.target_variant} dimensions technical drawing")

    open_conflicts = [conflict.property_id for conflict in reference_set.conflicts if conflict.status != "RESOLVED"]
    for property_id in open_conflicts:
        issues.append(f"unresolved reference conflict: {property_id}")
        queries.append(f"{reference_set.target_id} {reference_set.target_variant} {property_id.replace('_', ' ')} specification")

    checks = {
        "same_target_identity_pass": not mismatched and bool(matching),
        "view_coverage_pass": not missing_views,
        "orthographic_coverage_pass": not missing_ortho,
        "provenance_coverage_pass": len(source_ids) >= reference_set.minimum_independent_sources,
        "critical_property_coverage_pass": not missing_properties and not invalid_claims,
        "dimensional_anchor_pass": bool(anchors) or not reference_set.require_dimensional_anchor,
        "conflicts_resolved_pass": not open_conflicts,
    }
    ready = all(checks.values())
    return {
        "target_id": reference_set.target_id,
        "target_variant": reference_set.target_variant,
        "reference_count": len(reference_set.items),
        "matching_reference_count": len(matching),
        "independent_source_count": len(source_ids),
        "view_count": len(views),
        "checks": checks,
        "covered_properties": covered_properties,
        "dimensional_anchors": anchors,
        "issues": issues,
        "targeted_research_queries": list(dict.fromkeys(queries)),
        "pass": ready,
        "disposition": "READY_TO_MODEL" if ready else "TARGETED_RESEARCH",
    }


def reference_set_from_dict(payload: dict[str, Any]) -> ReferenceSet:
    """Load the documented JSON manifest shape without weakening validation."""
    items = []
    for raw in payload.get("items", []):
        claims = tuple(PropertyClaim(**claim) for claim in raw.get("claims", []))
        item = {**raw, "claims": claims}
        for key in ("purposes", "dimensional_anchors", "limitations"):
            item[key] = tuple(item.get(key, []))
        items.append(ReferenceItem(**item))
    conflicts = []
    for raw in payload.get("conflicts", []):
        conflicts.append(ReferenceConflict(**{**raw, "reference_ids": tuple(raw.get("reference_ids", []))}))
    return ReferenceSet(
        **{
            **payload,
            "items": tuple(items),
            "required_views": tuple(payload.get("required_views", [])),
            "critical_properties": tuple(payload.get("critical_properties", [])),
            "orthographic_required_views": tuple(payload.get("orthographic_required_views", [])),
            "conflicts": tuple(conflicts),
        }
    )


def reference_set_to_dict(reference_set: ReferenceSet) -> dict[str, Any]:
    return asdict(reference_set)


def build_reference_stage_evidence(
    audit: dict[str, Any], *, component_graph_pass: bool,
    measured_ratio_count: int, uncertainty_recorded: bool,
) -> dict[str, Any]:
    """Map one audit into the exact machine gate contract without hand-copied flags."""
    checks = audit.get("checks", {})
    return {
        "component_graph_pass": component_graph_pass,
        "measured_ratio_count": measured_ratio_count,
        "uncertainty_recorded": uncertainty_recorded,
        "reference_set_audit_pass": bool(audit.get("pass")),
        "same_target_identity_pass": bool(checks.get("same_target_identity_pass")),
        "view_coverage_pass": bool(checks.get("view_coverage_pass")) and bool(checks.get("orthographic_coverage_pass")),
        "critical_property_coverage_pass": bool(checks.get("critical_property_coverage_pass")),
        "conflicts_resolved_pass": bool(checks.get("conflicts_resolved_pass")),
        "targeted_research_queries": list(audit.get("targeted_research_queries", [])),
        "reference_audit": audit,
    }
