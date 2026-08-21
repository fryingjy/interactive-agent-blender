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
import re
from typing import Any

from knowledge_engine.reasoning import validate_component_graph

VALID_ROLES = {"primary", "secondary", "tertiary"}
VALID_MANUFACTURE = {"structural", "cosmetic", "unknown"}
_COVERAGE_GENERIC_TOKENS = {
    "back", "bottom", "component", "detail", "element", "front", "geometry",
    "geo", "left", "lower", "main", "mesh", "model", "object", "part",
    "piece", "primary", "right", "secondary", "shell", "surface", "tertiary",
    "top", "upper",
}
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
# These describe the representation of the *dominant continuous form*. A claim
# that only concerns a secondary component (for example, a curve-shaped carry
# handle) must not silently choose CURVE for the whole asset's primary cage.
PRIMARY_REPRESENTATION_SIGNALS = {
    "smooth_continuous_surface",
    "follows_path",
    "deformation_expected",
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
    # What this candidate PREDICTS should be observable in reference evidence
    # if it's correct -- e.g. {"view": "side_profile", "property": "roofline",
    # "prediction_type": "boundary_linearity", "prediction": "linear",
    # "testable_projection_types": ["ORTHOGRAPHIC"]}. Optional: older
    # candidates and most quick synthetic-only strategies won't have this.
    # Checked by knowledge_engine.representation_hypothesis, not here -- this
    # dataclass only carries the claim, it doesn't evaluate it (same
    # separation this module already keeps between claims and checks).
    predicted_consequences: list[dict] = field(default_factory=list)

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
        for consequence in self.predicted_consequences:
            required = {"view", "property", "prediction_type", "prediction"}
            missing_keys = required - set(consequence)
            if missing_keys:
                raise ValueError(
                    f"strategy '{self.name}' predicted_consequence missing keys: {sorted(missing_keys)}"
                )


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
    # Optional bounds measured from an aligned reference board.  Both entries use
    # scene-normalized coordinates in [0, 1] and an inclusive [minimum, maximum]
    # interval for x/y/z.  It stays optional: a single perspective photo must not
    # be laundered into fictional placement precision.
    expected_region: dict[str, dict[str, list[float]]] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("component name is required")
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role '{self.role}' for component '{self.name}'")
        if self.manufacture not in VALID_MANUFACTURE:
            raise ValueError(f"invalid manufacture '{self.manufacture}' for component '{self.name}'")
        _validate_evidence_binding(self.name, self.evidence_status, self.confidence, self.evidence)
        if not self.expected_region:
            return
        allowed = {"normalized_centroid", "normalized_size"}
        unknown = set(self.expected_region) - allowed
        if set(self.expected_region) != allowed:
            raise ValueError(f"invalid expected region keys for component '{self.name}': {sorted(unknown)}")
        for quantity, axes in self.expected_region.items():
            if not isinstance(axes, dict) or set(axes) != {"x", "y", "z"}:
                raise ValueError(
                    f"expected region '{quantity}' for component '{self.name}' must define x/y/z intervals"
                )
            for axis, interval in axes.items():
                if (
                    not isinstance(interval, list) or len(interval) != 2
                    or any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in interval)
                    or not 0.0 <= interval[0] <= interval[1] <= 1.0
                ):
                    raise ValueError(
                        f"expected region '{quantity}.{axis}' for component '{self.name}' must be a [0, 1] interval"
                    )


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
        primary_names = {component.name for component in self.primary_components()}
        signal_claims: dict[str, list[tuple[str, bool]]] = {}
        for claim in self.claims:
            if claim.evidence_status not in {"OBSERVED", "STRONGLY_INFERRED"}:
                continue
            for key, value in claim.modeling_signals.items():
                # An unscoped claim remains global.  A scoped primary-shape
                # signal, however, only affects the primary representation
                # when it is actually about a primary component.  Component
                # strategies remain available in the decomposition/contract
                # rather than being flattened into one asset-wide boolean.
                if (
                    key in PRIMARY_REPRESENTATION_SIGNALS
                    and claim.component_refs
                    and not (set(claim.component_refs) & primary_names)
                ):
                    continue
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

    def to_reference_to_blockout_contract(
        self,
        *,
        reference_set_id: str,
        selected_strategy_name: str | None = None,
    ) -> dict[str, Any]:
        """Emit the directive-required bridge from reference evidence to blockout.

        This is deliberately an interpretation artifact, not a blockout pass.  It
        preserves unknowns and rejected alternatives so a later Blender decision
        cannot quietly relabel a weak claim as construction truth.
        """
        self.validate()
        if not isinstance(reference_set_id, str) or not reference_set_id.strip():
            raise ValueError("reference_set_id is required for a reference-to-blockout contract")
        candidates = [strategy for strategy in self.strategies if strategy.status == "candidate"]
        if selected_strategy_name is None:
            if len(candidates) != 1:
                raise ValueError(
                    "selected_strategy_name is required when the decomposition has zero or multiple candidate strategies"
                )
            selected = candidates[0]
        else:
            selected = next((strategy for strategy in candidates if strategy.name == selected_strategy_name), None)
            if selected is None:
                raise ValueError("selected_strategy_name must name a candidate strategy")

        def claims(category: str) -> list[dict[str, Any]]:
            return [asdict(claim) for claim in self.claims if claim.category == category]

        supported = [
            asdict(claim) for claim in self.claims
            if claim.evidence_status in {"OBSERVED", "STRONGLY_INFERRED"}
        ]
        unresolved = [
            asdict(claim) for claim in self.claims
            if claim.evidence_status in {"WEAKLY_INFERRED", "UNKNOWN"}
        ]
        components = {component.name: asdict(component) for component in self.components}
        return {
            "schema_version": 1,
            "record_type": "REFERENCE_TO_BLOCKOUT_CONTRACT",
            "target": self.object_name,
            "reference_set_id": reference_set_id,
            "known": supported,
            "unknown": unresolved,
            "primary_forms": claims("primary_forms"),
            "primary_components": [components[component.name] for component in self.primary_components()],
            "secondary_components": [asdict(component) for component in self.components if component.role == "secondary"],
            "negative_spaces": claims("negative_spaces"),
            "silhouette_landmarks": claims("landmarks"),
            "depth_landmarks": claims("depth_order") + claims("overlap"),
            "symmetry": claims("symmetry"),
            "continuous_surface_hypotheses": claims("continuous_surfaces"),
            "separate_component_hypotheses": claims("separate_parts"),
            "dimensional_anchors": claims("known_dimensions") + claims("estimated_dimensions"),
            "candidate_strategies": [asdict(strategy) for strategy in candidates],
            "selected_strategy": asdict(selected),
            "rejected_strategies": [asdict(strategy) for strategy in self.strategies if strategy.status == "rejected"],
            "confidence": {
                "claims": {claim.claim_id: claim.confidence for claim in self.claims},
                "components": {component.name: component.confidence for component in self.components},
            },
            "reference_readiness": self.blockout_readiness(),
            "limitation": (
                "This contract makes reference interpretation and selected representation traceable. "
                "It does not authorize Blender construction until required external/human review gates pass."
            ),
        }

    def primary_components(self) -> list[Component]:
        return [c for c in self.components if c.role == "primary"]

    def has_primary_layout_expectations(self) -> bool:
        return any(component.expected_region for component in self.primary_components())

    def check_object_coverage(self, built_object_names: list[str]) -> dict[str, Any]:
        """The actual anti-wrench check: does the built scene have a plausible
        object for each PRIMARY component, or did construction collapse
        multiple declared primary components into fewer built objects (or one
        blob)? This does not by itself prove the geometry is correct -- a
        1:1 name-ish match is a necessary, not sufficient, condition -- but a
        primary component with no plausible match is a genuine, mechanically
        checkable red flag a pure silhouette/topology pass cannot catch.

        This is a name-based smoke detector, not geometric proof.  It uses
        meaningful name tokens and one-to-one maximum matching: a single
        ``Collector_Upper_Shell`` cannot silently count as both a collector
        and a ``Boiler_Lower_Shell`` just because both names contain "shell".
        Passing still does not establish that either component has the right
        proportions, construction, topology, or silhouette.
        """
        self.validate()
        primaries = self.primary_components()

        def tokens(name: str) -> set[str]:
            # Blender object names frequently use PascalCase while reference
            # boards use snake_case.  Split the former before case-folding so
            # `StageGateAsset` and `stage_gate_asset` express the same parts.
            spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
            return set(filter(None, re.split(r"[^a-z0-9]+", spaced.lower())))

        def normalized(name: str) -> str:
            return "_".join(sorted(tokens(name)))

        component_tokens = [tokens(component.name) for component in primaries]
        built_tokens = [tokens(name) for name in built_object_names]
        candidates: list[list[int]] = []
        for component, component_words in zip(primaries, component_tokens):
            meaningful_words = component_words - _COVERAGE_GENERIC_TOKENS
            exact_name = normalized(component.name)
            candidates.append([
                index
                for index, object_words in enumerate(built_tokens)
                if normalized(built_object_names[index]) == exact_name
                or bool(meaningful_words & (object_words - _COVERAGE_GENERIC_TOKENS))
            ])

        # Maximum bipartite matching rather than independent membership tests:
        # one built object may satisfy at most one declared primary component.
        object_to_component: dict[int, int] = {}

        def assign(component_index: int, visited: set[int]) -> bool:
            for object_index in candidates[component_index]:
                if object_index in visited:
                    continue
                visited.add(object_index)
                previous_component = object_to_component.get(object_index)
                if previous_component is None or assign(previous_component, visited):
                    object_to_component[object_index] = component_index
                    return True
            return False

        for component_index in sorted(range(len(primaries)), key=lambda index: len(candidates[index])):
            assign(component_index, set())

        component_to_object = {
            component_index: object_index
            for object_index, component_index in object_to_component.items()
        }
        unmatched = [
            component.name
            for component_index, component in enumerate(primaries)
            if component_index not in component_to_object
        ]
        return {
            "declared_primary_components": [c.name for c in primaries],
            "built_object_names": built_object_names,
            "component_matches": {
                primaries[component_index].name: built_object_names[object_index]
                for component_index, object_index in sorted(component_to_object.items())
            },
            "unmatched_primary_components": unmatched,
            "coverage_ok": not unmatched,
        }

    def check_component_layout(self, object_bounds: dict[str, dict[str, list[float]]]) -> dict[str, Any]:
        """Compare measured component bounds with optional reference-board regions.

        Names prove only presence.  This check adds coarse placement and proportion
        evidence in a target-independent coordinate frame: the union of the matched
        primary-component bounds.  It deliberately makes no shape or visual-fidelity
        claim, and returns ``not_applicable`` when the board did not provide an
        aligned expected region.
        """
        if not isinstance(object_bounds, dict):
            raise ValueError("object_bounds must map object names to min/max bounds")
        coverage = self.check_object_coverage(sorted(object_bounds))
        expected = {
            component.name: component.expected_region
            for component in self.primary_components()
            if component.expected_region
        }
        if not expected:
            return {
                "layout_expectations_present": False,
                "layout_ok": None,
                "status": "not_applicable",
                "component_reports": {},
                "limitation": "No aligned component regions were supplied by the reference board.",
            }

        matched_bounds: dict[str, tuple[list[float], list[float]]] = {}
        for component_name, object_name in coverage["component_matches"].items():
            raw = object_bounds.get(object_name)
            if not isinstance(raw, dict) or set(raw) != {"min", "max"}:
                raise ValueError(f"bounds for '{object_name}' must provide min/max vectors")
            lower, upper = raw["min"], raw["max"]
            if (
                not isinstance(lower, list) or not isinstance(upper, list)
                or len(lower) != 3 or len(upper) != 3
                or any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in lower + upper)
                or any(lower[index] > upper[index] for index in range(3))
            ):
                raise ValueError(f"invalid bounds for '{object_name}'")
            matched_bounds[component_name] = (lower, upper)

        all_lowers = [lower for lower, _ in matched_bounds.values()]
        all_uppers = [upper for _, upper in matched_bounds.values()]
        scene_min = [min(values[index] for values in all_lowers) for index in range(3)] if all_lowers else [0.0] * 3
        scene_max = [max(values[index] for values in all_uppers) for index in range(3)] if all_uppers else [0.0] * 3
        scene_span = [scene_max[index] - scene_min[index] for index in range(3)]
        axis_names = ("x", "y", "z")
        reports: dict[str, Any] = {}
        for component_name, region in expected.items():
            object_name = coverage["component_matches"].get(component_name)
            if object_name is None:
                reports[component_name] = {"object_name": None, "presence_ok": False, "placement_ok": False, "proportion_ok": False}
                continue
            lower, upper = matched_bounds[component_name]
            centroid = [(lower[index] + upper[index]) / 2.0 for index in range(3)]
            size = [upper[index] - lower[index] for index in range(3)]
            normalized_centroid = [
                (centroid[index] - scene_min[index]) / scene_span[index] if scene_span[index] else 0.5
                for index in range(3)
            ]
            normalized_size = [size[index] / scene_span[index] if scene_span[index] else 1.0 for index in range(3)]
            placement_ok = all(
                region.get("normalized_centroid", {}).get(axis, [value, value])[0] <= value <=
                region.get("normalized_centroid", {}).get(axis, [value, value])[1]
                for axis, value in zip(axis_names, normalized_centroid)
            )
            proportion_ok = all(
                region.get("normalized_size", {}).get(axis, [value, value])[0] <= value <=
                region.get("normalized_size", {}).get(axis, [value, value])[1]
                for axis, value in zip(axis_names, normalized_size)
            )
            reports[component_name] = {
                "object_name": object_name,
                "bbox_world": {"min": lower, "max": upper},
                "centroid_world": centroid,
                "relative_size": {"normalized_scene_span": normalized_size},
                "normalized_centroid": normalized_centroid,
                "expected_region": region,
                "presence_ok": True,
                "placement_ok": placement_ok,
                "proportion_ok": proportion_ok,
            }
        layout_ok = coverage["coverage_ok"] and all(
            report["presence_ok"] and report["placement_ok"] and report["proportion_ok"]
            for report in reports.values()
        )
        return {
            "layout_expectations_present": True,
            "layout_ok": layout_ok,
            "status": "pass" if layout_ok else "fail",
            "scene_bounds_world": {"min": scene_min, "max": scene_max},
            "component_reports": reports,
            "limitation": "Bounds/centroids verify coarse placement and proportion only; silhouette, depth, and shape still need separate review.",
        }


def scene_decomposition_from_dict(payload: dict[str, Any]) -> SceneDecomposition:
    """Load either the canonical evidence-bound record or the legacy compact shape.

    The loader deliberately validates after construction.  A reference board cannot
    gain blockout authority merely because its JSON parses: strict records must still
    bind primary components, claims, and strategies to concrete evidence.
    """
    if not isinstance(payload, dict):
        raise ValueError("scene decomposition must be a JSON object")

    def records_for(category: str) -> list[dict[str, Any]]:
        value = payload.get(category, [])
        if category == "camera_assumptions" and isinstance(value, dict):
            return list(value.values())
        if category == "symmetry" and isinstance(value, dict):
            return list(value.get("claims", []))
        return value if isinstance(value, list) else []

    raw_claims = payload.get("claims")
    if raw_claims is None:
        raw_claims = [
            record
            for category in CLAIM_CATEGORIES
            for record in records_for(category)
        ]
    if not isinstance(raw_claims, list):
        raise ValueError("scene decomposition claims must be a list")

    try:
        components = [Component(**record) for record in payload.get("components", [])]
        relationships = [Relationship(**record) for record in payload.get("relationships", [])]
        claims = [ReferenceClaim(**record) for record in raw_claims]
        strategies = [
            StrategyCandidate(**record)
            for record in (
                list(payload.get("candidate_modeling_strategies", []))
                + list(payload.get("rejected_strategies", []))
                if "strategies" not in payload
                else list(payload["strategies"])
            )
        ]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid scene decomposition record: {exc}") from exc
    result = SceneDecomposition(
        object_name=str(payload.get("object_name") or payload.get("target") or ""),
        object_class=str(payload.get("object_class") or "unknown"),
        reference_style=str(payload.get("reference_style") or "mixed"),
        components=components,
        relationships=relationships,
        claims=claims,
        strategies=strategies,
        require_evidence_bindings=bool(payload.get("require_evidence_bindings", False)),
    )
    result.validate()
    return result
