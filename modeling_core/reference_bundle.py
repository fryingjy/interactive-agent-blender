"""Assemble audited image evidence into one fail-closed multiview solver bundle."""

from __future__ import annotations

import hashlib
import json
import copy
import math
from pathlib import Path
from typing import Any


def _read(value: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return json.loads(Path(value).read_text(encoding="utf-8"))


def build_multiview_evidence_bundle(
    reference_audit: dict[str, Any] | str | Path,
    registration_gate: dict[str, Any] | str | Path,
    views: list[dict[str, Any]],
    *,
    required_component_support: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Bind accepted per-image evidence to existing identity and registration audits."""
    audit = _read(reference_audit)
    registration = _read(registration_gate)
    if audit.get("record_type") != "REFERENCE_SET_AUDIT" or registration.get("record_type") != "REFERENCE_REGISTRATION_GATE":
        raise ValueError("bundle requires reference-set and registration-gate records")
    if audit.get("target_id") != registration.get("target_id"):
        raise ValueError("reference and registration targets do not match")
    if not isinstance(views, list) or len(views) < 2:
        raise ValueError("multiview evidence requires at least two views")
    required_component_support = required_component_support or {}
    if any(not identifier or not isinstance(count, int) or isinstance(count, bool) or count < 1 for identifier, count in required_component_support.items()):
        raise ValueError("required component support must map ids to positive view counts")

    issues = []
    if not audit.get("pass"):
        issues.append("reference-set audit has not passed")
    if not registration.get("pass"):
        issues.append("reference-registration gate has not passed")
    authorized_hashes = set(audit.get("authorized_reference_sha256", []))
    authoritative_views = set(registration.get("authoritative_views", []))
    observed_view_ids = []
    observed_hashes = []
    bound_views = []
    component_support: dict[str, list[str]] = {}
    for specification in views:
        if not isinstance(specification, dict):
            raise ValueError("bundle views must be objects")
        view_id = str(specification.get("view_id") or "").strip().lower()
        source_id = str(specification.get("source_id") or "").strip()
        if not view_id:
            raise ValueError("bundle view ids must be non-empty")
        observed_view_ids.append(view_id)
        evidence = _read(specification.get("evidence"))
        if evidence.get("record_type") != "REFERENCE_IMAGE_EVIDENCE":
            raise ValueError(f"{view_id}: invalid reference image evidence")
        source = evidence.get("source", {})
        source_path = Path(source.get("path", ""))
        source_hash = str(source.get("sha256") or "").lower()
        hash_current = source_path.is_file() and hashlib.sha256(source_path.read_bytes()).hexdigest() == source_hash
        mask_path = Path(evidence.get("artifacts", {}).get("editable_mask", ""))
        mask_hash = evidence.get("artifact_sha256", {}).get("editable_mask")
        mask_current = mask_path.is_file() and hashlib.sha256(mask_path.read_bytes()).hexdigest() == mask_hash
        observed_hashes.append(source_hash)
        view_issues = []
        if not evidence.get("accepted_for_fitting"):
            view_issues.append("image extraction was not accepted")
        if not hash_current:
            view_issues.append("source image hash is stale or missing")
        if not mask_current:
            view_issues.append("editable mask hash is stale or missing")
        if source_hash not in authorized_hashes:
            view_issues.append("source image is not authorized by the reference-set audit")
        if view_id not in authoritative_views:
            view_issues.append("view is not authoritative in the registration gate")
        if not source_id:
            view_issues.append("view lacks a provenance source_id")
        solver_view = specification.get("solver_view")
        if solver_view is not None:
            if not isinstance(solver_view, dict):
                raise ValueError(f"{view_id}: solver_view must be an object")
            solver_view = copy.deepcopy(solver_view)
            if solver_view.get("id") != view_id:
                view_issues.append("solver view id does not match the evidence view")
            if solver_view.get("image_size") != source.get("image_size"):
                view_issues.append("solver view image size does not match the source image")
            if solver_view.get("projection") not in {"orthographic", "perspective"}:
                view_issues.append("solver view has an unsupported projection")
            numeric_values = [
                value for key, value in solver_view.items()
                if key not in {"id", "projection", "image_size", "world_to_camera"}
            ]
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in numeric_values):
                view_issues.append("solver view contains non-finite camera values")

        component_record = None
        if specification.get("components") is not None:
            component_record = _read(specification["components"])
            if component_record.get("record_type") != "REFERENCE_COMPONENT_EVIDENCE":
                raise ValueError(f"{view_id}: invalid component evidence")
            if component_record.get("source_reference_sha256") != source_hash:
                view_issues.append("component labels belong to a different source image")
            if component_record.get("source_mask_sha256") != mask_hash:
                view_issues.append("component labels belong to a different silhouette mask revision")
            if not component_record.get("accepted_for_bundle"):
                view_issues.append("component evidence was not accepted")
            label_record = component_record.get("label_map", {})
            label_path = Path(label_record.get("path", ""))
            label_current = label_path.is_file() and hashlib.sha256(label_path.read_bytes()).hexdigest() == label_record.get("sha256")
            if not label_current:
                view_issues.append("component label-map hash is stale or missing")
            for component_id in component_record.get("observations", {}):
                component_support.setdefault(component_id, []).append(view_id)
        if view_issues:
            issues.extend(f"{view_id}: {issue}" for issue in view_issues)
        bound_views.append({
            "view_id": view_id,
            "source_id": source_id,
            "source_path": str(source_path.resolve()),
            "source_sha256": source_hash,
            "mask_path": str(mask_path.resolve()),
            "mask_sha256": mask_hash,
            "measurements": evidence.get("measurements"),
            "component_evidence": component_record,
            "solver_view": solver_view,
            "issues": view_issues,
        })

    if len(observed_view_ids) != len(set(observed_view_ids)):
        issues.append("bundle view ids are not unique")
    if len(observed_hashes) != len(set(observed_hashes)):
        issues.append("the same source image is assigned to more than one view")
    missing_authoritative = sorted(authoritative_views - set(observed_view_ids))
    if missing_authoritative:
        issues.append(f"authoritative views are missing evidence: {missing_authoritative}")
    missing_support = {
        identifier: {"required": count, "observed": len(set(component_support.get(identifier, [])))}
        for identifier, count in required_component_support.items()
        if len(set(component_support.get(identifier, []))) < count
    }
    if missing_support:
        issues.append(f"components lack required cross-view support: {sorted(missing_support)}")
    return {
        "schema_version": 1,
        "record_type": "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE",
        "target_id": audit.get("target_id"),
        "target_variant": audit.get("target_variant"),
        "views": bound_views,
        "component_support": component_support,
        "missing_component_support": missing_support,
        "accepted_for_shape_solving": not issues,
        "issues": issues,
        "claim_boundary": "The bundle proves hash binding, declared target/variant audit, registration suitability, and visible component support. It does not independently recognize object identity or infer hidden geometry.",
    }
