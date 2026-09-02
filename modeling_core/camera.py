"""Measured perspective-camera initialization from landmark correspondences."""

from __future__ import annotations

import math
from typing import Sequence

import cv2
import numpy as np


def camera_intrinsics(image_size: tuple[int, int], vertical_fov_degrees: float) -> np.ndarray:
    width, height = (int(value) for value in image_size)
    if min(width, height) < 16 or not 5.0 <= float(vertical_fov_degrees) <= 150.0:
        raise ValueError("camera intrinsics need a valid image size and 5-150 degree vertical FOV")
    focal = 0.5 * height / math.tan(0.5 * math.radians(float(vertical_fov_degrees)))
    return np.asarray(((focal, 0.0, width * 0.5), (0.0, focal, height * 0.5), (0.0, 0.0, 1.0)), dtype=np.float64)


def calibrate_perspective_view(
    object_points: Sequence[Sequence[float]],
    image_points: Sequence[Sequence[float]],
    *,
    image_size: tuple[int, int],
    vertical_fov_degrees: float,
    view_id: str = "calibrated",
) -> dict:
    """Solve a world-to-camera transform and report normalized reprojection error.

    The caller must provide real correspondences on one physical object. This function does not
    infer which image feature matches which 3D landmark and cannot calibrate arbitrary style boards.
    """
    object_array = np.asarray(object_points, dtype=np.float64)
    image_array = np.asarray(image_points, dtype=np.float64)
    if object_array.ndim != 2 or object_array.shape[1:] != (3,) or len(object_array) < 6:
        raise ValueError("perspective calibration needs at least six 3D object points")
    if image_array.shape != (len(object_array), 2):
        raise ValueError("image points must match the object-point count")
    if np.linalg.matrix_rank(object_array - object_array.mean(axis=0)) < 3:
        raise ValueError("perspective calibration points must span three dimensions")
    intrinsics = camera_intrinsics(image_size, vertical_fov_degrees)
    success, rotation_vector, translation = cv2.solvePnP(
        object_array,
        image_array,
        intrinsics,
        np.zeros(5, dtype=np.float64),
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not success:
        raise ValueError("OpenCV could not solve the perspective camera")
    rotation, _ = cv2.Rodrigues(rotation_vector)
    world_to_camera = np.column_stack((rotation, translation.reshape(3)))
    projected, _ = cv2.projectPoints(
        object_array,
        rotation_vector,
        translation,
        intrinsics,
        np.zeros(5, dtype=np.float64),
    )
    residuals = np.linalg.norm(projected.reshape(-1, 2) - image_array, axis=1)
    normalized = residuals / max(image_size)
    return {
        "view": {
            "id": view_id,
            "projection": "perspective",
            "image_size": list(image_size),
            "vertical_fov_degrees": float(vertical_fov_degrees),
            "world_to_camera": world_to_camera.tolist(),
            "yaw_degrees": 0.0,
            "pitch_degrees": 0.0,
            "roll_degrees": 0.0,
            "world_scale": 1.0,
            "camera_distance": 1.0,
            "offset_x": 0.0,
            "offset_y": 0.0,
        },
        "control_point_count": len(object_array),
        "mean_reprojection_error_normalized": float(normalized.mean()),
        "max_reprojection_error_normalized": float(normalized.max()),
        "claim_boundary": "The transform is valid only for the supplied correspondences, intrinsics assumption, and physical target.",
    }
