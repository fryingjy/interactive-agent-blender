"""Bind editable semantic component labels to one extracted reference mask."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .reference_evidence import analyze_reference_mask


def _load_report(value: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return json.loads(Path(value).read_text(encoding="utf-8"))


def extract_component_evidence(
    reference_evidence: dict[str, Any] | str | Path,
    label_map_path: str | Path,
    components: list[dict[str, Any]],
    *,
    minimum_foreground_coverage: float = 0.95,
    maximum_background_leakage: float = 0.01,
) -> dict[str, Any]:
    """Measure a grayscale semantic label map against its source silhouette.

    Label zero is background.  Every declared component owns one integer label from 1 through 255.
    Labels are editable evidence, not automatically inferred semantic truth.
    """
    report = _load_report(reference_evidence)
    if report.get("record_type") != "REFERENCE_IMAGE_EVIDENCE":
        raise ValueError("component evidence requires a REFERENCE_IMAGE_EVIDENCE record")
    if not report.get("accepted_for_fitting"):
        raise ValueError("component evidence requires an accepted source extraction")
    if not 0.0 < minimum_foreground_coverage <= 1.0:
        raise ValueError("minimum_foreground_coverage must be in (0, 1]")
    if not 0.0 <= maximum_background_leakage < 1.0:
        raise ValueError("maximum_background_leakage must be in [0, 1)")
    if not components:
        raise ValueError("at least one semantic component is required")

    ids = [str(item.get("id") or "").strip() for item in components]
    labels = [item.get("label") for item in components]
    if any(not identifier for identifier in ids) or len(ids) != len(set(ids)):
        raise ValueError("component ids must be unique and non-empty")
    if any(not isinstance(label, int) or isinstance(label, bool) or not 1 <= label <= 255 for label in labels):
        raise ValueError("component labels must be integers from 1 through 255")
    if len(labels) != len(set(labels)):
        raise ValueError("component labels must be unique")

    source_path = Path(report["source"]["path"])
    if not source_path.is_file() or hashlib.sha256(source_path.read_bytes()).hexdigest() != report["source"]["sha256"]:
        raise ValueError("source image no longer matches its evidence hash")
    mask_path = Path(report["artifacts"]["editable_mask"])
    expected_mask_hash = report.get("artifact_sha256", {}).get("editable_mask")
    if not mask_path.is_file() or hashlib.sha256(mask_path.read_bytes()).hexdigest() != expected_mask_hash:
        raise ValueError("editable source mask no longer matches its evidence hash")
    source_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    label_path = Path(label_map_path).resolve()
    label_map = cv2.imread(str(label_path), cv2.IMREAD_GRAYSCALE)
    if source_mask is None or label_map is None:
        raise ValueError("source mask and component label map must be decodable grayscale images")
    if source_mask.shape != label_map.shape:
        raise ValueError("component label map dimensions must match the source mask")
    foreground = source_mask >= 128
    if not foreground.any():
        raise ValueError("source silhouette is empty")

    known_labels = set(labels)
    observed_labels = set(int(value) for value in np.unique(label_map) if value)
    unknown_labels = sorted(observed_labels - known_labels)
    labeled = label_map > 0
    covered = int(np.logical_and(labeled, foreground).sum())
    leaked = int(np.logical_and(labeled, ~foreground).sum())
    coverage = covered / int(foreground.sum())
    leakage = leaked / max(1, int(labeled.sum()))

    observations: dict[str, Any] = {}
    missing = []
    component_masks: dict[str, np.ndarray] = {}
    for specification, identifier, label in zip(components, ids, labels):
        component_mask = (label_map == label) & foreground
        if not component_mask.any():
            missing.append(identifier)
            continue
        component_masks[identifier] = component_mask
        measurement = analyze_reference_mask(component_mask)
        observations[identifier] = {
            "label": label,
            "role": specification.get("role", "UNSPECIFIED"),
            "continuity_policy": specification.get("continuity_policy", "UNRESOLVED"),
            "visible_area_fraction_of_object": float(component_mask.sum() / foreground.sum()),
            "measurements": measurement,
        }

    adjacency = []
    kernel = np.ones((3, 3), dtype=np.uint8)
    available = sorted(component_masks)
    for index, first in enumerate(available):
        expanded = cv2.dilate(component_masks[first].astype(np.uint8), kernel, iterations=1).astype(bool)
        for second in available[index + 1:]:
            if np.logical_and(expanded, component_masks[second]).any():
                adjacency.append([first, second])

    issues = []
    if unknown_labels:
        issues.append(f"undeclared labels are present: {unknown_labels}")
    if missing:
        issues.append(f"declared components have no visible pixels: {missing}")
    if coverage < minimum_foreground_coverage:
        issues.append(f"component labels cover only {coverage:.4f} of the object silhouette")
    if leakage > maximum_background_leakage:
        issues.append(f"component labels leak {leakage:.4f} into the background")
    return {
        "schema_version": 1,
        "record_type": "REFERENCE_COMPONENT_EVIDENCE",
        "source_reference_sha256": report["source"]["sha256"],
        "source_mask_path": str(mask_path.resolve()),
        "source_mask_sha256": expected_mask_hash,
        "label_map": {
            "path": str(label_path),
            "sha256": hashlib.sha256(label_path.read_bytes()).hexdigest(),
            "background_label": 0,
        },
        "component_ids": ids,
        "observations": observations,
        "visible_adjacency": adjacency,
        "foreground_coverage": coverage,
        "background_leakage": leakage,
        "unknown_labels": unknown_labels,
        "missing_component_ids": missing,
        "accepted_for_bundle": not issues,
        "issues": issues,
        "claim_boundary": "The label map records visible semantic regions and adjacency in one view. It does not prove hidden extent, physical continuity, occlusion order, or cross-view identity.",
    }
