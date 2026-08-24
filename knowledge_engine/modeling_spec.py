"""Validate a reference-bound modeling specification before Blender construction.

Unlike generic image-to-scene specs, semantic components are not assumed to be separate Blender
objects and arbitrary component-count quotas are forbidden. The contract records the visible
identity features, continuity decisions, representation, and measurable pass criteria that keep a
reference build from degenerating into a generic primitive assembly.
"""

from __future__ import annotations

import math
import string
from typing import Any


ROLES = {"PRIMARY", "SECONDARY", "TERTIARY"}
CONTINUITY_POLICIES = {"CONTINUOUS", "SEPARATE", "UNRESOLVED"}
REPRESENTATIONS = {
    "BOX_POLY", "PROFILE_EXTRUSION", "PROFILE_LOFT", "REVOLVE", "CURVE_SWEEP",
    "SUBD_CAGE", "BOOLEAN_PANEL", "RADIAL_CAGE", "AUTHORED_QUAD_CAGE", "HYBRID",
}
SALIENCE = {"HIGH", "MEDIUM", "LOW"}
MEASUREMENT_TYPES = {"RATIO", "LANDMARK", "NEGATIVE_SPACE", "SILHOUETTE", "RELATIONSHIP"}
REQUIRED_PASSES = {"REFERENCE_ANALYSIS", "PRIMARY_BLOCKOUT", "PROPORTION_SILHOUETTE"}


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in string.hexdigits for character in value)
    )


def validate_reference_modeling_spec(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict) or payload.get("record_type") != "REFERENCE_MODELING_SPEC":
        return {"schema_version": 1, "record_type": "REFERENCE_MODELING_SPEC_AUDIT", "errors": ["wrong record_type"], "pass": False}
    target = payload.get("target")
    if not isinstance(target, dict):
        errors.append("target must be an object")
        target = {}
    if not all(isinstance(target.get(key), str) and target[key].strip() for key in ("target_id", "target_variant")):
        errors.append("target_id and target_variant are required")
    if target.get("complexity") not in {"SIMPLE", "MODERATE", "COMPLEX"}:
        errors.append("target complexity must be SIMPLE, MODERATE, or COMPLEX")
    reference_hashes = target.get("authorized_reference_sha256")
    if not isinstance(reference_hashes, list) or not reference_hashes or any(
        not _is_sha256(value) for value in reference_hashes
    ) or len(reference_hashes) != len(set(reference_hashes)):
        errors.append("target requires unique authorized reference SHA-256 values")
        reference_hashes = []

    components = payload.get("components")
    if not isinstance(components, list) or not components:
        errors.append("at least one semantic component is required")
        components = []
    component_ids = [item.get("id") for item in components if isinstance(item, dict)]
    if len(component_ids) != len(components) or any(not isinstance(value, str) or not value.strip() for value in component_ids):
        errors.append("every component requires a non-empty id")
    if len(component_ids) != len(set(component_ids)):
        errors.append("component ids must be unique")
    primary_ids: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            continue
        component_id = component.get("id")
        if component.get("role") not in ROLES:
            errors.append(f"component {component_id!r} has invalid role")
        if component.get("role") == "PRIMARY" and isinstance(component_id, str):
            primary_ids.add(component_id)
        continuity = component.get("continuity_policy")
        if continuity not in CONTINUITY_POLICIES:
            errors.append(f"component {component_id!r} has invalid continuity_policy")
        if continuity == "UNRESOLVED" and component.get("high_salience") is True:
            errors.append(f"high-salience component {component_id!r} has unresolved continuity")
        if component.get("representation") not in REPRESENTATIONS:
            errors.append(f"component {component_id!r} has invalid representation")
        if not str(component.get("construction_justification") or "").strip():
            errors.append(f"component {component_id!r} requires construction_justification")
        evidence = component.get("evidence_sha256")
        if not isinstance(evidence, list) or not evidence or not set(evidence) <= set(reference_hashes):
            errors.append(f"component {component_id!r} is not bound to authorized reference evidence")
        if component.get("depth_critical") is True and not component.get("reversible_until_multiview_pass") is True:
            errors.append(f"depth-critical component {component_id!r} must remain reversible until multi-view pass")

    features = payload.get("identity_features")
    if not isinstance(features, list) or not features:
        errors.append("identity_features must be a non-empty list")
        features = []
    feature_ids = [item.get("id") for item in features if isinstance(item, dict)]
    if len(feature_ids) != len(features) or len(feature_ids) != len(set(feature_ids)):
        errors.append("identity feature ids must be present and unique")
    high_feature_components: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            continue
        feature_id = feature.get("id")
        component_id = feature.get("component_id")
        if component_id not in set(component_ids):
            errors.append(f"identity feature {feature_id!r} cites an unknown component")
        if feature.get("salience") not in SALIENCE:
            errors.append(f"identity feature {feature_id!r} has invalid salience")
        if feature.get("salience") == "HIGH" and isinstance(component_id, str):
            high_feature_components.add(component_id)
        if not str(feature.get("description") or "").strip():
            errors.append(f"identity feature {feature_id!r} requires a visible description")
        if feature.get("evidence_sha256") not in reference_hashes:
            errors.append(f"identity feature {feature_id!r} is not bound to authorized evidence")
        measurement = feature.get("measurement")
        if not isinstance(measurement, dict) or measurement.get("type") not in MEASUREMENT_TYPES:
            errors.append(f"identity feature {feature_id!r} requires a supported measurement")
            continue
        tolerance = measurement.get("tolerance")
        if (
            not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool)
            or not math.isfinite(float(tolerance)) or float(tolerance) <= 0
        ):
            errors.append(f"identity feature {feature_id!r} requires a finite positive tolerance")
    missing_primary_features = sorted(primary_ids - high_feature_components)
    if missing_primary_features:
        errors.append(f"primary components lack HIGH identity features: {missing_primary_features}")

    passes = payload.get("passes")
    if not isinstance(passes, list) or not passes:
        errors.append("passes must be a non-empty list")
        passes = []
    pass_ids = [item.get("stage") for item in passes if isinstance(item, dict)]
    if len(pass_ids) != len(passes) or len(pass_ids) != len(set(pass_ids)):
        errors.append("pass stages must be present and unique")
    missing_passes = sorted(REQUIRED_PASSES - set(pass_ids))
    if missing_passes:
        errors.append(f"required passes missing: {missing_passes}")
    for stage_pass in passes:
        if not isinstance(stage_pass, dict):
            continue
        criteria = stage_pass.get("criteria")
        if not isinstance(criteria, list) or not criteria or len(criteria) > 5:
            errors.append(f"pass {stage_pass.get('stage')!r} requires 1-5 criteria")
            continue
        for criterion in criteria:
            if (
                not isinstance(criterion, dict)
                or criterion.get("feature_id") not in set(feature_ids)
                or not str(criterion.get("observable") or "").strip()
                or criterion.get("channel") not in {"REFERENCE", "BASE_CAGE", "EVALUATED", "VISUAL", "TECHNICAL"}
            ):
                errors.append(f"pass {stage_pass.get('stage')!r} contains an invalid criterion")

    repair_policy = payload.get("repair_policy")
    if not isinstance(repair_policy, dict):
        errors.append("repair_policy is required")
    elif repair_policy.get("max_attempts_per_region_stage") != 3 or repair_policy.get("stagnation_limit") != 2:
        errors.append("repair_policy must use max 3 attempts and a 2-attempt stagnation limit")

    return {
        "schema_version": 1,
        "record_type": "REFERENCE_MODELING_SPEC_AUDIT",
        "target_id": target.get("target_id"),
        "target_variant": target.get("target_variant"),
        "component_ids": component_ids,
        "identity_feature_ids": feature_ids,
        "authorized_reference_sha256": sorted(reference_hashes),
        "errors": errors,
        "pass": not errors,
        "claim_boundary": "A valid spec makes visible intent and repair limits explicit; it does not prove the interpretation or resulting model is accurate.",
    }
