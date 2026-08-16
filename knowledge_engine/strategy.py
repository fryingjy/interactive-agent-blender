"""Evidence-readable strategy selection for early modeling decisions.

This is deliberately a constraint/ranking layer, not an asset generator.  It makes the reasons for
a workflow choice inspectable and leaves tied or low-margin choices uncertain.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelingBrief:
    shape_family: str = "mechanical"
    smooth_continuous_surface: bool = False
    repeated_elements: bool = False
    symmetric: bool = False
    follows_path: bool = False
    destructive_required: bool = False
    deformation_expected: bool = False
    watertight_union_required: bool = False
    independent_motion_or_material: bool = False
    local_damage_fraction: float = 0.0
    failed_repairs: int = 0
    modifier_instability: float = 0.0
    notes: tuple[str, ...] = field(default_factory=tuple)


def _pick(scores: dict[str, float], reasons: dict[str, list[str]]) -> dict:
    ranked = sorted(scores, key=lambda key: (-scores[key], key))
    best, runner_up = ranked[:2]
    margin = scores[best] - scores[runner_up]
    return {
        "choice": best,
        "score": round(scores[best], 3),
        "runner_up": runner_up,
        "margin": round(margin, 3),
        "confidence": "HIGH" if margin >= 3 else "MEDIUM" if margin >= 1 else "LOW",
        "reasons": reasons[best],
        "all_scores": {key: round(value, 3) for key, value in sorted(scores.items())},
    }


def choose_primary_representation(brief: ModelingBrief) -> dict:
    scores = {"BOX_MESH": 0.0, "SUBD_CAGE": 0.0, "CURVE": 0.0}
    reasons = {key: [] for key in scores}
    if brief.follows_path:
        scores["CURVE"] += 6
        reasons["CURVE"].append("form follows an editable path")
    if brief.smooth_continuous_surface:
        scores["SUBD_CAGE"] += 5
        reasons["SUBD_CAGE"].append("continuous smooth surface needs controlled curvature")
    if brief.shape_family in {"mechanical", "architectural", "blockout"}:
        scores["BOX_MESH"] += 3
        reasons["BOX_MESH"].append("shape family favors explicit planar proportions")
    if brief.deformation_expected:
        scores["SUBD_CAGE"] += 2
        reasons["SUBD_CAGE"].append("deformation benefits from planned continuous flow")
    if brief.repeated_elements:
        scores["BOX_MESH"] += 1
        reasons["BOX_MESH"].append("repeatable modules can remain simple instances")
    return _pick(scores, reasons)


def choose_component_policy(brief: ModelingBrief) -> dict:
    scores = {"SEPARATE_COMPONENTS": 0.0, "CONTINUOUS_MESH": 0.0}
    reasons = {key: [] for key in scores}
    if brief.independent_motion_or_material:
        scores["SEPARATE_COMPONENTS"] += 5
        reasons["SEPARATE_COMPONENTS"].append("part has independent motion or material identity")
    if brief.watertight_union_required:
        scores["CONTINUOUS_MESH"] += 5
        reasons["CONTINUOUS_MESH"].append("final deliverable requires one watertight shell")
    if brief.smooth_continuous_surface:
        scores["CONTINUOUS_MESH"] += 3
        reasons["CONTINUOUS_MESH"].append("surface continuity crosses the proposed boundary")
    if brief.repeated_elements:
        scores["SEPARATE_COMPONENTS"] += 2
        reasons["SEPARATE_COMPONENTS"].append("repeated elements are easier to instance separately")
    return _pick(scores, reasons)


def choose_edit_policy(brief: ModelingBrief) -> dict:
    scores = {"NONDESTRUCTIVE_MODIFIERS": 0.0, "DESTRUCTIVE_EDIT": 0.0}
    reasons = {key: [] for key in scores}
    # Retaining an editable cage/modifier stack is the safe production default.
    # Without an explicit downstream reason to bake geometry, a zero-evidence
    # tie must not select destructive editing merely because of lexical sort
    # order in _pick().
    scores["NONDESTRUCTIVE_MODIFIERS"] += 0.1
    reasons["NONDESTRUCTIVE_MODIFIERS"].append(
        "no destructive downstream constraint is evidenced"
    )
    if brief.symmetric:
        scores["NONDESTRUCTIVE_MODIFIERS"] += 3
        reasons["NONDESTRUCTIVE_MODIFIERS"].append("symmetry remains editable")
    if brief.repeated_elements:
        scores["NONDESTRUCTIVE_MODIFIERS"] += 3
        reasons["NONDESTRUCTIVE_MODIFIERS"].append("repeat count and spacing remain editable")
    if brief.follows_path:
        scores["NONDESTRUCTIVE_MODIFIERS"] += 2
        reasons["NONDESTRUCTIVE_MODIFIERS"].append("path remains adjustable")
    if brief.destructive_required:
        scores["DESTRUCTIVE_EDIT"] += 7
        reasons["DESTRUCTIVE_EDIT"].append("downstream constraint explicitly requires baked geometry")
    return _pick(scores, reasons)


def choose_repair_policy(brief: ModelingBrief) -> dict:
    scores = {"PATCH_REGION": 0.0, "REBUILD_REGION": 0.0}
    reasons = {key: [] for key in scores}
    damage = min(1.0, max(0.0, brief.local_damage_fraction))
    scores["PATCH_REGION"] += (1.0 - damage) * 4
    scores["REBUILD_REGION"] += damage * 4
    if damage <= 0.2:
        reasons["PATCH_REGION"].append("damage is localized")
    else:
        reasons["REBUILD_REGION"].append("damage affects a broad fraction of the region")
    scores["REBUILD_REGION"] += brief.failed_repairs * 1.5
    if brief.failed_repairs >= 2:
        reasons["REBUILD_REGION"].append("multiple repairs already failed")
    scores["REBUILD_REGION"] += max(0.0, brief.modifier_instability) * 3
    if brief.modifier_instability >= 0.5:
        reasons["REBUILD_REGION"].append("evaluated stack is unstable")
    return _pick(scores, reasons)


def choose_strategy(brief: ModelingBrief) -> dict:
    """Return independent, inspectable decisions instead of one opaque label."""
    return {
        "representation": choose_primary_representation(brief),
        "components": choose_component_policy(brief),
        "editing": choose_edit_policy(brief),
        "repair": choose_repair_policy(brief),
    }
