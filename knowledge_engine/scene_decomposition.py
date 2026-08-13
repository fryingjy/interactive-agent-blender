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
    "slides_relative_to",
    "rotates_relative_to",
    "rests_on",
    "transitions_into",
    "occupies_surface_of",
    "interacts_with",
    "fastens_to",
    "hangs_from",
}


@dataclass
class Component:
    name: str
    role: str  # primary / secondary / tertiary, per the reference protocol's own form hierarchy
    manufacture: str = "unknown"  # structural / cosmetic / unknown
    separately_manufactured: bool | None = None  # None = not yet determined from reference
    notes: str = ""

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("component name is required")
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role '{self.role}' for component '{self.name}'")
        if self.manufacture not in VALID_MANUFACTURE:
            raise ValueError(f"invalid manufacture '{self.manufacture}' for component '{self.name}'")


@dataclass
class Relationship:
    from_component: str
    to_component: str
    type: str
    notes: str = ""

    def validate_type(self) -> None:
        if self.type not in VALID_RELATIONSHIP_TYPES:
            raise ValueError(f"invalid relationship type '{self.type}'")


@dataclass
class SceneDecomposition:
    object_name: str
    components: list[Component] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)

    def validate(self) -> None:
        if not self.object_name.strip():
            raise ValueError("object_name is required")
        if not self.components:
            raise ValueError("at least one component is required -- an empty decomposition is not a decomposition")
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

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "object_name": self.object_name,
            "components": [asdict(c) for c in self.components],
            "relationships": [asdict(r) for r in self.relationships],
        }

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
