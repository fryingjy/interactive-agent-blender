"""Small CPU orthographic silhouette renderer for optimizer inner loops."""

from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np


def _rotation(view: dict[str, Any]) -> np.ndarray:
    yaw, pitch, roll = (math.radians(float(view[key])) for key in ("yaw_degrees", "pitch_degrees", "roll_degrees"))
    cz, sz = math.cos(yaw), math.sin(yaw)
    cx, sx = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(roll), math.sin(roll)
    rz = np.asarray(((cz, -sz, 0), (sz, cz, 0), (0, 0, 1)), dtype=float)
    rx = np.asarray(((1, 0, 0), (0, cx, -sx), (0, sx, cx)), dtype=float)
    ry = np.asarray(((cy, 0, sy), (0, 1, 0), (-sy, 0, cy)), dtype=float)
    return ry @ rx @ rz


def project_vertices(vertices: np.ndarray, view: dict[str, Any]) -> np.ndarray:
    """Project world XYZ to image XY using an explicit orthographic camera hypothesis."""
    width, height = view["image_size"]
    rotated = np.asarray(vertices, dtype=float) @ _rotation(view).T
    scale = float(view["world_scale"])
    x = width * 0.5 + (rotated[:, 0] / scale + float(view["offset_x"])) * min(width, height)
    y = height * 0.5 - (rotated[:, 2] / scale + float(view["offset_y"])) * min(width, height)
    return np.column_stack((x, y))


def render_silhouette(
    vertices: np.ndarray,
    faces: list[tuple[int, int, int, int]],
    view: dict[str, Any],
) -> np.ndarray:
    """Rasterize the union of cage faces; depth is irrelevant for a binary silhouette."""
    width, height = view["image_size"]
    points = project_vertices(vertices, view)
    mask = np.zeros((height, width), dtype=np.uint8)
    for face in faces:
        polygon = np.rint(points[np.asarray(face, dtype=int)]).astype(np.int32)
        cv2.fillConvexPoly(mask, polygon, 1, lineType=cv2.LINE_8)
    return mask.astype(bool)
