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
    """Project world XYZ to image XY using an explicit camera hypothesis."""
    width, height = view["image_size"]
    rotated = np.asarray(vertices, dtype=float) @ _rotation(view).T
    if view.get("projection", "orthographic") == "perspective":
        matrix = view.get("world_to_camera")
        if matrix is not None:
            homogeneous = np.column_stack((np.asarray(vertices, dtype=float), np.ones(len(vertices))))
            camera = homogeneous @ np.asarray(matrix, dtype=float).T
            depth = camera[:, 2]
            horizontal = camera[:, 0]
            vertical = camera[:, 1]
        else:
            depth = float(view["camera_distance"]) - rotated[:, 1]
            horizontal = rotated[:, 0]
            vertical = -rotated[:, 2]
        if np.any(depth <= 1e-4):
            raise ValueError("geometry crosses or falls behind the perspective camera")
        focal = 0.5 * height / math.tan(0.5 * math.radians(float(view["vertical_fov_degrees"])))
        x = width * 0.5 + focal * horizontal / depth + float(view["offset_x"]) * min(width, height)
        y = height * 0.5 + focal * vertical / depth - float(view["offset_y"]) * min(width, height)
    else:
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
