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


def _directed_contour_distance(source: np.ndarray, target_mask: np.ndarray) -> float | None:
    if not len(source) or not np.any(target_mask):
        return None
    target_edge = cv2.Canny(target_mask.astype(np.uint8) * 255, 1, 2) > 0
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
    return {
        "width": int(reference.shape[1]),
        "height": int(reference.shape[0]),
        "reference_pixels": int(reference.sum()),
        "candidate_pixels": int(candidate.sum()),
        "silhouette_iou": float(intersection / union) if union else 1.0,
        "centroid_error_normalized": centroid_error,
        "bounding_box_error_normalized": bbox_error,
        "symmetric_contour_error_normalized": contour_error,
        "reference_bbox": reference_bbox,
        "candidate_bbox": candidate_bbox,
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
