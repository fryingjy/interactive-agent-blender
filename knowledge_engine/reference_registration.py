"""Reference suitability and camera/pose registration gates.

This module prevents silhouette disagreement from being labeled a geometry defect until the
reference view has an explicit projection class and registration evidence appropriate to the
claims being made.
"""

from __future__ import annotations

from typing import Any

import numpy as np


REFERENCE_CLASSES = {
    "ORTHOGRAPHIC_OR_NEAR_ORTHOGRAPHIC",
    "CALIBRATED_PERSPECTIVE",
    "SFM_REGISTERED_MULTIVIEW",
    "UNCALIBRATED_PERSPECTIVE_STYLE_ONLY",
}
GEOMETRY_CLASSES = REFERENCE_CLASSES - {"UNCALIBRATED_PERSPECTIVE_STYLE_ONLY"}
ALIGNMENT_MODES = {"STRICT_FRAME", "LANDMARK_SIMILARITY", "CAMERA_SOLUTION"}


def landmark_registration_error(pairs: list[dict[str, Any]], image_size: tuple[int, int]) -> dict[str, Any]:
    """Measure normalized residuals for already-corresponding 2D landmarks."""
    width, height = image_size
    if width <= 0 or height <= 0 or len(pairs) < 2:
        raise ValueError("landmark registration requires a positive image size and at least two pairs")
    residuals = []
    for pair in pairs:
        reference = np.asarray(pair.get("reference"), dtype=float)
        candidate = np.asarray(pair.get("candidate"), dtype=float)
        if reference.shape != (2,) or candidate.shape != (2,):
            raise ValueError("landmark pairs require two-dimensional reference and candidate points")
        residuals.append(float(np.linalg.norm((reference - candidate) / np.asarray((width, height)))))
    return {
        "pair_count": len(residuals),
        "mean_error_normalized": float(np.mean(residuals)),
        "max_error_normalized": float(np.max(residuals)),
    }


def evaluate_reference_registration(record: dict[str, Any]) -> dict[str, Any]:
    """Fail closed when a view's camera evidence cannot support its requested claims."""
    if not isinstance(record, dict) or record.get("schema_version") != 1:
        raise ValueError("reference registration must be a schema-version 1 object")
    views = record.get("views")
    if not isinstance(views, list) or not views:
        raise ValueError("reference registration requires at least one view")
    issues: list[str] = []
    authoritative_views: list[str] = []
    authorized_claims: dict[str, list[str]] = {}
    seen: set[str] = set()
    for view in views:
        if not isinstance(view, dict):
            raise ValueError("reference registration views must be objects")
        view_id = str(view.get("view_id") or "").strip().lower()
        if not view_id or view_id in seen:
            raise ValueError("reference registration view ids must be unique and non-empty")
        seen.add(view_id)
        classification = view.get("classification")
        alignment = view.get("alignment_mode")
        claims = view.get("requested_geometry_claims", [])
        if classification not in REFERENCE_CLASSES:
            issues.append(f"{view_id}: unknown reference classification")
            continue
        if alignment not in ALIGNMENT_MODES:
            issues.append(f"{view_id}: missing or unknown alignment mode")
            continue
        if not isinstance(claims, list) or any(not isinstance(item, str) or not item for item in claims):
            raise ValueError("requested_geometry_claims must be a list of non-empty strings")
        if classification == "UNCALIBRATED_PERSPECTIVE_STYLE_ONLY":
            if claims:
                issues.append(f"{view_id}: uncalibrated perspective is style-only and cannot authorize geometry claims")
            continue
        if classification == "ORTHOGRAPHIC_OR_NEAR_ORTHOGRAPHIC":
            if not str(view.get("projection_evidence") or "").strip():
                issues.append(f"{view_id}: orthographic classification lacks projection evidence")
                continue
            if alignment == "CAMERA_SOLUTION":
                issues.append(f"{view_id}: orthographic evidence should use strict-frame or landmark alignment")
                continue
        else:
            solution = view.get("camera_solution")
            if alignment != "CAMERA_SOLUTION" or not isinstance(solution, dict):
                issues.append(f"{view_id}: perspective geometry claims require a camera solution")
                continue
            if int(solution.get("control_point_count", 0)) < 4:
                issues.append(f"{view_id}: camera solution needs at least four control points")
                continue
            error = solution.get("reprojection_error_normalized")
            if not isinstance(error, (int, float)) or isinstance(error, bool) or not 0 <= float(error) <= 0.02:
                issues.append(f"{view_id}: camera reprojection error is missing or above 0.02")
                continue
            if classification == "SFM_REGISTERED_MULTIVIEW" and not bool(solution.get("same_physical_target_verified")):
                issues.append(f"{view_id}: SfM evidence does not verify the same physical target")
                continue
        authoritative_views.append(view_id)
        authorized_claims[view_id] = list(claims)
    requested = sum((view.get("requested_geometry_claims", []) for view in views if isinstance(view, dict)), [])
    return {
        "schema_version": 1,
        "record_type": "REFERENCE_REGISTRATION_GATE",
        "target_id": record.get("target_id"),
        "pass": not issues and (not requested or bool(authoritative_views)),
        "authoritative_views": authoritative_views,
        "authorized_geometry_claims": authorized_claims,
        "issues": issues,
        "claim_boundary": "This gate establishes projection/registration suitability only; it does not prove segmentation, geometry correctness, or professional quality.",
    }
