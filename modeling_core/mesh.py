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
                        start[0] + (end[0] - start[0]) * factor,
                        start[1] + (end[1] - start[1]) * factor,
                        z,
                    ))
        else:
            exponent = 2.0 / float(station.get("power", 2.0))
            for segment in range(segments):
                angle = 2.0 * math.pi * segment / segments
                cosine, sine = math.cos(angle), math.sin(angle)
                x = width * math.copysign(abs(cosine) ** exponent, cosine)
                y = depth * math.copysign(abs(sine) ** exponent, sine)
                vertices.append((x, y, z))
    faces: list[tuple[int, int, int, int]] = []
    for station in range(len(shape["stations"]) - 1):
        lower, upper = station * segments, (station + 1) * segments
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((lower + segment, lower + nxt, upper + nxt, upper + segment))
    return np.asarray(vertices, dtype=np.float64), faces
