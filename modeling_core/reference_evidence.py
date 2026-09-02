"""Deterministic first-pass evidence extraction for isolated reference images.

This module intentionally handles only references with a separable border background or a useful
alpha channel.  It fails closed on ambiguous photographs instead of manufacturing a confident
silhouette.  A human- or model-edited mask can replace the generated mask while preserving the
source hash and measurement contract.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def _border_pixels(image: np.ndarray) -> np.ndarray:
    top, bottom = image[0], image[-1]
    left, right = image[1:-1, 0], image[1:-1, -1]
    return np.concatenate((top, bottom, left, right), axis=0)


def _component_cleanup(mask: np.ndarray, minimum_area: int) -> tuple[np.ndarray, dict[str, Any]]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    components = []
    for label in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[label])
        if area >= minimum_area:
            components.append({"label": label, "area": area, "bbox": [x, y, width, height]})
    if not components:
        return np.zeros_like(mask, dtype=bool), {"retained": [], "discarded_count": count - 1}
    largest = max(item["area"] for item in components)
    retained = [item for item in components if item["area"] >= max(minimum_area, round(largest * 0.01))]
    cleaned = np.isin(labels, [item["label"] for item in retained])
    return cleaned, {"retained": retained, "discarded_count": count - 1 - len(retained)}


def _extract_mask(image: np.ndarray, *, method: str, background_tolerance: float | None) -> tuple[np.ndarray, dict[str, Any]]:
    if method not in {"auto", "alpha", "border"}:
        raise ValueError("method must be auto, alpha, or border")
    alpha = image[:, :, 3] if image.shape[2] == 4 else None
    useful_alpha = alpha is not None and int(alpha.min()) != int(alpha.max())
    if method == "alpha" and not useful_alpha:
        raise ValueError("alpha extraction requested but the image has no varying alpha channel")
    if method == "alpha" or (method == "auto" and useful_alpha):
        mask = alpha >= 128
        return mask, {
            "method": "alpha",
            "threshold": 128,
            "background_model": None,
            "border_color_spread": None,
        }

    bgr = image[:, :, :3]
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    border = _border_pixels(lab)
    background = np.median(border, axis=0)
    distances = np.linalg.norm(lab - background, axis=2)
    border_distances = np.linalg.norm(border - background, axis=1)
    spread = float(np.percentile(border_distances, 95))
    tolerance = float(background_tolerance) if background_tolerance is not None else max(10.0, spread * 2.5 + 4.0)
    if tolerance <= 0:
        raise ValueError("background_tolerance must be positive")
    return distances > tolerance, {
        "method": "border_lab_distance",
        "threshold": tolerance,
        "background_model": [round(float(value), 4) for value in background],
        "border_color_spread": spread,
    }


def _holes(mask: np.ndarray) -> tuple[int, int]:
    inverse = (~mask).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(inverse, connectivity=8)
    border_labels = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
    holes = [label for label in range(1, count) if label not in border_labels]
    return len(holes), sum(int(stats[label, cv2.CC_STAT_AREA]) for label in holes)


def analyze_reference_mask(mask: np.ndarray) -> dict[str, Any]:
    """Measure a foreground mask in normalized full-image coordinates."""
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2 or not mask.any():
        raise ValueError("reference mask must be a non-empty 2D array")
    height, width = mask.shape
    ys, xs = np.where(mask)
    left, top, right, bottom = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    bbox_width, bbox_height = right - left + 1, bottom - top + 1
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    largest_contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(largest_contour, True)
    approximation = cv2.approxPolyDP(largest_contour, max(1.0, perimeter * 0.005), True).reshape(-1, 2)
    moments = cv2.moments(mask.astype(np.uint8), binaryImage=True)
    centroid = [moments["m10"] / moments["m00"] / width, moments["m01"] / moments["m00"] / height]
    samples = []
    for fraction in np.linspace(0.0, 1.0, 33):
        row = min(bottom, top + round(fraction * max(0, bbox_height - 1)))
        row_x = np.where(mask[row])[0]
        samples.append({
            "position": round(float(fraction), 6),
            "left": round(float((row_x.min() - left) / bbox_width), 6) if len(row_x) else None,
            "right": round(float((row_x.max() - left + 1) / bbox_width), 6) if len(row_x) else None,
            "width": round(float((row_x.max() - row_x.min() + 1) / bbox_width), 6) if len(row_x) else 0.0,
        })
    hole_count, hole_pixels = _holes(mask)
    return {
        "image_size": [width, height],
        "bbox_pixels": [left, top, right + 1, bottom + 1],
        "bbox_normalized": [left / width, top / height, (right + 1) / width, (bottom + 1) / height],
        "aspect_ratio_width_over_height": bbox_width / bbox_height,
        "centroid_normalized": centroid,
        "extrema_normalized": {
            "top": [float(xs[ys.argmin()] / width), float(top / height)],
            "bottom": [float(xs[ys.argmax()] / width), float((bottom + 1) / height)],
            "left": [float(left / width), float(ys[xs.argmin()] / height)],
            "right": [float((right + 1) / width), float(ys[xs.argmax()] / height)],
        },
        "outline_landmarks_normalized": [[float(x / width), float(y / height)] for x, y in approximation],
        "row_profile": samples,
        "enclosed_negative_space_count": hole_count,
        "enclosed_negative_space_fraction": hole_pixels / (width * height),
    }


def extract_reference_evidence(
    image_path: str | Path,
    output_directory: str | Path,
    *,
    method: str = "auto",
    background_tolerance: float | None = None,
    crop_padding_fraction: float = 0.08,
    mask_override: str | Path | None = None,
) -> dict[str, Any]:
    """Extract auditable image evidence and materialize editable artifacts.

    The generated mask is a proposal, never ground truth.  `accepted_for_fitting` is false when
    border leakage, foreground extent, fragmentation, or background ambiguity makes it unsafe.
    """
    source = Path(image_path).resolve()
    destination = Path(output_directory).resolve()
    if not source.is_file():
        raise ValueError(f"reference image does not exist: {source}")
    if not 0.0 <= crop_padding_fraction <= 0.5:
        raise ValueError("crop_padding_fraction must be between 0 and 0.5")
    image = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
    if image is None or image.ndim not in {2, 3}:
        raise ValueError(f"OpenCV could not decode reference image: {source}")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    elif image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    elif image.shape[2] != 4:
        raise ValueError("reference image must have one, three, or four channels")

    override_source = None
    if mask_override is not None:
        override_source = Path(mask_override).resolve()
        override = cv2.imread(str(override_source), cv2.IMREAD_GRAYSCALE)
        if override is None:
            raise ValueError(f"OpenCV could not decode mask override: {override_source}")
        if override.shape != image.shape[:2]:
            raise ValueError("mask override dimensions must match the source image")
        raw_mask = override >= 128
        extraction = {
            "method": "manual_mask_override",
            "threshold": 128,
            "background_model": None,
            "border_color_spread": None,
            "override_path": str(override_source),
            "override_sha256": hashlib.sha256(override_source.read_bytes()).hexdigest(),
        }
    else:
        raw_mask, extraction = _extract_mask(image, method=method, background_tolerance=background_tolerance)
    height, width = raw_mask.shape
    minimum_area = max(4, round(width * height * 0.0001))
    mask, component_report = _component_cleanup(raw_mask, minimum_area)
    if not mask.any():
        raise ValueError("reference extraction produced no usable foreground")

    foreground_fraction = float(mask.mean())
    border_fraction = float(_border_pixels(mask[:, :, None]).mean())
    retained = component_report["retained"]
    largest_fraction = max(item["area"] for item in retained) / max(1, int(mask.sum()))
    issues = []
    if not 0.003 <= foreground_fraction <= 0.90:
        issues.append("foreground fraction is implausible for an isolated-object reference")
    if border_fraction > 0.02:
        issues.append("foreground leaks into the image border")
    if largest_fraction < 0.70:
        issues.append("foreground is strongly fragmented")
    if extraction["method"] == "border_lab_distance" and extraction["border_color_spread"] > 18.0:
        issues.append("border background is too variable for reliable automatic subtraction")

    measurements = analyze_reference_mask(mask)
    left, top, right, bottom = measurements["bbox_pixels"]
    pad_x = round((right - left) * crop_padding_fraction)
    pad_y = round((bottom - top) * crop_padding_fraction)
    crop_box = [max(0, left - pad_x), max(0, top - pad_y), min(width, right + pad_x), min(height, bottom + pad_y)]
    crop_left, crop_top, crop_right, crop_bottom = crop_box
    crop_image = image[crop_top:crop_bottom, crop_left:crop_right]
    crop_mask = mask[crop_top:crop_bottom, crop_left:crop_right]

    destination.mkdir(parents=True, exist_ok=True)
    mask_path = destination / "reference_mask.png"
    normalized_path = destination / "reference_normalized.png"
    normalized_mask_path = destination / "reference_normalized_mask.png"
    preview_path = destination / "reference_evidence_preview.png"
    cv2.imwrite(str(mask_path), mask.astype(np.uint8) * 255)
    cv2.imwrite(str(normalized_path), crop_image)
    cv2.imwrite(str(normalized_mask_path), crop_mask.astype(np.uint8) * 255)
    preview = image[:, :, :3].copy()
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(preview, contours, -1, (0, 0, 255), max(1, round(max(width, height) / 500)))
    cv2.rectangle(preview, (crop_left, crop_top), (crop_right - 1, crop_bottom - 1), (0, 255, 0), 1)
    cv2.imwrite(str(preview_path), preview)

    report = {
        "schema_version": 1,
        "record_type": "REFERENCE_IMAGE_EVIDENCE",
        "source": {
            "path": str(source),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "image_size": [width, height],
        },
        "extraction": {
            **extraction,
            "foreground_fraction": foreground_fraction,
            "border_foreground_fraction": border_fraction,
            "largest_component_fraction": largest_fraction,
            "components": component_report,
        },
        "measurements": measurements,
        "normalization": {"crop_box_pixels": crop_box, "padding_fraction": crop_padding_fraction},
        "artifacts": {
            "editable_mask": str(mask_path),
            "normalized_image": str(normalized_path),
            "normalized_mask": str(normalized_mask_path),
            "preview": str(preview_path),
        },
        "artifact_sha256": {
            "editable_mask": hashlib.sha256(mask_path.read_bytes()).hexdigest(),
            "normalized_image": hashlib.sha256(normalized_path.read_bytes()).hexdigest(),
            "normalized_mask": hashlib.sha256(normalized_mask_path.read_bytes()).hexdigest(),
            "preview": hashlib.sha256(preview_path.read_bytes()).hexdigest(),
        },
        "accepted_for_fitting": not issues,
        "issues": issues,
        "manual_correction": {
            "allowed": True,
            "applied": override_source is not None,
            "instruction": "Edit reference_mask.png and rerun extract-reference with --mask-override; source and override hashes will remain in the evidence record.",
        },
        "claim_boundary": "Automatic extraction is a deterministic proposal for separable backgrounds. It does not identify semantic components, infer hidden geometry, or prove visual correctness.",
    }
    report_path = destination / "reference_evidence.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
