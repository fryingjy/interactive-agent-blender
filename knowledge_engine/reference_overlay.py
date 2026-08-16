"""Reusable reference-to-render masking, alignment, overlays, and mismatch evidence.

Alignment is always explicit. ``strict`` preserves the supplied frame. ``uniform-bbox`` translates
and uniformly scales the candidate while preserving its aspect ratio. ``bbox`` independently
stretches both axes and is retained only as an explicitly limited contour-shape diagnostic.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .visual_compare import compare_masks, make_reference_tickets


def foreground_mask(
    path: str | Path,
    *,
    mode: str = "auto",
    light_background_threshold: int = 240,
    alpha_threshold: int = 1,
    luminance_min: int = 0,
    luminance_max: int = 255,
) -> np.ndarray:
    """Load a foreground mask without silently assuming alpha is meaningful."""
    image = np.asarray(Image.open(path).convert("RGBA"))
    alpha = image[..., 3]
    clean_mode = str(mode).strip().lower()
    if clean_mode not in {"auto", "alpha", "light-background", "luminance-range"}:
        raise ValueError("mask mode must be auto, alpha, light-background, or luminance-range")
    has_transparency = bool(np.any(alpha < 255))
    if clean_mode == "alpha" or (clean_mode == "auto" and has_transparency):
        mask = alpha >= int(alpha_threshold)
    elif clean_mode == "luminance-range":
        luminance = cv2.cvtColor(image[..., :3], cv2.COLOR_RGB2GRAY)
        mask = (luminance >= int(luminance_min)) & (luminance <= int(luminance_max))
    else:
        rgb = image[..., :3]
        mask = ~np.all(rgb > int(light_background_threshold), axis=2)
    if not np.any(mask):
        raise ValueError(f"foreground mask is empty: {Path(path)}")
    return mask


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError("cannot align an empty mask")
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def align_candidate(reference: np.ndarray, candidate: np.ndarray, mode: str) -> tuple[np.ndarray, dict]:
    """Return a candidate mask in the reference frame plus explicit alignment provenance."""
    clean_mode = str(mode).strip().lower()
    if clean_mode not in {"strict", "uniform-bbox", "bbox"}:
        raise ValueError("alignment mode must be strict, uniform-bbox, or bbox")
    if clean_mode == "strict":
        if reference.shape != candidate.shape:
            raise ValueError(
                f"strict alignment requires equal image shapes: {reference.shape} vs {candidate.shape}"
            )
        return candidate.copy(), {
            "mode": "strict",
            "normalization": "none",
            "claim_boundary": "Placement, scale, silhouette, contour, and negative space remain measurable in the supplied frame.",
        }

    rx0, ry0, rx1, ry1 = _bbox(reference)
    cx0, cy0, cx1, cy1 = _bbox(candidate)
    crop = Image.fromarray(
        (candidate[cy0 : cy1 + 1, cx0 : cx1 + 1] * 255).astype(np.uint8), "L"
    )
    if clean_mode == "uniform-bbox":
        reference_width = rx1 - rx0 + 1
        reference_height = ry1 - ry0 + 1
        candidate_width = cx1 - cx0 + 1
        candidate_height = cy1 - cy0 + 1
        scale = min(reference_width / candidate_width, reference_height / candidate_height)
        target_width = max(1, int(round(candidate_width * scale)))
        target_height = max(1, int(round(candidate_height * scale)))
        resized = np.asarray(
            crop.resize((target_width, target_height), Image.Resampling.NEAREST)
        ) > 0
        reference_center_x = (rx0 + rx1) * 0.5
        reference_center_y = (ry0 + ry1) * 0.5
        target_x0 = int(round(reference_center_x - (target_width - 1) * 0.5))
        target_y0 = int(round(reference_center_y - (target_height - 1) * 0.5))
        target_x1 = target_x0 + target_width
        target_y1 = target_y0 + target_height
        aligned = np.zeros_like(reference, dtype=bool)
        aligned[target_y0:target_y1, target_x0:target_x1] = resized
        return aligned, {
            "mode": "uniform-bbox",
            "normalization": "candidate foreground cropped, uniformly scaled to fit the reference foreground bounding box, and center-aligned",
            "uniform_scale": float(scale),
            "reference_bbox": [rx0, ry0, rx1, ry1],
            "candidate_bbox_before_alignment": [cx0, cy0, cx1, cy1],
            "candidate_bbox_after_alignment": [target_x0, target_y0, target_x1 - 1, target_y1 - 1],
            "claim_boundary": "Translation and overall scale were removed, but aspect ratio and contour differences remain measurable.",
        }
    resized = np.asarray(
        crop.resize((rx1 - rx0 + 1, ry1 - ry0 + 1), Image.Resampling.NEAREST)
    ) > 0
    aligned = np.zeros_like(reference, dtype=bool)
    aligned[ry0 : ry1 + 1, rx0 : rx1 + 1] = resized
    return aligned, {
        "mode": "bbox",
        "normalization": "candidate foreground cropped and independently resized into the reference foreground bounding box",
        "reference_bbox": [rx0, ry0, rx1, ry1],
        "candidate_bbox_before_alignment": [cx0, cy0, cx1, cy1],
        "claim_boundary": "Translation and bounding-box scale errors were removed; use only for normalized shape comparison, never placement or absolute proportion claims.",
    }


def overlay_pixels(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    """White=agreement, red=missing candidate, cyan=extra candidate, dark=background."""
    if reference.shape != candidate.shape:
        raise ValueError("overlay masks must have the same shape")
    pixels = np.full((*reference.shape, 3), 18, dtype=np.uint8)
    pixels[reference & ~candidate] = (235, 70, 70)
    pixels[candidate & ~reference] = (55, 210, 235)
    pixels[reference & candidate] = (240, 240, 240)
    return pixels


def contour_error_pixels(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    """Heatmap of distance from each mismatched foreground pixel to the opposing mask."""
    reference = reference.astype(bool)
    candidate = candidate.astype(bool)
    ref_distance = cv2.distanceTransform((~reference).astype(np.uint8), cv2.DIST_L2, 3)
    cand_distance = cv2.distanceTransform((~candidate).astype(np.uint8), cv2.DIST_L2, 3)
    error = np.zeros(reference.shape, dtype=np.float32)
    error[reference & ~candidate] = cand_distance[reference & ~candidate]
    error[candidate & ~reference] = ref_distance[candidate & ~reference]
    maximum = float(error.max())
    normalized = np.zeros_like(error, dtype=np.uint8) if maximum == 0 else np.clip(error / maximum * 255, 0, 255).astype(np.uint8)
    return cv2.applyColorMap(normalized, cv2.COLORMAP_INFERNO)[..., ::-1]


def save_mask(mask: np.ndarray, path: str | Path) -> None:
    rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = mask.astype(np.uint8) * 255
    Image.fromarray(rgba, "RGBA").save(path)


def compare_reference_render(
    reference_path: str | Path,
    candidate_path: str | Path,
    *,
    alignment: str = "strict",
    reference_mask_mode: str = "auto",
    candidate_mask_mode: str = "auto",
    light_background_threshold: int = 240,
    reference_luminance_min: int = 0,
    reference_luminance_max: int = 255,
    candidate_luminance_min: int = 0,
    candidate_luminance_max: int = 255,
    reference_roi: tuple[int, int, int, int] | None = None,
    candidate_roi: tuple[int, int, int, int] | None = None,
    view: str = "unknown",
) -> tuple[dict, dict[str, np.ndarray]]:
    reference = foreground_mask(
        reference_path,
        mode=reference_mask_mode,
        light_background_threshold=light_background_threshold,
        luminance_min=reference_luminance_min,
        luminance_max=reference_luminance_max,
    )
    candidate = foreground_mask(
        candidate_path,
        mode=candidate_mask_mode,
        light_background_threshold=light_background_threshold,
        luminance_min=candidate_luminance_min,
        luminance_max=candidate_luminance_max,
    )
    if reference_roi is not None:
        x0, y0, x1, y1 = (int(value) for value in reference_roi)
        reference = reference[y0:y1, x0:x1]
    if candidate_roi is not None:
        x0, y0, x1, y1 = (int(value) for value in candidate_roi)
        candidate = candidate[y0:y1, x0:x1]
    if not np.any(reference) or not np.any(candidate):
        raise ValueError("ROI produced an empty reference or candidate mask")
    aligned, alignment_record = align_candidate(reference, candidate, alignment)
    metrics = compare_masks(reference, aligned)
    report = {
        "schema_version": 1,
        "record_type": "REFERENCE_RENDER_COMPARISON",
        "reference": str(Path(reference_path).resolve()),
        "candidate": str(Path(candidate_path).resolve()),
        "view": view,
        "reference_roi_xyxy_exclusive": list(reference_roi) if reference_roi is not None else None,
        "candidate_roi_xyxy_exclusive": list(candidate_roi) if candidate_roi is not None else None,
        "alignment": alignment_record,
        "metrics": metrics,
        "tickets": make_reference_tickets(metrics, view=view),
    }
    images = {
        "reference_mask": reference,
        "candidate_mask_aligned": aligned,
        "overlay": overlay_pixels(reference, aligned),
        "contour_error_heatmap": contour_error_pixels(reference, aligned),
    }
    return report, images
