"""Reference-mask comparison for silhouette, contour, and multi-view checks."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def load_mask(path: str | Path, alpha_threshold: int = 1) -> np.ndarray:
    image = np.asarray(Image.open(path).convert("RGBA"))
    alpha = image[..., 3]
    if np.any(alpha < 255):
        return alpha >= alpha_threshold
    luminance = cv2.cvtColor(image[..., :3], cv2.COLOR_RGB2GRAY)
    return luminance < 250


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _centroid(mask: np.ndarray) -> tuple[float, float] | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return float(xs.mean()), float(ys.mean())


def _contour(mask: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return np.empty((0, 2), dtype=np.float32)
    return np.concatenate([item[:, 0, :] for item in contours], axis=0).astype(np.float32)


def negative_space_mask(mask: np.ndarray) -> np.ndarray:
    """Return enclosed background regions inside the silhouette's bounding box.

    Background connected to the bounding-box border is exterior; remaining components are holes or
    enclosed negative spaces. This intentionally does not infer semantic gaps outside the outer
    contour (for example, spacing between two separate components).
    """
    mask = mask.astype(bool)
    bbox = _bbox(mask)
    result = np.zeros_like(mask, dtype=bool)
    if bbox is None:
        return result
    x0, y0, x1, y1 = bbox
    crop = mask[y0 : y1 + 1, x0 : x1 + 1]
    background = (~crop).astype(np.uint8)
    count, labels = cv2.connectedComponents(background, connectivity=8)
    border_labels = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    enclosed = np.zeros_like(crop, dtype=bool)
    for label in range(1, count):
        if label not in border_labels:
            enclosed |= labels == label
    result[y0 : y1 + 1, x0 : x1 + 1] = enclosed
    return result


def _directed_contour_distance(source: np.ndarray, target_mask: np.ndarray) -> float | None:
    if not len(source) or not np.any(target_mask):
        return None
    target_points = _contour(target_mask)
    if not len(target_points):
        return None
    target_edge = np.zeros_like(target_mask, dtype=bool)
    target_edge[target_points[:, 1].astype(int), target_points[:, 0].astype(int)] = True
    distance = cv2.distanceTransform((~target_edge).astype(np.uint8), cv2.DIST_L2, 3)
    xs = np.clip(source[:, 0].astype(int), 0, distance.shape[1] - 1)
    ys = np.clip(source[:, 1].astype(int), 0, distance.shape[0] - 1)
    return float(distance[ys, xs].mean())


def compare_masks(reference: np.ndarray, candidate: np.ndarray) -> dict:
    if reference.shape != candidate.shape:
        raise ValueError(f"mask shapes differ: {reference.shape} vs {candidate.shape}")
    reference = reference.astype(bool)
    candidate = candidate.astype(bool)
    union = np.logical_or(reference, candidate).sum()
    intersection = np.logical_and(reference, candidate).sum()
    diagonal = float(np.hypot(*reference.shape))
    reference_centroid = _centroid(reference)
    candidate_centroid = _centroid(candidate)
    centroid_error = None
    if reference_centroid and candidate_centroid:
        centroid_error = float(np.linalg.norm(np.subtract(reference_centroid, candidate_centroid)) / diagonal)
    reference_bbox = _bbox(reference)
    candidate_bbox = _bbox(candidate)
    bbox_error = None
    if reference_bbox and candidate_bbox:
        bbox_error = float(np.mean(np.abs(np.subtract(reference_bbox, candidate_bbox))) / diagonal)
    reference_contour = _contour(reference)
    candidate_contour = _contour(candidate)
    forward = _directed_contour_distance(candidate_contour, reference)
    backward = _directed_contour_distance(reference_contour, candidate)
    contour_error = None if forward is None or backward is None else (forward + backward) * 0.5 / diagonal
    reference_negative = negative_space_mask(reference)
    candidate_negative = negative_space_mask(candidate)
    negative_union = np.logical_or(reference_negative, candidate_negative).sum()
    negative_intersection = np.logical_and(reference_negative, candidate_negative).sum()
    return {
        "width": int(reference.shape[1]),
        "height": int(reference.shape[0]),
        "reference_pixels": int(reference.sum()),
        "candidate_pixels": int(candidate.sum()),
        "silhouette_iou": float(intersection / union) if union else 1.0,
        "centroid_error_normalized": centroid_error,
        "bounding_box_error_normalized": bbox_error,
        "symmetric_contour_error_normalized": contour_error,
        "negative_space_iou": float(negative_intersection / negative_union) if negative_union else 1.0,
        "reference_negative_space_pixels": int(reference_negative.sum()),
        "candidate_negative_space_pixels": int(candidate_negative.sum()),
        "reference_bbox": reference_bbox,
        "candidate_bbox": candidate_bbox,
    }


def compare_landmarks(
    reference: dict[str, tuple[float, float]],
    candidate: dict[str, tuple[float, float]],
    image_shape: tuple[int, int],
) -> dict:
    """Compare named pixel-space landmarks with image-diagonal normalization."""
    missing = sorted(set(reference) - set(candidate))
    extra = sorted(set(candidate) - set(reference))
    diagonal = float(np.hypot(*image_shape))
    errors = {
        name: float(np.linalg.norm(np.subtract(reference[name], candidate[name])) / diagonal)
        for name in sorted(set(reference) & set(candidate))
    }
    return {
        "errors_normalized": errors,
        "mean_error_normalized": float(np.mean(list(errors.values()))) if errors else None,
        "max_error_normalized": max(errors.values(), default=None),
        "missing_landmarks": missing,
        "extra_landmarks": extra,
        "pass": not missing,
    }


def compare_component_masks(reference: dict[str, np.ndarray], candidate: dict[str, np.ndarray]) -> dict:
    """Compare semantic component masks independently so global overlap cannot hide placement errors."""
    missing = sorted(set(reference) - set(candidate))
    extra = sorted(set(candidate) - set(reference))
    components = {
        name: compare_masks(reference[name], candidate[name])
        for name in sorted(set(reference) & set(candidate))
    }
    return {
        "components": components,
        "mean_component_iou": float(np.mean([item["silhouette_iou"] for item in components.values()])) if components else None,
        "worst_component_iou": min((item["silhouette_iou"] for item in components.values()), default=None),
        "missing_components": missing,
        "extra_components": extra,
        "pass": not missing,
    }


def compare_image_files(reference_path: str | Path, candidate_path: str | Path) -> dict:
    return compare_masks(load_mask(reference_path), load_mask(candidate_path))


def compare_views(view_pairs: dict[str, tuple[str | Path, str | Path]]) -> dict:
    views = {name: compare_image_files(reference, candidate) for name, (reference, candidate) in view_pairs.items()}
    return {
        "views": views,
        "mean_iou": float(np.mean([item["silhouette_iou"] for item in views.values()])) if views else None,
        "worst_view_iou": min((item["silhouette_iou"] for item in views.values()), default=None),
        "mean_contour_error_normalized": float(np.mean([item["symmetric_contour_error_normalized"] for item in views.values() if item["symmetric_contour_error_normalized"] is not None])) if views else None,
    }
