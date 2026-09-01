"""Deterministic mask-quality checks required before silhouette scoring."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from .visual_compare import negative_space_mask


def audit_segmentation_mask(
    mask: np.ndarray,
    *,
    expected_component_range: tuple[int, int] = (1, 1),
    expected_hole_range: tuple[int, int] | None = None,
    min_foreground_fraction: float = 0.01,
    max_foreground_fraction: float = 0.95,
    allow_border_touch: bool = False,
) -> dict[str, Any]:
    """Audit polarity, coverage, components, and enclosed negative space."""
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2 or mask.size == 0:
        raise ValueError("segmentation mask must be a non-empty 2D array")
    low_components, high_components = expected_component_range
    if low_components < 1 or high_components < low_components:
        raise ValueError("expected_component_range is invalid")
    foreground_fraction = float(mask.mean())
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    areas = sorted((int(stats[index, cv2.CC_STAT_AREA]) for index in range(1, count)), reverse=True)
    component_count = len(areas)
    enclosed = negative_space_mask(mask)
    hole_count = max(0, cv2.connectedComponents(enclosed.astype(np.uint8), connectivity=8)[0] - 1)
    touches = bool(mask[0].any() or mask[-1].any() or mask[:, 0].any() or mask[:, -1].any())
    issues: list[str] = []
    if not min_foreground_fraction <= foreground_fraction <= max_foreground_fraction:
        issues.append("foreground fraction suggests empty/full polarity or a failed crop")
    if not low_components <= component_count <= high_components:
        issues.append(f"connected component count {component_count} is outside [{low_components}, {high_components}]")
    if expected_hole_range is not None:
        low_holes, high_holes = expected_hole_range
        if low_holes < 0 or high_holes < low_holes:
            raise ValueError("expected_hole_range is invalid")
        if not low_holes <= hole_count <= high_holes:
            issues.append(f"enclosed negative-space count {hole_count} is outside [{low_holes}, {high_holes}]")
    if touches and not allow_border_touch:
        issues.append("foreground touches the image border; crop or polarity may be invalid")
    dominance = 0.0 if not areas else areas[0] / max(sum(areas), 1)
    return {
        "schema_version": 1,
        "record_type": "SEGMENTATION_MASK_AUDIT",
        "pass": not issues,
        "shape_hw": [int(mask.shape[0]), int(mask.shape[1])],
        "foreground_fraction": foreground_fraction,
        "component_count": component_count,
        "component_areas_px": areas,
        "largest_component_fraction": dominance,
        "enclosed_negative_space_count": hole_count,
        "enclosed_negative_space_pixels": int(enclosed.sum()),
        "touches_border": touches,
        "issues": issues,
        "claim_boundary": "A passing mask audit establishes extraction integrity, not semantic component labels or model fidelity.",
    }
