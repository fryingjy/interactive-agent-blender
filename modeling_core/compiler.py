"""Compile a fitted proxy into the existing transaction-safe Blender command surface."""

from __future__ import annotations

from typing import Any

from .hypothesis import validate_hypothesis
from .mesh import build_shape_mesh


def compile_blender_command(raw: dict[str, Any], *, name: str = "FittedProxy") -> dict[str, Any]:
    hypothesis = validate_hypothesis(raw)
    vertices, faces = build_shape_mesh(hypothesis["shape"])
    return {
        "command": "create_authored_quad_mesh",
        "params": {
            "name": name,
            "vertices": vertices.tolist(),
            "faces": [list(face) for face in faces],
        },
        "metadata": {
            "source": f"modeling_core.{hypothesis['shape']['family']}",
            "connected_components": 1,
            "all_quad": True,
            "end_caps": "OPEN_FOR_EXPLICIT_SURFACE_DECISION",
            "modifiers_applied": False,
            "profile_winding_normalized": bool(hypothesis["shape"].get("profile_winding_normalized", False)),
        },
    }
