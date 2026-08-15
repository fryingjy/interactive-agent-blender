"""Structured component/relationship decomposition of a reference object, produced
BEFORE modeling and checked AFTER, per docs/REFERENCE_COLLECTION_PROTOCOL.md's
"modeling brief before Blender" step and a user-directed critique (2026-08-13):

    SYSTEM: "I have a good silhouette."
    HUMAN:  "You didn't actually model the wrench."

A silhouette/topology pass can be clean while the object was reduced to one
decorative blob instead of its real parts -- exactly what happened to the
adjustable wrench (see knowledge/foundation/operator_cards/visual_reference_comparison.md).
This module makes the "what are the real components and how do they relate"
step an explicit, structured, checkable record instead of only prose in a
markdown brief, so a build can be checked against it mechanically, not just
read by eye.

Deliberately small and dependency-free, matching this project's own existing
knowledge_engine/schemas.py convention -- this is a decomposition record and a
coverage check, not a new inference engine.

CORRECTION (found live building this): `knowledge_engine/reasoning.py` already
has `validate_component_graph()` (duplicate/missing-id and dangling-relationship
checks) -- but it is called from nowhere except its own unit test, exactly the
"documented architecture, not yet operationalized" pattern the user's critique
named directly. Rather than write a second, slightly different graph validator,
`SceneDecomposition.validate()` below delegates the graph-shape check to the
existing function and only adds what genuinely doesn't exist yet: a typed
component/relationship vocabulary (role, manufacture, relationship type) and
`check_object_coverage()`, the actual anti-wrench mechanism.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from knowledge_engine.reasoning import validate_component_graph

VALID_ROLES = {"primary", "secondary", "tertiary"}
VALID_MANUFACTURE = {"structural", "cosmetic", "unknown"}
VALID_RELATIONSHIP_TYPES = {
    "attached_to",
    "aligned_with",
    "slides_relative_to",
    "rotates_relative_to",
    "rests_on",
    "transitions_into",
    "occupies_surface_of",
    "interacts_with",
    "fastens_to",
    "hangs_from",
    "inset_into",
    "mirrors",
    "nested_inside",
    "overlaps",
    "repeats_along",
    "separated_from",
}

EVIDENCE_STATES = {"OBSERVED", "STRONGLY_INFERRED", "WEAKLY_INFERRED", "UNKNOWN"}
REFERENCE_STYLES = {"photo", "concept", "orthographic", "stylized", "mixed"}
CLAIM_CATEGORIES = (
    "camera_assumptions",
    "primary_forms",
    "secondary_forms",
    "tertiary_forms",
    "continuous_surfaces",
    "separate_parts",
    "negative_spaces",
    "landmarks",
    "symmetry",
    "repetition",
    "thickness_hypotheses",
    "depth_order",
    "overlap",
    "material_boundaries",
    "construction_hypotheses",
    "known_dimensions",
    "estimated_dimensions",
    "unknowns",
    "ambiguities",
)
MODELING_SIGNAL_FIELDS = {
    "smooth_continuous_surface",
    "repeated_elements",
    "symmetric",
    "follows_path",
    "deformation_expected",
    "watertight_union_required",
    "independent_motion_or_material",
}


def _validate_evidence_binding(label: str, status: str, confidence: float, evidence: list[str]) -> None:
    if status not in EVIDENCE_STATES:
        raise ValueError(f"invalid evidence status '{status}' for {label}")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence for {label} must be between 0 and 1")
    if status in {"OBSERVED", "STRONGLY_INFERRED"} and not any(item.strip() for item in evidence):
        raise ValueError(f"{status} claim '{label}' requires concrete evidence")
    if status == "OBSERVED" and confidence < 0.65:
        raise ValueError(f"OBSERVED claim '{label}' must have confidence >= 0.65")
    if status == "STRONGLY_INFERRED" and confidence < 0.5:
        raise ValueError(f"STRONGLY_INFERRED claim '{label}' must have confidence >= 0.5")
    if status == "UNKNOWN" and confidence > 0.25:
        raise ValueError(f"UNKNOWN claim '{label}' cannot have confidence > 0.25")


@dataclass
class ReferenceClaim:
    claim_id: str
    category: str
    statement: str
    evidence_status: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    modeling_consequence: str = ""
    impact: str = "medium"  # low / medium / high if wrong
    component_refs: list[str] = field(default_factory=list)
    source_views: list[str] = field(default_factory=list)
    modeling_signals: dict[str, bool] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.claim_id.strip() or not self.statement.strip():
            raise ValueError("reference claim id and statement are required")
        if self.category not in CLAIM_CATEGORIES:
            raise ValueError(f"invalid reference claim category '{self.category}'")
        if self.impact not in {"low", "medium", "high"}:
            raise ValueError(f"invalid impact '{self.impact}' for claim '{self.claim_id}'")
        _validate_evidence_binding(self.claim_id, self.evidence_status, self.confidence, self.evidence)
        unknown_signals = set(self.modeling_signals) - MODELING_SIGNAL_FIELDS
        if unknown_signals:
            raise ValueError(f"unknown modeling signals for '{self.claim_id}': {sorted(unknown_signals)}")
        if self.impact == "high" and self.evidence_status != "UNKNOWN" and not self.modeling_consequence.strip():
            raise ValueError(f"high-impact claim '{self.claim_id}' requires a modeling consequence")


@dataclass
class StrategyCandidate:
    name: str
    representation: str
    rationale_claim_ids: list[str]
    status: str = "candidate"  # candidate / rejected
    rejection_reason: str = ""
    reversible: bool = True

    def validate(self, claim_ids: set[str]) -> None:
        if not self.name.strip() or not self.representation.strip():
            raise ValueError("strategy name and representation are required")
        if self.status not in {"candidate", "rejected"}:
            raise ValueError(f"invalid strategy status '{self.status}'")
        if not self.rationale_claim_ids:
            raise ValueError(f"strategy '{self.name}' requires at least one evidence-bound rationale claim")
        missing = sorted(set(self.rationale_claim_ids) - claim_ids)
        if missing:
            raise ValueError(f"strategy '{self.name}' references missing claims: {missing}")
        if self.status == "rejected" and not self.rejection_reason.strip():
            raise ValueError(f"rejected strategy '{self.name}' requires a reason")


@dataclass
class Component:
    name: str
    role: str  # primary / secondary / tertiary, per the reference protocol's own form hierarchy
    manufacture: str = "unknown"  # structural / cosmetic / unknown
    separately_manufactured: bool | None = None  # None = not yet determined from reference
    notes: str = ""
    evidence_status: str = "UNKNOWN"
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("component name is required")
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role '{self.role}' for component '{self.name}'")
        if self.manufacture not in VALID_MANUFACTURE:
            raise ValueError(f"invalid manufacture '{self.manufacture}' for component '{self.name}'")
        _validate_evidence_binding(self.name, self.evidence_status, self.confidence, self.evidence)


@dataclass
class Relationship:
    from_component: str
    to_component: str
    type: str
    notes: str = ""
    evidence_status: str = "UNKNOWN"
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)

    def validate_type(self) -> None:
        if self.type not in VALID_RELATIONSHIP_TYPES:
            raise ValueError(f"invalid relationship type '{self.type}'")
        _validate_evidence_binding(
            f"{self.from_component}->{self.to_component}:{self.type}",
            self.evidence_status,
            self.confidence,
            self.evidence,
        )


@dataclass
class SceneDecomposition:
    object_name: str
    components: list[Component] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    object_class: str = "unknown"
    reference_style: str = "mixed"
    claims: list[ReferenceClaim] = field(default_factory=list)
    strategies: list[StrategyCandidate] = field(default_factory=list)
    require_evidence_bindings: bool = False

    def validate(self) -> None:
        if not self.object_name.strip():
            raise ValueError("object_name is required")
        if not self.components:
            raise ValueError("at least one component is required -- an empty decomposition is not a decomposition")
        if self.reference_style not in REFERENCE_STYLES:
            raise ValueError(f"invalid reference style '{self.reference_style}'")
        for c in self.components:
            c.validate()
        for r in self.relationships:
            r.validate_type()

        # Graph-shape validity (duplicate/missing ids, dangling relationship
        # endpoints) is not re-implemented here -- delegated to the existing
        # knowledge_engine/reasoning.py check so there is one graph validator
        # in the project, not two.
        graph_result = validate_component_graph(
            components=[{"id": c.name} for c in self.components],
            relationships=[{"from": r.from_component, "to": r.to_component} for r in self.relationships],
        )
        if not graph_result["pass"]:
            raise ValueError(f"component graph invalid: {graph_result}")

        claim_ids = [claim.claim_id for claim in self.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("reference claim ids must be unique")
        component_names = {component.name for component in self.components}
        for claim in self.claims:
            claim.validate()
            missing_components = sorted(set(claim.component_refs) - component_names)
            if missing_components:
                raise ValueError(f"claim '{claim.claim_id}' references missing components: {missing_components}")
        for strategy in self.strategies:
            strategy.validate(set(claim_ids))
        if self.require_evidence_bindings:
            if not self.claims:
                raise ValueError("strict reference decomposition requires typed reference claims")
            unsupported_primaries = [
                component.name
                for component in self.primary_components()
                if component.evidence_status not in {"OBSERVED", "STRONGLY_INFERRED"}
            ]
            if unsupported_primaries:
                raise ValueError(
                    "strict reference decomposition requires evidence-bound primary components: "
                    f"{unsupported_primaries}"
                )
            if not any(strategy.status == "candidate" for strategy in self.strategies):
                raise ValueError("strict reference decomposition requires a candidate modeling strategy")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        grouped = {category: [] for category in CLAIM_CATEGORIES}
        for claim in self.claims:
            grouped[claim.category].append(asdict(claim))
        result = {
            "target": self.object_name,
            "object_name": self.object_name,
            "object_class": self.object_class,
            "reference_style": self.reference_style,
            "camera_assumptions": {item["claim_id"]: item for item in grouped.pop("camera_assumptions")},
            "components": [asdict(c) for c in self.components],
            "relationships": [asdict(r) for r in self.relationships],
            "confidence_by_claim": {claim.claim_id: claim.confidence for claim in self.claims},
            "candidate_modeling_strategies": [asdict(item) for item in self.strategies if item.status == "candidate"],
            "rejected_strategies": [asdict(item) for item in self.strategies if item.status == "rejected"],
            "reference_readiness": self.blockout_readiness(),
        }
        for category, items in grouped.items():
            result[category] = {"claims": items} if category == "symmetry" else items
        return result

    def blockout_readiness(self) -> dict[str, Any]:
        """Determine whether interpretation is strong enough to risk a blockout.

        This is intentionally stricter than graph validity.  A plausible component
        list is not enough when primary form, construction, or strategy is unknown.
        """
        categories = {category: [] for category in CLAIM_CATEGORIES}
        for claim in self.claims:
            categories[claim.category].append(claim)
        missing = []
        if not any(item.evidence_status in {"OBSERVED", "STRONGLY_INFERRED"} for item in categories["primary_forms"]):
            missing.append("primary_forms")
        if not any(component.role == "primary" and component.evidence_status in {"OBSERVED", "STRONGLY_INFERRED"} for component in self.components):
            missing.append("evidence_bound_primary_components")
        if not any(item.evidence_status in {"OBSERVED", "STRONGLY_INFERRED"} for item in categories["construction_hypotheses"]):
            missing.append("construction_hypotheses")
        if not any(item.status == "candidate" for item in self.strategies):
            missing.append("candidate_modeling_strategy")
        unresolved = [
            claim
            for claim in self.claims
            if claim.impact == "high" and claim.evidence_status in {"WEAKLY_INFERRED", "UNKNOWN"}
        ]
        supported_signal_values: dict[str, set[bool]] = {}
        for claim in self.claims:
            if claim.evidence_status not in {"OBSERVED", "STRONGLY_INFERRED"}:
                continue
            for key, value in claim.modeling_signals.items():
                supported_signal_values.setdefault(key, set()).add(bool(value))
        conflicting_signals = sorted(
            key for key, values in supported_signal_values.items() if len(values) > 1
        )
        return {
            "ready_for_blockout": not missing and not unresolved and not conflicting_signals,
            "missing_requirements": missing,
            "high_impact_unresolved_claims": [claim.claim_id for claim in unresolved],
            "research_questions": [claim.statement for claim in unresolved],
            "conflicting_modeling_signals": conflicting_signals,
            "claim_counts_by_status": {
                status: sum(claim.evidence_status == status for claim in self.claims)
                for status in sorted(EVIDENCE_STATES)
            },
        }

    def to_modeling_brief(self, base=None):
        """Translate evidence-bound claims into the existing strategy input.

        Weak/unknown claims never harden into strategy booleans.  This is the
        operational bridge from reference interpretation to modeling choice.
        """
        from knowledge_engine.strategy import ModelingBrief

        values = asdict(base) if base is not None else asdict(ModelingBrief())
        notes = list(values.pop("notes", ()))
        signal_claims: dict[str, list[tuple[str, bool]]] = {}
        for claim in self.claims:
            if claim.evidence_status not in {"OBSERVED", "STRONGLY_INFERRED"}:
                continue
            for key, value in claim.modeling_signals.items():
                signal_claims.setdefault(key, []).append((claim.claim_id, bool(value)))
            if claim.modeling_consequence:
                notes.append(f"{claim.claim_id}: {claim.modeling_consequence}")
        for key, bindings in signal_claims.items():
            distinct = {value for _, value in bindings}
            if len(distinct) > 1:
                claim_ids = [claim_id for claim_id, _ in bindings]
                raise ValueError(
                    f"conflicting evidence-bound modeling signal '{key}' from claims {claim_ids}"
                )
            values[key] = bindings[0][1]
        if any(component.separately_manufactured is True and component.evidence_status in {"OBSERVED", "STRONGLY_INFERRED"} for component in self.components):
            values["independent_motion_or_material"] = True
        values["notes"] = tuple(dict.fromkeys(notes))
        return ModelingBrief(**values)

    def primary_components(self) -> list[Component]:
        return [c for c in self.components if c.role == "primary"]

    def check_object_coverage(self, built_object_names: list[str]) -> dict[str, Any]:
        """The actual anti-wrench check: does the built scene have a plausible
        object for each PRIMARY component, or did construction collapse
        multiple declared primary components into fewer built objects (or one
        blob)? This does not by itself prove the geometry is correct -- a
        1:1 name-ish match is a necessary, not sufficient, condition -- but a
        primary component with no plausible match is a genuine, mechanically
        checkable red flag a pure silhouette/topology pass cannot catch.

        Matching is deliberately loose (substring, case-insensitive) since
        built object names won't exactly equal component names -- this is a
        coverage smell test, not an identity assertion.
        """
        self.validate()
        primaries = self.primary_components()
        built_lower = [b.lower() for b in built_object_names]
        unmatched = []
        for c in primaries:
            key_words = [w for w in c.name.lower().replace("-", " ").split() if len(w) > 2]
            matched = any(
                any(w in b for w in key_words) for b in built_lower
            )
            if not matched:
                unmatched.append(c.name)
        return {
            "declared_primary_components": [c.name for c in primaries],
            "built_object_names": built_object_names,
            "unmatched_primary_components": unmatched,
            "coverage_ok": not unmatched,
        }
