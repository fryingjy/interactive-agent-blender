"""Extract normalized component bounds from a controlled Blender mask pass."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


_PALETTE = np.asarray(((1.0, 0.1, 0.1), (0.1, 1.0, 0.1), (0.1, 0.1, 1.0), (1.0, 1.0, 0.1)), dtype=np.float32)
_DEFAULT_PALETTE_TOLERANCES = np.asarray((0.55, 0.8, 0.55, 0.55), dtype=np.float32)


def extract_component_mask_observations(image_path: str | Path, component_ids: list[str], *, max_color_distance: float | None = None) -> dict[str, Any]:
    """Return component bounding boxes normalized to the combined foreground.

    The input must be a `render_diagnostic_pass(..., pass_type="component_mask")`
    image using no more than four listed components; that render assigns the
    stable red/green/blue/yellow palette declared here.  Blender's display
    transform shifts those object colors in the saved PNG. The default
    per-color tolerances are calibrated against actual Workbench output (the
    green handle needs more latitude) while still assigning every foreground
    pixel to its nearest palette color.
    Bounds are normalized
    to the full combined foreground box, making them independent of render
    resolution and orthographic margin but *not* a substitute for explicitly
    registered reference-camera alignment.
    """
    if not component_ids or len(component_ids) > len(_PALETTE):
        raise ValueError("component_ids must contain between one and four unique entries")
    if len(set(component_ids)) != len(component_ids):
        raise ValueError("component_ids must be unique")
    if max_color_distance is not None and not 0 < max_color_distance <= 2:
        raise ValueError("max_color_distance must be in (0, 2]")
    pixels = np.asarray(Image.open(image_path).convert("RGBA"), dtype=np.float32) / 255.0
    alpha = pixels[..., 3] > 0.5
    if not np.any(alpha):
        raise ValueError("component-mask image has no foreground alpha")
    ys, xs = np.nonzero(alpha)
    left, top, right, bottom = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    frame_width, frame_height = max(right - left, 1), max(bottom - top, 1)
    rgb = pixels[..., :3]
    distances = np.linalg.norm(rgb[..., None, :] - _PALETTE[None, None, :, :], axis=3)
    nearest = distances.argmin(axis=2)
    nearest_distance = distances.min(axis=2)
    tolerances = np.full(len(_PALETTE), max_color_distance, dtype=np.float32) if max_color_distance is not None else _DEFAULT_PALETTE_TOLERANCES
    observations: dict[str, Any] = {}
    missing: list[str] = []
    for index, component_id in enumerate(component_ids):
        component = alpha & (nearest == index) & (nearest_distance <= tolerances[index])
        component_ys, component_xs = np.nonzero(component)
        if not len(component_xs):
            missing.append(component_id)
            continue
        observations[component_id] = {
            "left": round((int(component_xs.min()) - left) / frame_width, 6),
            "top": round((int(component_ys.min()) - top) / frame_height, 6),
            "right": round((int(component_xs.max()) - left) / frame_width, 6),
            "bottom": round((int(component_ys.max()) - top) / frame_height, 6),
        }
    return {
        "schema_version": 1,
        "record_type": "COMPONENT_MASK_NORMALIZED_OBSERVATIONS",
        "image_path": str(image_path),
        "normalization_frame_bbox_px": {"left": left, "top": top, "right": right, "bottom": bottom},
        "component_ids": list(component_ids),
        "observations": observations,
        "missing_component_ids": missing,
        "claim_boundary": "Bounds derive from the controlled component-mask palette and its combined foreground frame. They localize layout correction; camera/reference registration and visual review remain separate requirements.",
    }
