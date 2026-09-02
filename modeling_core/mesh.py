"""Deterministic connected-cage generators used by the fitting core."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def build_section_loft(shape: dict[str, Any]) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    """Build one open, connected, all-quad loft from semantic cross sections.

    Twelve or sixteen segments are normally enough for blockout fitting.  End caps intentionally
    remain open so the Blender stage can choose Solidify, a local quad cap, or an assembly joint.
    """
    segments = int(shape["segments"])
    vertices: list[tuple[float, float, float]] = []
    sx, sy, sz = (float(shape.get(key, 1.0)) for key in ("scale_x", "scale_y", "scale_z"))
    tx, ty, tz = (float(shape.get(key, 0.0)) for key in ("translate_x", "translate_y", "translate_z"))
    for station in shape["stations"]:
        width = float(station["half_width"]) * sx
        depth = float(station["half_depth"]) * sy
        z = float(station["z"]) * sz
        if shape.get("cross_section", "superellipse") == "box":
            corners = ((width, depth), (-width, depth), (-width, -depth), (width, -depth))
            per_side = segments // 4
            for side, start in enumerate(corners):
                end = corners[(side + 1) % 4]
                for step in range(per_side):
                    factor = step / per_side
                    vertices.append((
                        start[0] + (end[0] - start[0]) * factor + tx,
                        start[1] + (end[1] - start[1]) * factor + ty,
                        z + tz,
                    ))
        else:
            exponent = 2.0 / float(station.get("power", 2.0))
            for segment in range(segments):
                angle = 2.0 * math.pi * segment / segments
                cosine, sine = math.cos(angle), math.sin(angle)
                x = width * math.copysign(abs(cosine) ** exponent, cosine)
                y = depth * math.copysign(abs(sine) ** exponent, sine)
                vertices.append((x + tx, y + ty, z + tz))
    faces: list[tuple[int, int, int, int]] = []
    for station in range(len(shape["stations"]) - 1):
        lower, upper = station * segments, (station + 1) * segments
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((lower + segment, lower + nxt, upper + nxt, upper + segment))
    return np.asarray(vertices, dtype=np.float64), faces


def build_profile_extrusion(shape: dict[str, Any]) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    """Build one connected all-quad side cage from an arbitrary measured X/Z outline."""
    profile = [(float(point[0]), float(point[1])) for point in shape["profile"]]
    sx, sy, sz = (float(shape.get(key, 1.0)) for key in ("scale_x", "scale_y", "scale_z"))
    tx, ty, tz = (float(shape.get(key, 0.0)) for key in ("translate_x", "translate_y", "translate_z"))
    vertices = []
    for station in shape["depth_stations"]:
        for x, z in profile:
            vertices.append((
                x * sx * float(station.get("scale_x", 1.0)) + tx,
                float(station["y"]) * sy + ty,
                z * sz * float(station.get("scale_z", 1.0)) + tz,
            ))
    count = len(profile)
    faces = []
    for station in range(len(shape["depth_stations"]) - 1):
        front, rear = station * count, (station + 1) * count
        for index in range(count):
            nxt = (index + 1) % count
            faces.append((front + index, front + nxt, rear + nxt, rear + index))
    return np.asarray(vertices, dtype=np.float64), faces


def build_shape_mesh(shape: dict[str, Any]) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    if shape["family"] == "section_loft":
        return build_section_loft(shape)
    if shape["family"] == "profile_extrusion":
        return build_profile_extrusion(shape)
    raise ValueError(f"unsupported shape family: {shape.get('family')}")
