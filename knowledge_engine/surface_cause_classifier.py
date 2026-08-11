"""Conservative intervention-based classification of visible surface defects.

This module does not infer artistic defects from one beauty render.  It classifies
which controlled intervention removes a discrepancy while checking whether base or
evaluated geometry changed.  Conflicting evidence remains uncertain.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SurfaceCauseEvidence:
    base_geometry_changed: bool = False
    evaluated_geometry_changed: bool = False
    silhouette_or_depth_changed: bool = False
    face_orientation_or_split_normals_changed: bool = False
    normal_repair_neutralizes: bool = False
    material_state_changed: bool = False
    neutral_material_neutralizes: bool = False
    lighting_state_changed: bool = False
    neutral_lighting_neutralizes: bool = False
    bevel_parameters_changed: bool = False
    bevel_repair_neutralizes: bool = False


@dataclass(frozen=True)
class SurfaceCauseDiagnosis:
    cause: str
    confidence: float
    reasons: tuple[str, ...]
    next_action: str


@dataclass(frozen=True)
class SurfaceCauseAblation:
    """One controlled repair applied to an otherwise fixed mixed-defect state."""

    cause: str
    intervention_applied: bool
    target_state_changed: bool
    unrelated_states_held_constant: bool
    before_error: float
    after_error: float
    before_changed_pixels: int
    after_changed_pixels: int


@dataclass(frozen=True)
class MixedSurfaceCauseDiagnosis:
    causes: tuple[str, ...]
    rejected: tuple[str, ...]
    confidence: float
    reductions: tuple[tuple[str, float], ...]
    status: str
    next_action: str


def classify_surface_cause(evidence: SurfaceCauseEvidence) -> SurfaceCauseDiagnosis:
    """Return a bounded cause from controlled state and repair interventions."""

    candidates: list[tuple[str, tuple[str, ...], str]] = []

    if (
        evidence.bevel_parameters_changed
        and evidence.evaluated_geometry_changed
        and evidence.bevel_repair_neutralizes
    ):
        candidates.append((
            "BEVEL_PROFILE",
            ("bevel parameters changed", "evaluated geometry changed", "bevel repair neutralized discrepancy"),
            "Inspect bevel width, segments, limit method, clamp, and modifier order.",
        ))

    if (
        evidence.base_geometry_changed
        and evidence.evaluated_geometry_changed
        and evidence.silhouette_or_depth_changed
    ):
        candidates.append((
            "GEOMETRY",
            ("base geometry changed", "evaluated geometry changed", "silhouette/depth changed"),
            "Repair the control cage or rebuild the localized surface region.",
        ))

    if (
        not evidence.base_geometry_changed
        and evidence.face_orientation_or_split_normals_changed
        and evidence.normal_repair_neutralizes
    ):
        candidates.append((
            "NORMALS",
            ("geometry stayed fixed", "normal state changed", "normal repair neutralized discrepancy"),
            "Inspect face orientation, smooth-by-angle, sharp edges, and custom normal data.",
        ))

    if (
        not evidence.base_geometry_changed
        and not evidence.face_orientation_or_split_normals_changed
        and evidence.material_state_changed
        and evidence.neutral_material_neutralizes
    ):
        candidates.append((
            "MATERIAL",
            ("geometry and normal state stayed fixed", "material state changed", "neutral material neutralized discrepancy"),
            "Inspect material slots, roughness/metallic values, maps, and color-space semantics.",
        ))

    if (
        not evidence.base_geometry_changed
        and not evidence.face_orientation_or_split_normals_changed
        and not evidence.material_state_changed
        and evidence.lighting_state_changed
        and evidence.neutral_lighting_neutralizes
    ):
        candidates.append((
            "LIGHTING",
            ("object state stayed fixed", "lighting state changed", "neutral lighting neutralized discrepancy"),
            "Keep the asset unchanged and repair or replace the review light rig.",
        ))

    if len(candidates) == 1:
        cause, reasons, action = candidates[0]
        return SurfaceCauseDiagnosis(cause, 0.95, reasons, action)
    if len(candidates) > 1:
        return SurfaceCauseDiagnosis(
            "CONFLICTING",
            0.25,
            tuple(f"{cause}: {', '.join(reasons)}" for cause, reasons, _ in candidates),
            "Isolate one variable at a time and rerun the intervention matrix.",
        )
    return SurfaceCauseDiagnosis(
        "UNRESOLVED",
        0.1,
        ("no controlled repair produced a unique causal signature",),
        "Capture neutral material, neutral lighting, normal, depth, and evaluated-geometry evidence.",
    )


def diagnose_mixed_surface_causes(
    ablations: tuple[SurfaceCauseAblation, ...],
    minimum_relative_reduction: float = 0.02,
) -> MixedSurfaceCauseDiagnosis:
    """Identify multiple causes only when independent repair ablations reduce error.

    The caller must hold every unrelated state constant for each intervention.  This
    function deliberately rejects an apparently successful repair when collateral
    state changed, preventing a broad reset from being credited to one cause.
    """

    allowed = {"GEOMETRY", "NORMALS", "MATERIAL", "LIGHTING", "BEVEL_PROFILE"}
    accepted: list[tuple[str, float]] = []
    rejected: list[str] = []
    seen: set[str] = set()
    for item in ablations:
        if item.cause not in allowed or item.cause in seen:
            rejected.append(item.cause)
            continue
        seen.add(item.cause)
        denominator = max(item.before_error, 1e-12)
        reduction = (item.before_error - item.after_error) / denominator
        visible_reduction = item.after_changed_pixels < item.before_changed_pixels
        controlled = (
            item.intervention_applied
            and item.target_state_changed
            and item.unrelated_states_held_constant
        )
        if controlled and reduction >= minimum_relative_reduction and visible_reduction:
            accepted.append((item.cause, reduction))
        else:
            rejected.append(item.cause)

    accepted.sort(key=lambda pair: pair[1], reverse=True)
    if not accepted:
        return MixedSurfaceCauseDiagnosis(
            (), tuple(rejected), 0.1, (), "UNRESOLVED",
            "Capture controlled one-variable repair ablations against a fixed review baseline.",
        )
    complete = len(accepted) == len(allowed) and not rejected
    return MixedSurfaceCauseDiagnosis(
        tuple(cause for cause, _ in accepted),
        tuple(rejected),
        0.95 if complete else 0.7,
        tuple(accepted),
        "MULTI_CAUSE_CONFIRMED" if len(accepted) > 1 else "SINGLE_CAUSE_CONFIRMED",
        "Repair causes in measured order, re-render after each change, and check for interactions.",
    )
