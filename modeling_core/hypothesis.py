"""Validation for the executable shape-and-camera intermediate representation.

The representation is deliberately small.  It describes what may be optimized before Blender is
allowed to mutate: one connected section loft, registered views, and explicit bounded variables.
It does not contain arbitrary Python or asset-specific builder logic.
"""

from __future__ import annotations

import copy
import math
from typing import Any


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def validate_hypothesis(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized copy or fail closed on an invalid hypothesis."""
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("shape hypothesis must be a schema-version 1 object")
    result = copy.deepcopy(raw)
    shape = result.get("shape")
    if not isinstance(shape, dict) or shape.get("family") != "section_loft":
        raise ValueError("shape.family must be section_loft")
    segments = int(shape.get("segments", 0))
    if segments < 8 or segments > 32 or segments % 4:
        raise ValueError("section loft segments must be a multiple of four from 8 through 32")
    shape["segments"] = segments
    shape["cross_section"] = str(shape.get("cross_section", "superellipse"))
    if shape["cross_section"] not in {"superellipse", "box"}:
        raise ValueError("shape.cross_section must be superellipse or box")
    for key in ("scale_x", "scale_y", "scale_z"):
        shape[key] = _finite(shape.get(key, 1.0), f"shape.{key}")
        if shape[key] <= 0:
            raise ValueError(f"shape.{key} must be positive")
    stations = shape.get("stations")
    if not isinstance(stations, list) or len(stations) < 2:
        raise ValueError("section loft needs at least two stations")
    previous_z = None
    for index, station in enumerate(stations):
        if not isinstance(station, dict):
            raise ValueError(f"station {index} must be an object")
        for key in ("z", "half_width", "half_depth"):
            station[key] = _finite(station.get(key), f"station {index}.{key}")
        station["power"] = _finite(station.get("power", 2.0), f"station {index}.power")
        if station["half_width"] <= 0 or station["half_depth"] <= 0:
            raise ValueError(f"station {index} dimensions must be positive")
        if not 1.0 <= station["power"] <= 12.0:
            raise ValueError(f"station {index}.power must be between 1 and 12")
        if previous_z is not None and station["z"] <= previous_z:
            raise ValueError("station z values must be strictly increasing")
        previous_z = station["z"]

    views = result.get("views")
    if not isinstance(views, list) or not views:
        raise ValueError("shape hypothesis needs at least one view")
    identifiers: set[str] = set()
    for index, view in enumerate(views):
        if not isinstance(view, dict):
            raise ValueError(f"view {index} must be an object")
        identifier = str(view.get("id") or "").strip()
        if not identifier or identifier in identifiers:
            raise ValueError("view ids must be unique and non-empty")
        identifiers.add(identifier)
        if view.get("projection", "orthographic") != "orthographic":
            raise ValueError("the CPU solver currently accepts orthographic views only")
        view["projection"] = "orthographic"
        view["image_size"] = [int(value) for value in view.get("image_size", [])]
        if len(view["image_size"]) != 2 or min(view["image_size"]) < 16:
            raise ValueError(f"view {identifier} needs image_size [width, height] >= 16")
        for key in ("yaw_degrees", "pitch_degrees", "roll_degrees", "world_scale", "offset_x", "offset_y"):
            default = 1.0 if key == "world_scale" else 0.0
            view[key] = _finite(view.get(key, default), f"view {identifier}.{key}")
        if view["world_scale"] <= 0:
            raise ValueError(f"view {identifier}.world_scale must be positive")

    variables = result.get("variables", [])
    if not isinstance(variables, list):
        raise ValueError("variables must be a list")
    for index, variable in enumerate(variables):
        if not isinstance(variable, dict) or not str(variable.get("pointer") or "").startswith("/"):
            raise ValueError(f"variable {index} needs a JSON pointer")
        bounds = variable.get("bounds")
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise ValueError(f"variable {index} needs [low, high] bounds")
        low, high = (_finite(bounds[0], "bound"), _finite(bounds[1], "bound"))
        if low >= high:
            raise ValueError(f"variable {index} bounds must increase")
        variable["bounds"] = [low, high]
    return result


def pointer_get(document: dict[str, Any], pointer: str) -> Any:
    node: Any = document
    for token in pointer.strip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def pointer_set(document: dict[str, Any], pointer: str, value: float) -> None:
    tokens = pointer.strip("/").split("/")
    node: Any = document
    for token in tokens[:-1]:
        token = token.replace("~1", "/").replace("~0", "~")
        node = node[int(token)] if isinstance(node, list) else node[token]
    final = tokens[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(node, list):
        node[int(final)] = float(value)
    else:
        node[final] = float(value)
