"""Validation for the executable shape-and-camera intermediate representation.

The representation is deliberately small. It describes what may be optimized before Blender is
allowed to mutate: one generic connected cage, registered views, and explicit bounded variables.
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
    if not isinstance(shape, dict) or shape.get("family") not in {"section_loft", "profile_extrusion", "profile_revolution", "curve_sweep"}:
        raise ValueError("shape.family must be section_loft, profile_extrusion, profile_revolution, or curve_sweep")
    for key in ("scale_x", "scale_y", "scale_z"):
        shape[key] = _finite(shape.get(key, 1.0), f"shape.{key}")
        if shape[key] <= 0:
            raise ValueError(f"shape.{key} must be positive")
    for key in ("translate_x", "translate_y", "translate_z"):
        shape[key] = _finite(shape.get(key, 0.0), f"shape.{key}")
    if shape["family"] == "section_loft":
        segments = int(shape.get("segments", 0))
        if segments < 8 or segments > 32 or segments % 4:
            raise ValueError("section loft segments must be a multiple of four from 8 through 32")
        shape["segments"] = segments
        shape["cross_section"] = str(shape.get("cross_section", "superellipse"))
        if shape["cross_section"] not in {"superellipse", "box"}:
            raise ValueError("shape.cross_section must be superellipse or box")
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
    elif shape["family"] == "profile_extrusion":
        profile = shape.get("profile")
        if not isinstance(profile, list) or len(profile) < 4:
            raise ValueError("profile extrusion needs at least four outline points")
        normalized_profile = []
        for index, point in enumerate(profile):
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError(f"profile point {index} must be [x, z]")
            normalized_profile.append([_finite(point[0], "profile x"), _finite(point[1], "profile z")])
        if len({tuple(point) for point in normalized_profile}) != len(normalized_profile):
            raise ValueError("profile outline points must be unique")
        signed_area = 0.5 * sum(
            point[0] * normalized_profile[(index + 1) % len(normalized_profile)][1]
            - normalized_profile[(index + 1) % len(normalized_profile)][0] * point[1]
            for index, point in enumerate(normalized_profile)
        )
        if abs(signed_area) <= 1e-10:
            raise ValueError("profile outline must enclose non-zero area")
        shape["profile_winding_normalized"] = signed_area > 0.0
        if signed_area > 0.0:
            normalized_profile.reverse()
        shape["profile_winding"] = "CLOCKWISE_XZ"
        shape["profile"] = normalized_profile
        depth_stations = shape.get("depth_stations")
        if not isinstance(depth_stations, list) or len(depth_stations) < 2:
            raise ValueError("profile extrusion needs at least two depth stations")
        previous_y = None
        for index, station in enumerate(depth_stations):
            if not isinstance(station, dict):
                raise ValueError(f"depth station {index} must be an object")
            station["y"] = _finite(station.get("y"), f"depth station {index}.y")
            station["scale_x"] = _finite(station.get("scale_x", 1.0), f"depth station {index}.scale_x")
            station["scale_z"] = _finite(station.get("scale_z", 1.0), f"depth station {index}.scale_z")
            if station["scale_x"] <= 0 or station["scale_z"] <= 0:
                raise ValueError("depth-station scales must be positive")
            if previous_y is not None and station["y"] <= previous_y:
                raise ValueError("depth-station y values must be strictly increasing")
            previous_y = station["y"]
    elif shape["family"] == "profile_revolution":
        segments = int(shape.get("segments", 0))
        if segments < 8 or segments > 32 or segments % 4:
            raise ValueError("profile revolution segments must be a multiple of four from 8 through 32")
        shape["segments"] = segments
        profile = shape.get("profile")
        if not isinstance(profile, list) or len(profile) < 2:
            raise ValueError("profile revolution needs at least two [radius, z] points")
        normalized_profile = []
        previous_z = None
        for index, point in enumerate(profile):
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError(f"revolution profile point {index} must be [radius, z]")
            radius = _finite(point[0], f"revolution profile {index}.radius")
            z = _finite(point[1], f"revolution profile {index}.z")
            if radius <= 0:
                raise ValueError("open all-quad revolution profile radii must be positive")
            if normalized_profile and normalized_profile[-1] == [radius, z]:
                raise ValueError("revolution profile consecutive points must be distinct")
            if previous_z is not None and z < previous_z:
                raise ValueError("revolution profile z values must be non-decreasing")
            normalized_profile.append([radius, z])
            previous_z = z
        shape["profile"] = normalized_profile
    else:
        segments = int(shape.get("segments", 0))
        if segments < 8 or segments > 32 or segments % 4:
            raise ValueError("curve sweep segments must be a multiple of four from 8 through 32")
        shape["segments"] = segments
        stations = shape.get("path_stations")
        if not isinstance(stations, list) or len(stations) < 2:
            raise ValueError("curve sweep needs at least two path stations")
        previous_point = None
        for index, station in enumerate(stations):
            if not isinstance(station, dict):
                raise ValueError(f"path station {index} must be an object")
            point = station.get("point")
            if not isinstance(point, list) or len(point) != 3:
                raise ValueError(f"path station {index}.point must be [x, y, z]")
            station["point"] = [_finite(value, f"path station {index}.point") for value in point]
            if previous_point is not None and math.dist(previous_point, station["point"]) <= 1e-8:
                raise ValueError("curve sweep consecutive path points must be distinct")
            station["radius"] = _finite(station.get("radius"), f"path station {index}.radius")
            station["scale_x"] = _finite(station.get("scale_x", 1.0), f"path station {index}.scale_x")
            station["scale_y"] = _finite(station.get("scale_y", 1.0), f"path station {index}.scale_y")
            station["roll_degrees"] = _finite(station.get("roll_degrees", 0.0), f"path station {index}.roll_degrees")
            if station["radius"] <= 0 or station["scale_x"] <= 0 or station["scale_y"] <= 0:
                raise ValueError("curve sweep radii and station scales must be positive")
            previous_point = station["point"]
        if any(math.dist(stations[index - 1]["point"], stations[index + 1]["point"]) <= 1e-8 for index in range(1, len(stations) - 1)):
            raise ValueError("curve sweep centered path tangents must be non-zero")

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
        projection = str(view.get("projection", "orthographic"))
        if projection not in {"orthographic", "perspective"}:
            raise ValueError("view projection must be orthographic or perspective")
        view["projection"] = projection
        view["image_size"] = [int(value) for value in view.get("image_size", [])]
        if len(view["image_size"]) != 2 or min(view["image_size"]) < 16:
            raise ValueError(f"view {identifier} needs image_size [width, height] >= 16")
        for key in ("yaw_degrees", "pitch_degrees", "roll_degrees", "world_scale", "offset_x", "offset_y"):
            default = 1.0 if key == "world_scale" else 0.0
            view[key] = _finite(view.get(key, default), f"view {identifier}.{key}")
        if view["world_scale"] <= 0:
            raise ValueError(f"view {identifier}.world_scale must be positive")
        view["camera_distance"] = _finite(view.get("camera_distance", 5.0), f"view {identifier}.camera_distance")
        view["vertical_fov_degrees"] = _finite(view.get("vertical_fov_degrees", 50.0), f"view {identifier}.vertical_fov_degrees")
        if projection == "perspective":
            if view["camera_distance"] <= 0:
                raise ValueError(f"view {identifier}.camera_distance must be positive")
            if not 5.0 <= view["vertical_fov_degrees"] <= 150.0:
                raise ValueError(f"view {identifier}.vertical_fov_degrees must be between 5 and 150")
            matrix = view.get("world_to_camera")
            if matrix is not None:
                if not isinstance(matrix, list) or len(matrix) != 3 or any(not isinstance(row, list) or len(row) != 4 for row in matrix):
                    raise ValueError(f"view {identifier}.world_to_camera must be a 3x4 matrix")
                view["world_to_camera"] = [[_finite(value, "world_to_camera") for value in row] for row in matrix]

    acceptance = result.setdefault("acceptance", {})
    if not isinstance(acceptance, dict):
        raise ValueError("acceptance must be an object")
    acceptance["max_mean_view_loss"] = _finite(acceptance.get("max_mean_view_loss", 0.18), "acceptance.max_mean_view_loss")
    acceptance["max_each_view_loss"] = _finite(acceptance.get("max_each_view_loss", 0.25), "acceptance.max_each_view_loss")
    acceptance["require_hole_count_match"] = bool(acceptance.get("require_hole_count_match", True))
    if acceptance["max_mean_view_loss"] <= 0 or acceptance["max_each_view_loss"] <= 0:
        raise ValueError("acceptance loss limits must be positive")

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
