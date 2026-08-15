"""Fail-closed classification of editable variants versus production low topology."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HighLowEvidence:
    high_object: str
    low_object: str
    separate_collections: bool
    independent_mesh_datablocks: bool
    high_base_faces: int
    low_base_faces: int
    high_connected_components: int
    low_connected_components: int
    high_live_modifiers: tuple[str, ...] = ()
    low_live_modifiers: tuple[str, ...] = ()
    low_uv_layer: str | None = None
    low_uv_loop_count: int = 0
    low_degenerate_uv_faces: int = 0
    low_uv_inside_unit_tile: bool = False
    silhouette_iou_by_view: dict[str, float] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.high_object.strip() or not self.low_object.strip():
            raise ValueError("high and low object names are required")
        if self.high_object == self.low_object:
            raise ValueError("high and low object names must differ")
        if self.high_base_faces < 1 or self.low_base_faces < 1:
            raise ValueError("high and low face counts must be positive")
        if self.high_connected_components < 1 or self.low_connected_components < 1:
            raise ValueError("connected-component counts must be positive")
        if self.low_uv_loop_count < 0 or self.low_degenerate_uv_faces < 0:
            raise ValueError("UV counts cannot be negative")
        invalid = {
            view: value
            for view, value in self.silhouette_iou_by_view.items()
            if not 0.0 <= value <= 1.0
        }
        if invalid:
            raise ValueError(f"silhouette IoU must be in [0, 1]: {invalid}")


def audit_production_high_low(
    evidence: HighLowEvidence,
    *,
    max_low_to_high_face_ratio: float = 0.65,
    minimum_silhouette_iou: float = 0.90,
    minimum_view_count: int = 2,
    require_live_modifiers: bool = True,
) -> dict[str, Any]:
    """Classify a pair without pretending an equal cage is production retopology.

    The modifier check proves only that current stacks remain live. Blender does not retain enough
    history to prove that no modifier was ever applied before the audit, so that limitation is
    returned explicitly.
    """
    evidence.validate()
    if not 0.0 < max_low_to_high_face_ratio < 1.0:
        raise ValueError("max_low_to_high_face_ratio must be between 0 and 1")
    if not 0.0 <= minimum_silhouette_iou <= 1.0:
        raise ValueError("minimum_silhouette_iou must be in [0, 1]")
    if minimum_view_count < 1:
        raise ValueError("minimum_view_count must be positive")

    face_ratio = evidence.low_base_faces / evidence.high_base_faces
    topology_is_distinct = (
        evidence.low_base_faces != evidence.high_base_faces and face_ratio <= max_low_to_high_face_ratio
    )
    uv_pass = bool(
        evidence.low_uv_layer
        and evidence.low_uv_loop_count > 0
        and evidence.low_degenerate_uv_faces == 0
        and evidence.low_uv_inside_unit_tile
    )
    silhouette_pass = bool(
        len(evidence.silhouette_iou_by_view) >= minimum_view_count
        and min(evidence.silhouette_iou_by_view.values(), default=0.0) >= minimum_silhouette_iou
    )
    live_modifier_pass = bool(
        not require_live_modifiers
        or (evidence.high_live_modifiers and evidence.low_live_modifiers)
    )
    connectivity_pass = (
        evidence.high_connected_components == 1 and evidence.low_connected_components == 1
    )
    checks = {
        "separate_collections": evidence.separate_collections,
        "independent_mesh_datablocks": evidence.independent_mesh_datablocks,
        "purpose_authored_lower_topology": topology_is_distinct,
        "single_connected_component_each": connectivity_pass,
        "low_uv_ready": uv_pass,
        "multiview_shape_preserved": silhouette_pass,
        "current_modifier_stacks_live": live_modifier_pass,
    }
    editable_variant_only = bool(
        evidence.separate_collections
        and evidence.independent_mesh_datablocks
        and evidence.low_base_faces == evidence.high_base_faces
    )
    if all(checks.values()):
        disposition = "PRODUCTION_LOW_AUDIT_PASS"
    elif editable_variant_only:
        disposition = "EDITABLE_VARIANT_ONLY"
    else:
        disposition = "REVIEW_REQUIRED"
    return {
        "disposition": disposition,
        "checks": checks,
        "pass": disposition == "PRODUCTION_LOW_AUDIT_PASS",
        "editable_variant_only": editable_variant_only,
        "face_ratio": face_ratio,
        "thresholds": {
            "max_low_to_high_face_ratio": max_low_to_high_face_ratio,
            "minimum_silhouette_iou": minimum_silhouette_iou,
            "minimum_view_count": minimum_view_count,
            "require_live_modifiers": require_live_modifiers,
        },
        "modifier_history_boundary": (
            "Current live stacks are observed; Blender does not prove that no modifier was applied "
            "earlier in the asset's history."
        ),
        "failures": [name for name, passed in checks.items() if not passed],
    }
