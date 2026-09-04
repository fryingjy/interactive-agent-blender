"""Structured readiness checks for reference-driven modeling.

The audit measures information coverage, not image count.  It deliberately keeps
view diversity, provenance diversity, target identity, and evidentiary purpose as
separate concepts.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


FACTUAL_PURPOSES = {
    "PRIMARY_FORM", "ORTHOGRAPHIC", "DETAIL", "CONSTRUCTION", "DIMENSION",
    "FUNCTIONAL", "MATERIAL", "CONTEXT",
}
VALID_PROJECTIONS = {"ORTHOGRAPHIC", "PERSPECTIVE", "UNKNOWN"}
VALID_SOURCE_TIERS = {"VERY_HIGH", "HIGH", "USEFUL_VERIFY", "INSPIRATION"}
AUTHORITATIVE_CONFIDENCE = {"MEDIUM", "HIGH"}
VALID_RESEARCH_IMPACTS = {"LOW", "MEDIUM", "HIGH"}
VALID_RESEARCH_STATUSES = {"OPEN", "RESOLVED", "DEFERRED"}
VALID_CANDIDATE_DISPOSITIONS = {"ACCEPTED", "REJECTED", "PENDING"}
VALID_GEOMETRY_SCOPES = {"FULL_OBJECT", "OCCLUDED_OBJECT", "PARTIAL_OBJECT", "COMPONENT_DETAIL"}


@dataclass(frozen=True)
class PropertyClaim:
    property_id: str
    purpose: str
    observation: str
    confidence: str = "MEDIUM"
    # Which declared component (from the scene-decomposition component graph)
    # this specific claim documents. Optional/defaulted so existing claims
    # and callers stay valid; see validate_component_reference_coverage below
    # for what actually consumes it.
    component_id: str = ""

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
    # Optional provenance is retained with the evidence record rather than
    # forcing callers to strip it before validation.  It does not change the
    # factual-readiness criteria, but makes a validated manifest reproducible.
    source_url: str = ""
    local_file: str = ""
    local_sha256: str = ""
    claims: tuple[PropertyClaim, ...] = ()
    dimensional_anchors: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    # Which declared components (from the scene-decomposition component
    # graph) this reference image/item documents overall -- one photo commonly
    # shows several components at once. Optional/defaulted; see
    # validate_component_reference_coverage below.
    component_ids: tuple[str, ...] = ()
    geometry_scope: str = "FULL_OBJECT"
    viewpoint_family: str = ""
    occlusion_fraction: float = 0.0
    identity_markers: tuple[str, ...] = ()

    def validate(self) -> None:
        if not all((self.reference_id, self.source_id, self.target_id, self.target_variant)):
            raise ValueError("reference identity and provenance fields are required")
        if not self.view:
            raise ValueError("reference view is required")
        if self.projection not in VALID_PROJECTIONS:
            raise ValueError(f"unknown projection: {self.projection}")
        if self.source_tier not in VALID_SOURCE_TIERS:
            raise ValueError(f"unknown source tier: {self.source_tier}")
        if self.geometry_scope not in VALID_GEOMETRY_SCOPES:
            raise ValueError(f"unknown geometry scope: {self.geometry_scope}")
        if isinstance(self.occlusion_fraction, bool) or not 0.0 <= float(self.occlusion_fraction) <= 1.0:
            raise ValueError("reference occlusion_fraction must be in [0, 1]")
        if self.geometry_scope == "FULL_OBJECT" and self.occlusion_fraction > 0.05:
            raise ValueError("FULL_OBJECT references cannot declare material occlusion")
        if any(not str(marker).strip() for marker in self.identity_markers):
            raise ValueError("identity markers must be non-empty strings")
        if not self.source_url and not self.local_file:
            raise ValueError("reference items require source_url or local_file provenance")
        if self.source_url:
            parsed = urlparse(self.source_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("reference source_url must be an absolute HTTP(S) URL")
        if self.local_file:
            path = Path(self.local_file)
            if not path.is_file():
                raise ValueError(f"reference local_file does not exist: {self.local_file}")
            if len(self.local_sha256) != 64:
                raise ValueError("materialized reference files require local_sha256")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest.lower() != self.local_sha256.lower():
                raise ValueError("reference local_sha256 does not match local_file")
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

    def validate(self) -> None:
        if not self.property_id or not self.reference_ids or not self.description:
            raise ValueError("reference conflicts require a property, references, and description")
        if self.status not in {"OPEN", "RESOLVED"}:
            raise ValueError(f"unknown conflict status: {self.status}")
        if self.status == "RESOLVED" and not self.resolution.strip():
            raise ValueError("resolved reference conflicts require a recorded resolution")


@dataclass(frozen=True)
class ResearchCandidate:
    """One inspected search result, including evidence that was rejected."""

    candidate_id: str
    source_url: str
    source_id: str
    observed_identity: str
    observed_variant: str
    purpose: str
    disposition: str
    reason: str
    accepted_reference_id: str = ""
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        if not all(
            (
                self.candidate_id,
                self.source_url,
                self.source_id,
                self.observed_identity,
                self.observed_variant,
                self.purpose,
                self.reason,
            )
        ):
            raise ValueError("research candidates require identity, provenance, purpose, and reason")
        if self.purpose not in FACTUAL_PURPOSES | {"INSPIRATION"}:
            raise ValueError(f"unknown research-candidate purpose: {self.purpose}")
        if self.disposition not in VALID_CANDIDATE_DISPOSITIONS:
            raise ValueError(f"unknown candidate disposition: {self.disposition}")
        if self.disposition == "ACCEPTED" and not self.accepted_reference_id:
            raise ValueError("accepted research candidates must link to a reference item")
        if self.disposition != "ACCEPTED" and self.accepted_reference_id:
            raise ValueError("only accepted candidates may link to a reference item")


@dataclass(frozen=True)
class ReferenceResearchQuestion:
    """Question-driven search history tied to one uncertain target property."""

    question_id: str
    property_id: str
    question: str
    trigger: str
    impact: str
    search_queries: tuple[str, ...]
    candidates: tuple[ResearchCandidate, ...]
    status: str = "OPEN"
    resolution: str = ""
    modeling_constraint: str = ""

    def validate(self) -> None:
        if not all((self.question_id, self.property_id, self.question, self.trigger)):
            raise ValueError("reference research questions require identity, property, question, and trigger")
        if self.impact not in VALID_RESEARCH_IMPACTS:
            raise ValueError(f"unknown research-question impact: {self.impact}")
        if self.status not in VALID_RESEARCH_STATUSES:
            raise ValueError(f"unknown research-question status: {self.status}")
        queries = [query.strip() for query in self.search_queries]
        if not queries or any(not query for query in queries):
            raise ValueError("reference research questions require at least one non-empty search query")
        if len(set(queries)) != len(queries):
            raise ValueError("reference research search queries must be unique per question")
        for candidate in self.candidates:
            candidate.validate()
        candidate_ids = [candidate.candidate_id for candidate in self.candidates]
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("research candidate IDs must be unique per question")
        accepted = [candidate for candidate in self.candidates if candidate.disposition == "ACCEPTED"]
        if self.status == "RESOLVED" and (not self.resolution.strip() or not accepted):
            raise ValueError("resolved research questions require a resolution and accepted evidence")
        if self.status == "DEFERRED" and (
            not self.resolution.strip() or not self.modeling_constraint.strip() or not self.candidates
        ):
            raise ValueError(
                "deferred research questions require attempted candidates, a reason, and a modeling constraint"
            )


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
    minimum_full_object_geometry_views: int = 1
    minimum_distinct_viewpoint_families: int = 1
    conflicts: tuple[ReferenceConflict, ...] = ()
    research_questions: tuple[ReferenceResearchQuestion, ...] = ()


def audit_reference_research(
    questions: tuple[ReferenceResearchQuestion, ...], reference_ids: set[str]
) -> dict[str, Any]:
    """Audit whether uncertainty led to traceable searches and bounded decisions."""
    question_ids = [question.question_id for question in questions]
    if len(set(question_ids)) != len(question_ids):
        raise ValueError("reference research question IDs must be unique")
    missing_reference_links: list[str] = []
    accepted_reference_links: list[str] = []
    open_questions: list[str] = []
    blocking_questions: list[str] = []
    deferred_questions: list[str] = []
    modeling_constraints: list[str] = []
    targeted_queries: list[str] = []
    candidate_counts = {"ACCEPTED": 0, "REJECTED": 0, "PENDING": 0}

    for question in questions:
        question.validate()
        for candidate in question.candidates:
            candidate_counts[candidate.disposition] += 1
            if candidate.disposition == "ACCEPTED":
                accepted_reference_links.append(candidate.accepted_reference_id)
                if candidate.accepted_reference_id not in reference_ids:
                    missing_reference_links.append(
                        f"{question.question_id}:{candidate.accepted_reference_id}"
                    )
        if question.status == "OPEN":
            open_questions.append(question.question_id)
            targeted_queries.extend(question.search_queries)
            if question.impact == "HIGH":
                blocking_questions.append(question.question_id)
        elif question.status == "DEFERRED":
            deferred_questions.append(question.question_id)
            modeling_constraints.append(question.modeling_constraint)

    checks = {
        "question_records_valid": True,
        "accepted_candidates_link_to_reference_items": not missing_reference_links,
        "no_high_impact_question_open": not blocking_questions,
    }
    return {
        "question_count": len(questions),
        "candidate_counts": candidate_counts,
        "accepted_reference_links": sorted(set(accepted_reference_links)),
        "missing_reference_links": missing_reference_links,
        "open_questions": open_questions,
        "blocking_questions": blocking_questions,
        "deferred_questions": deferred_questions,
        "modeling_constraints": modeling_constraints,
        "targeted_research_queries": list(dict.fromkeys(targeted_queries)),
        "checks": checks,
        "pass": all(checks.values()),
    }


def audit_reference_set(reference_set: ReferenceSet) -> dict[str, Any]:
    """Return a deterministic, JSON-safe readiness decision and research prompts."""
    if not reference_set.target_id or not reference_set.target_variant:
        raise ValueError("target_id and target_variant are required")
    if reference_set.minimum_independent_sources < 1:
        raise ValueError("minimum_independent_sources must be positive")
    if reference_set.minimum_full_object_geometry_views < 1:
        raise ValueError("minimum_full_object_geometry_views must be positive")
    if reference_set.minimum_distinct_viewpoint_families < 1:
        raise ValueError("minimum_distinct_viewpoint_families must be positive")
    for item in reference_set.items:
        item.validate()
    reference_ids = [item.reference_id for item in reference_set.items]
    if len(set(reference_ids)) != len(reference_ids):
        raise ValueError("reference_id values must be unique")
    for conflict in reference_set.conflicts:
        conflict.validate()

    research_audit = audit_reference_research(
        reference_set.research_questions, set(reference_ids)
    )

    issues: list[str] = []
    queries: list[str] = []
    matching = [
        item for item in reference_set.items
        if item.target_id == reference_set.target_id
        and item.target_variant == reference_set.target_variant
    ]
    artifact_hashes = sorted({
        item.local_sha256.lower() for item in matching if item.local_file and item.local_sha256
    })
    if not artifact_hashes:
        issues.append("no materialized reference artifact is hash-bound")
    mismatched = [
        item.reference_id for item in reference_set.items
        if item.target_id != reference_set.target_id
        or item.target_variant != reference_set.target_variant
    ]
    if mismatched:
        issues.append(f"mixed target identity or variant: {', '.join(mismatched)}")

    views = {item.view.lower() for item in matching}
    full_object_items = [item for item in matching if item.geometry_scope == "FULL_OBJECT"]
    viewpoint_families = {
        (item.viewpoint_family or item.view).strip().lower()
        for item in full_object_items
    }
    if len(full_object_items) < reference_set.minimum_full_object_geometry_views:
        issues.append(
            f"only {len(full_object_items)} full-object geometry view(s); "
            f"{reference_set.minimum_full_object_geometry_views} required"
        )
        queries.append(f"{reference_set.target_id} {reference_set.target_variant} complete unobscured product view")
    if len(viewpoint_families) < reference_set.minimum_distinct_viewpoint_families:
        issues.append(
            f"only {len(viewpoint_families)} distinct full-object viewpoint family/families; "
            f"{reference_set.minimum_distinct_viewpoint_families} required"
        )
        queries.append(f"{reference_set.target_id} {reference_set.target_variant} opposite side rear oblique view")
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
    low_authority_claims: list[str] = []
    for item in matching:
        for claim in item.claims:
            if claim.purpose not in item.purposes or claim.purpose == "INSPIRATION":
                invalid_claims.append(f"{item.reference_id}:{claim.property_id}")
                continue
            if item.source_tier == "INSPIRATION" or claim.confidence not in AUTHORITATIVE_CONFIDENCE:
                low_authority_claims.append(f"{item.reference_id}:{claim.property_id}")
                continue
            covered_properties.setdefault(claim.property_id, []).append(item.reference_id)
    if invalid_claims:
        issues.append("claims lack matching factual purpose: " + ", ".join(invalid_claims))
    if low_authority_claims:
        issues.append(
            "claims are too weak to establish authoritative properties: "
            + ", ".join(low_authority_claims)
        )

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
    queries.extend(research_audit["targeted_research_queries"])
    if research_audit["missing_reference_links"]:
        issues.append(
            "accepted research candidates lack matching reference items: "
            + ", ".join(research_audit["missing_reference_links"])
        )
    for question_id in research_audit["blocking_questions"]:
        issues.append(f"high-impact research question remains open: {question_id}")

    checks = {
        "same_target_identity_pass": not mismatched and bool(matching),
        "view_coverage_pass": not missing_views,
        "full_object_geometry_coverage_pass": (
            len(full_object_items) >= reference_set.minimum_full_object_geometry_views
        ),
        "viewpoint_diversity_pass": (
            len(viewpoint_families) >= reference_set.minimum_distinct_viewpoint_families
        ),
        "orthographic_coverage_pass": not missing_ortho,
        "provenance_coverage_pass": len(source_ids) >= reference_set.minimum_independent_sources,
        "critical_property_coverage_pass": (
            not missing_properties and not invalid_claims and not low_authority_claims
        ),
        "dimensional_anchor_pass": bool(anchors) or not reference_set.require_dimensional_anchor,
        "conflicts_resolved_pass": not open_conflicts,
        "question_driven_research_pass": research_audit["pass"],
        "artifact_binding_pass": bool(artifact_hashes),
    }
    ready = all(checks.values())
    return {
        "schema_version": 1,
        "record_type": "REFERENCE_SET_AUDIT",
        "target_id": reference_set.target_id,
        "target_variant": reference_set.target_variant,
        "reference_count": len(reference_set.items),
        "matching_reference_count": len(matching),
        "independent_source_count": len(source_ids),
        "view_count": len(views),
        "full_object_geometry_view_count": len(full_object_items),
        "distinct_viewpoint_families": sorted(viewpoint_families),
        "checks": checks,
        "covered_properties": covered_properties,
        "dimensional_anchors": anchors,
        "authorized_reference_sha256": artifact_hashes,
        "issues": issues,
        "targeted_research_queries": list(dict.fromkeys(queries)),
        "research_audit": research_audit,
        "pass": ready,
        "disposition": "READY_TO_MODEL" if ready else "TARGETED_RESEARCH",
    }


def reference_set_from_dict(payload: dict[str, Any], *, base_dir: str | Path | None = None) -> ReferenceSet:
    """Load the documented JSON manifest shape without weakening validation."""
    items = []
    for raw in payload.get("items", []):
        claims = tuple(PropertyClaim(**claim) for claim in raw.get("claims", []))
        item = {**raw, "claims": claims}
        if item.get("local_file") and base_dir is not None:
            local_path = Path(item["local_file"])
            if not local_path.is_absolute():
                item["local_file"] = str((Path(base_dir) / local_path).resolve())
        for key in ("purposes", "dimensional_anchors", "limitations", "component_ids", "identity_markers"):
            item[key] = tuple(item.get(key, []))
        items.append(ReferenceItem(**item))
    conflicts = []
    for raw in payload.get("conflicts", []):
        conflicts.append(ReferenceConflict(**{**raw, "reference_ids": tuple(raw.get("reference_ids", []))}))
    research_questions = []
    for raw in payload.get("research_questions", []):
        candidates = []
        for candidate in raw.get("candidates", []):
            candidates.append(
                ResearchCandidate(
                    **{**candidate, "limitations": tuple(candidate.get("limitations", []))}
                )
            )
        research_questions.append(
            ReferenceResearchQuestion(
                **{
                    **raw,
                    "search_queries": tuple(raw.get("search_queries", [])),
                    "candidates": tuple(candidates),
                }
            )
        )
    return ReferenceSet(
        **{
            **payload,
            "items": tuple(items),
            "required_views": tuple(payload.get("required_views", [])),
            "critical_properties": tuple(payload.get("critical_properties", [])),
            "orthographic_required_views": tuple(payload.get("orthographic_required_views", [])),
            "conflicts": tuple(conflicts),
            "research_questions": tuple(research_questions),
        }
    )


def reference_set_to_dict(reference_set: ReferenceSet) -> dict[str, Any]:
    return asdict(reference_set)


def validate_component_reference_coverage(
    components: list[dict[str, Any]], items: tuple[ReferenceItem, ...]
) -> dict[str, Any]:
    """Prove reference evidence covers each declared component individually, not just globally.

    `knowledge_engine.reasoning.validate_component_graph` proves the declared component
    list/relationship graph is internally well-formed; it says nothing about whether reference
    evidence actually documents any specific component. This is the analogous *evidence-coverage*
    check -- the reference-side counterpart to how `stage_gates._component_coverage_is_valid`
    already checks *built-geometry* coverage against the same declared components.
    """
    declared = {item.get("id") for item in components if item.get("id")}
    covered: set[str] = set()
    for item in items:
        covered.update(item.component_ids)
        for claim in item.claims:
            if claim.component_id:
                covered.add(claim.component_id)
    uncovered = sorted(declared - covered)
    return {
        "schema_version": 1,
        "record_type": "COMPONENT_REFERENCE_COVERAGE",
        "component_count": len(declared),
        "covered_component_ids": sorted(covered & declared),
        "uncovered_component_ids": uncovered,
        "pass": not uncovered,
    }


def validate_depth_critical_reference_support(
    components: list[dict[str, Any]], items: tuple[ReferenceItem, ...]
) -> dict[str, Any]:
    """Require more than one observed view for every depth-critical component.

    A front image can cover a component while still providing no evidence for its thickness,
    layering, attachment depth, or rear construction. Components opt into this stricter check with
    ``depth_critical: true`` in the decomposition. Evidence counts only when the reference or one
    of its factual claims is explicitly assigned to that component; inspiration-only material does
    not satisfy the gate.
    """
    critical_ids = {
        component.get("id") for component in components
        if component.get("id") and component.get("depth_critical") is True
    }
    views_by_component: dict[str, set[str]] = {component_id: set() for component_id in critical_ids}
    references_by_component: dict[str, set[str]] = {component_id: set() for component_id in critical_ids}
    for item in items:
        factual_item = bool(set(item.purposes) & FACTUAL_PURPOSES)
        assigned = set(item.component_ids) if factual_item else set()
        assigned.update(
            claim.component_id for claim in item.claims
            if claim.component_id and claim.purpose in FACTUAL_PURPOSES
        )
        for component_id in critical_ids & assigned:
            views_by_component[component_id].add(item.view.strip().lower())
            references_by_component[component_id].add(item.reference_id)
    reports = {
        component_id: {
            "view_ids": sorted(views_by_component[component_id]),
            "reference_ids": sorted(references_by_component[component_id]),
            "view_count": len(views_by_component[component_id]),
            "pass": len(views_by_component[component_id]) >= 2,
        }
        for component_id in sorted(critical_ids)
    }
    unsupported = [component_id for component_id, report in reports.items() if not report["pass"]]
    return {
        "schema_version": 1,
        "record_type": "DEPTH_CRITICAL_REFERENCE_SUPPORT",
        "depth_critical_component_ids": sorted(critical_ids),
        "component_reports": reports,
        "unsupported_component_ids": unsupported,
        "pass": not unsupported,
    }


def build_reference_stage_evidence(
    audit: dict[str, Any], *, component_graph_pass: bool,
    measured_ratio_count: int, uncertainty_recorded: bool,
    visual_reconstruction_audit: dict[str, Any] | None = None,
    component_reference_coverage: dict[str, Any] | None = None,
    depth_critical_reference_support: dict[str, Any] | None = None,
    modeling_spec_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map one audit into the exact machine gate contract without hand-copied flags.

    ``visual_reconstruction_audit`` and ``component_reference_coverage`` are the real structured
    results of ``visual_reconstruction.audit_visual_reconstruction(...)`` and
    ``validate_component_reference_coverage(...)`` respectively -- pass the dict itself, not a
    bare boolean, so `blender_ops.stage_gates` can keep checking actual structure rather than a
    self-reported flag. Left as ``None`` only for callers not yet producing that evidence; the
    REFERENCE_ANALYSIS gate will then correctly fail on them rather than silently pass.
    """
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
        "question_driven_research_pass": bool(checks.get("question_driven_research_pass")),
        "visual_reconstruction_audit_pass": visual_reconstruction_audit,
        "component_reference_coverage_pass": component_reference_coverage,
        "depth_critical_reference_support_pass": depth_critical_reference_support,
        "modeling_spec_audit": modeling_spec_audit,
        "targeted_research_queries": list(audit.get("targeted_research_queries", [])),
        "modeling_constraints": list(
            audit.get("research_audit", {}).get("modeling_constraints", [])
        ),
        "reference_audit": audit,
    }
