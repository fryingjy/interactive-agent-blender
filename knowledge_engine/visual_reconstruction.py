"""Audit evidence-bound visual observation -> 3D interpretation -> construction chains.

This module complements ``reference_analysis``.  A reference set can be complete
and authoritative while its proposed mental model is still wrong.  Here each
important region must carry competing 3D interpretations whose visual
consequences are tested against observations recorded independently of the
hypotheses.  Construction is allowed only from the selected interpretation;
unresolved regions must remain explicit and reversible.
"""

from __future__ import annotations

from typing import Any

from knowledge_engine.representation_hypothesis import rank_competing_hypotheses


REQUIRED_PASSES = (
    "identity",
    "silhouette",
    "massing",
    "components",
    "depth",
    "negative_space",
    "cross_sections",
    "representation_hypotheses",
    "cross_view_prediction",
    "uncertainty",
    "construction_plan",
)

STRUCTURE_TYPES = {
    "revolved_body", "extruded_slab", "tapered_prism", "rounded_shell",
    "swept_tube", "lofted_transition", "nested_cylindrical_stack",
    "offset_panel", "inset_recess", "wrapped_band", "attached_boss",
    "through_hole", "open_cavity", "bridged_transition",
    "floating_separate_assembly", "continuous_molded_housing",
}

CONSTRUCTION_FAMILIES = {
    "box_poly", "subd_cage", "profile_extrusion", "profile_revolution",
    "profile_loft", "quad_shell_grid", "curve_sweep", "boolean_cage",
    "separate_radial_assembly", "live_modifier_stack",
}


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def audit_visual_reconstruction(
    payload: dict[str, Any],
    reference_items: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Validate and evaluate one visual reconstruction package.

    The function does not infer pixels.  It proves that recorded observations
    are independent, property-scoped, cross-view tested, and actually constrain
    the construction plan rather than merely accompanying it as prose.
    """
    errors: list[str] = []
    target_id = payload.get("target_id")
    target_variant = payload.get("target_variant")
    if not isinstance(target_id, str) or not target_id.strip():
        _fail(errors, "target_id is required")
    if not isinstance(target_variant, str) or not target_variant.strip():
        _fail(errors, "target_variant is required")

    observations_list = payload.get("observations", [])
    observations: dict[str, dict[str, Any]] = {}
    for observation in observations_list:
        observation_id = observation.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id.strip():
            _fail(errors, "every observation needs observation_id")
            continue
        if observation_id in observations:
            _fail(errors, f"duplicate observation_id: {observation_id}")
        observations[observation_id] = observation
        reference_id = observation.get("reference_id")
        if reference_id not in reference_items:
            _fail(errors, f"observation {observation_id} references missing source {reference_id}")
        if not observation.get("view") or not observation.get("property"):
            _fail(errors, f"observation {observation_id} needs view and property")
        if "value" not in observation:
            _fail(errors, f"observation {observation_id} needs an independently recorded value")
        if not observation.get("method") or not observation.get("evidence_path"):
            _fail(errors, f"observation {observation_id} needs method and evidence_path")

    authority = {
        (item.get("reference_id"), item.get("property"))
        for item in payload.get("property_authority", [])
        if item.get("fit_for_property") is True
    }
    for observation_id, observation in observations.items():
        binding = (observation.get("reference_id"), observation.get("property"))
        if binding not in authority:
            _fail(errors, f"observation {observation_id} lacks property-specific source suitability")

    pass_records = payload.get("passes", {})
    for pass_name in REQUIRED_PASSES:
        record = pass_records.get(pass_name)
        if not isinstance(record, dict) or record.get("status") not in {"PASS", "BOUNDED"}:
            _fail(errors, f"visual pass '{pass_name}' is missing or not PASS/BOUNDED")
            continue
        evidence_ids = record.get("evidence_ids", [])
        if not evidence_ids or any(item not in observations for item in evidence_ids):
            _fail(errors, f"visual pass '{pass_name}' needs valid independent evidence_ids")

    region_reports = []
    selected_hypotheses: list[str] = []
    contradiction_count = 0
    for region in payload.get("regions", []):
        region_id = region.get("region_id")
        hypotheses = region.get("hypotheses", [])
        if not region_id:
            _fail(errors, "every region needs region_id")
            continue
        if len(hypotheses) < 2:
            _fail(errors, f"region {region_id} needs at least two competing hypotheses")
            continue
        candidates = []
        for hypothesis in hypotheses:
            hypothesis_id = hypothesis.get("hypothesis_id")
            interpretation = hypothesis.get("interpretation", {})
            construction = hypothesis.get("construction", {})
            if interpretation.get("structure_type") not in STRUCTURE_TYPES:
                _fail(errors, f"hypothesis {hypothesis_id} has unsupported structure_type")
            if construction.get("family") not in CONSTRUCTION_FAMILIES:
                _fail(errors, f"hypothesis {hypothesis_id} has unsupported construction family")
            predictions = hypothesis.get("predicted_consequences", [])
            prediction_views = {item.get("view") for item in predictions if item.get("view")}
            if len(prediction_views) < 2:
                _fail(errors, f"hypothesis {hypothesis_id} needs consequences in at least two views")
            candidates.append({
                "name": hypothesis_id,
                "representation": interpretation.get("summary", ""),
                "predicted_consequences": predictions,
            })
        ranking = rank_competing_hypotheses(
            candidates,
            reference_items,
            observations,
            minimum_confirmed_views=int(region.get("minimum_confirmed_views", 2)),
        )
        contradiction_count += sum(
            candidate["counts"]["CONTRADICTED"] for candidate in ranking["candidates"]
        )
        declared = region.get("selected_hypothesis_id")
        if declared is not None:
            if ranking["selected_candidate"] != declared:
                _fail(
                    errors,
                    f"region {region_id} declares {declared!r} but evidence selects "
                    f"{ranking['selected_candidate']!r} ({ranking['disposition']})",
                )
            else:
                selected_hypotheses.append(declared)
        elif not region.get("uncertainty"):
            _fail(errors, f"unselected region {region_id} needs an explicit uncertainty boundary")
        region_reports.append({"region_id": region_id, "ranking": ranking})

    if not region_reports:
        _fail(errors, "at least one ambiguous region is required")
    if contradiction_count == 0:
        _fail(errors, "the package eliminates no interpretation; hypotheses are not discriminating")

    plan = payload.get("construction_plan", {})
    plan_hypotheses = plan.get("selected_hypothesis_ids", [])
    if sorted(plan_hypotheses) != sorted(selected_hypotheses):
        _fail(errors, "construction_plan must reference exactly the evidence-selected hypotheses")
    if not plan.get("generic_operations"):
        _fail(errors, "construction_plan requires generic_operations")
    unresolved_regions = {
        region.get("region_id") for region in payload.get("regions", [])
        if region.get("selected_hypothesis_id") is None
    }
    reversible_regions = {
        item.get("region_id") for item in plan.get("reversible_assumptions", [])
    }
    if not unresolved_regions <= reversible_regions:
        _fail(errors, "every unresolved region must remain a reversible construction assumption")

    checks = {
        "identity_bound": bool(target_id and target_variant),
        "independent_observations": bool(observations) and not any("observation" in error for error in errors),
        "property_specific_authority": bool(authority) and not any("source suitability" in error for error in errors),
        "eleven_passes_recorded": all(name in pass_records for name in REQUIRED_PASSES),
        "competing_interpretations_tested": bool(region_reports),
        "bad_interpretation_eliminated": contradiction_count > 0,
        "construction_bound_to_selected_interpretation": sorted(plan_hypotheses) == sorted(selected_hypotheses),
        "uncertainty_kept_reversible": unresolved_regions <= reversible_regions,
    }
    return {
        "schema_version": 1,
        "record_type": "VISUAL_RECONSTRUCTION_AUDIT",
        "target_id": target_id,
        "checks": checks,
        "region_reports": region_reports,
        "selected_hypothesis_ids": selected_hypotheses,
        "contradiction_count": contradiction_count,
        "errors": errors,
        "pass": not errors and all(checks.values()),
    }
