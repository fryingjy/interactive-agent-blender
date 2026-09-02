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


def build_profile_revolution(shape: dict[str, Any]) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    """Revolve an ordered radius/Z profile into one open all-quad radial cage."""
    segments = int(shape["segments"])
    sx, sy, sz = (float(shape.get(key, 1.0)) for key in ("scale_x", "scale_y", "scale_z"))
    tx, ty, tz = (float(shape.get(key, 0.0)) for key in ("translate_x", "translate_y", "translate_z"))
    vertices = []
    for radius, z in shape["profile"]:
        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments
            vertices.append((
                float(radius) * math.cos(angle) * sx + tx,
                float(radius) * math.sin(angle) * sy + ty,
                float(z) * sz + tz,
            ))
    faces = []
    for station in range(len(shape["profile"]) - 1):
        lower, upper = station * segments, (station + 1) * segments
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((lower + segment, lower + nxt, upper + nxt, upper + segment))
    return np.asarray(vertices, dtype=np.float64), faces


def _sweep_frames(points: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    tangents = []
    for index in range(len(points)):
        direction = (
            points[1] - points[0]
            if index == 0
            else points[-1] - points[-2]
            if index == len(points) - 1
            else points[index + 1] - points[index - 1]
        )
        tangents.append(direction / np.linalg.norm(direction))
    axes = np.eye(3)
    first_axis = axes[int(np.argmin(np.abs(axes @ tangents[0])))]
    normal = np.cross(tangents[0], first_axis)
    normal /= np.linalg.norm(normal)
    frames = []
    for tangent in tangents:
        transported = normal - np.dot(normal, tangent) * tangent
        if np.linalg.norm(transported) <= 1e-8:
            axis = axes[int(np.argmin(np.abs(axes @ tangent)))]
            transported = np.cross(tangent, axis)
        normal = transported / np.linalg.norm(transported)
        binormal = np.cross(tangent, normal)
        binormal /= np.linalg.norm(binormal)
        frames.append((normal.copy(), binormal))
    return frames


def build_curve_sweep(shape: dict[str, Any]) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    """Sweep elliptical rings along a measured 3D path using transported local frames."""
    segments = int(shape["segments"])
    stations = shape["path_stations"]
    points = np.asarray([station["point"] for station in stations], dtype=np.float64)
    frames = _sweep_frames(points)
    vertices = []
    for station, point, (normal, binormal) in zip(stations, points, frames):
        roll = math.radians(float(station.get("roll_degrees", 0.0)))
        radius = float(station["radius"])
        scale_x = float(station.get("scale_x", 1.0))
        scale_y = float(station.get("scale_y", 1.0))
        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments + roll
            vertices.append(point + radius * (
                math.cos(angle) * scale_x * normal
                + math.sin(angle) * scale_y * binormal
            ))
    vertices = np.asarray(vertices, dtype=np.float64)
    vertices *= np.asarray([float(shape.get(key, 1.0)) for key in ("scale_x", "scale_y", "scale_z")])
    vertices += np.asarray([float(shape.get(key, 0.0)) for key in ("translate_x", "translate_y", "translate_z")])
    faces = []
    for station in range(len(stations) - 1):
        first, second = station * segments, (station + 1) * segments
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((first + segment, first + nxt, second + nxt, second + segment))
    return vertices, faces


def build_shape_mesh(shape: dict[str, Any]) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    if shape["family"] == "section_loft":
        return build_section_loft(shape)
    if shape["family"] == "profile_extrusion":
        return build_profile_extrusion(shape)
    if shape["family"] == "profile_revolution":
        return build_profile_revolution(shape)
    if shape["family"] == "curve_sweep":
        return build_curve_sweep(shape)
    raise ValueError(f"unsupported shape family: {shape.get('family')}")
