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


def _signed_profile_area(profile: list[list[float]]) -> float:
    return 0.5 * sum(
        point[0] * profile[(index + 1) % len(profile)][1]
        - profile[(index + 1) % len(profile)][0] * point[1]
        for index, point in enumerate(profile)
    )


def _cross_2d(first: list[float], second: list[float], third: list[float]) -> float:
    return (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (third[0] - first[0])


def _segments_cross(first: list[float], second: list[float], third: list[float], fourth: list[float]) -> bool:
    first_side = _cross_2d(first, second, third)
    second_side = _cross_2d(first, second, fourth)
    third_side = _cross_2d(third, fourth, first)
    fourth_side = _cross_2d(third, fourth, second)
    if first_side * second_side < -1e-12 and third_side * fourth_side < -1e-12:
        return True

    def on_segment(start: list[float], end: list[float], point: list[float], cross: float) -> bool:
        return (
            abs(cross) <= 1e-10
            and min(start[0], end[0]) - 1e-10 <= point[0] <= max(start[0], end[0]) + 1e-10
            and min(start[1], end[1]) - 1e-10 <= point[1] <= max(start[1], end[1]) + 1e-10
        )

    return (
        on_segment(first, second, third, first_side)
        or on_segment(first, second, fourth, second_side)
        or on_segment(third, fourth, first, third_side)
        or on_segment(third, fourth, second, fourth_side)
    )


def _normalize_closed_profile(raw: Any, label: str, *, minimum_points: int = 4) -> tuple[list[list[float]], bool]:
    if not isinstance(raw, list) or len(raw) < minimum_points:
        raise ValueError(f"{label} needs at least {minimum_points} outline points")
    profile = []
    for index, point in enumerate(raw):
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError(f"{label} point {index} must be [x, z]")
        profile.append([_finite(point[0], f"{label} x"), _finite(point[1], f"{label} z")])
    if len({tuple(point) for point in profile}) != len(profile):
        raise ValueError(f"{label} points must be unique")
    count = len(profile)
    for first in range(count):
        for second in range(first + 1, count):
            if second in {first, (first + 1) % count} or first == (second + 1) % count:
                continue
            if _segments_cross(profile[first], profile[(first + 1) % count], profile[second], profile[(second + 1) % count]):
                raise ValueError(f"{label} must be a simple non-self-intersecting outline")
    signed_area = _signed_profile_area(profile)
    if abs(signed_area) <= 1e-10:
        raise ValueError(f"{label} must enclose non-zero area")
    normalized = signed_area > 0.0
    if normalized:
        profile.reverse()
    return profile, normalized


def _point_strictly_inside_profile(point: list[float], profile: list[list[float]]) -> bool:
    inside = False
    x, z = point
    for index, first in enumerate(profile):
        second = profile[(index + 1) % len(profile)]
        if abs(_cross_2d(first, second, point)) <= 1e-10 and min(first[0], second[0]) <= x <= max(first[0], second[0]) and min(first[1], second[1]) <= z <= max(first[1], second[1]):
            return False
        if (first[1] > z) != (second[1] > z):
            crossing_x = first[0] + (z - first[1]) * (second[0] - first[0]) / (second[1] - first[1])
            if crossing_x > x:
                inside = not inside
    return inside


def _normalize_depth_stations(raw: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError(f"{label} needs at least two depth stations")
    previous_y = None
    for index, station in enumerate(raw):
        if not isinstance(station, dict):
            raise ValueError(f"{label} station {index} must be an object")
        station["y"] = _finite(station.get("y"), f"{label} station {index}.y")
        station["scale_x"] = _finite(station.get("scale_x", 1.0), f"{label} station {index}.scale_x")
        station["scale_z"] = _finite(station.get("scale_z", 1.0), f"{label} station {index}.scale_z")
        if station["scale_x"] <= 0 or station["scale_z"] <= 0:
            raise ValueError(f"{label} station scales must be positive")
        if previous_y is not None and station["y"] <= previous_y:
            raise ValueError(f"{label} station y values must be strictly increasing")
        previous_y = station["y"]
    return raw


def validate_hypothesis(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized copy or fail closed on an invalid hypothesis."""
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("shape hypothesis must be a schema-version 1 object")
    result = copy.deepcopy(raw)
    shape = result.get("shape")
    families = {"section_loft", "profile_extrusion", "profile_revolution", "curve_sweep", "profile_sweep", "profile_ring_extrusion"}
    if not isinstance(shape, dict) or shape.get("family") not in families:
        raise ValueError(f"shape.family must be one of {sorted(families)}")
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
        normalized_profile, normalized = _normalize_closed_profile(shape.get("profile"), "profile extrusion")
        shape["profile_winding_normalized"] = normalized
        shape["profile_winding"] = "CLOCKWISE_XZ"
        shape["profile"] = normalized_profile
        shape["depth_stations"] = _normalize_depth_stations(shape.get("depth_stations"), "profile extrusion")
    elif shape["family"] == "profile_ring_extrusion":
        outer, outer_normalized = _normalize_closed_profile(shape.get("outer_profile"), "outer profile")
        inner, inner_normalized = _normalize_closed_profile(shape.get("inner_profile"), "inner profile")
        if len(outer) != len(inner):
            raise ValueError("ring extrusion outer and inner profiles require equal vertex counts for all-quad caps")
        if abs(_signed_profile_area(inner)) >= abs(_signed_profile_area(outer)):
            raise ValueError("ring extrusion inner profile must have less area than the outer profile")
        if any(not _point_strictly_inside_profile(point, outer) for point in inner):
            raise ValueError("ring extrusion inner profile must be strictly inside the outer profile")
        for outer_index in range(len(outer)):
            for inner_index in range(len(inner)):
                if _segments_cross(
                    outer[outer_index], outer[(outer_index + 1) % len(outer)],
                    inner[inner_index], inner[(inner_index + 1) % len(inner)],
                ):
                    raise ValueError("ring extrusion inner and outer profile edges cannot cross")
        options = [inner[shift:] + inner[:shift] for shift in range(len(inner))]
        inner = min(options, key=lambda candidate: sum(
            (outer[index][0] - candidate[index][0]) ** 2 + (outer[index][1] - candidate[index][1]) ** 2
            for index in range(len(outer))
        ))
        connectors = [(outer[index], inner[index]) for index in range(len(outer))]
        for index, (outer_point, inner_point) in enumerate(connectors):
            for factor in (0.25, 0.5, 0.75):
                sample = [
                    outer_point[axis] + factor * (inner_point[axis] - outer_point[axis])
                    for axis in range(2)
                ]
                if not _point_strictly_inside_profile(sample, outer) or _point_strictly_inside_profile(sample, inner):
                    raise ValueError("ring extrusion correspondence crosses outside the annular material")
            next_index = (index + 1) % len(outer)
            cap_quad = [outer_point, inner_point, inner[next_index], outer[next_index]]
            if abs(_signed_profile_area(cap_quad)) <= 1e-10:
                raise ValueError("ring extrusion correspondence creates a degenerate cap quad")
            for other_index in range(index + 1, len(connectors)):
                if _segments_cross(outer_point, inner_point, *connectors[other_index]):
                    raise ValueError("ring extrusion correspondence connectors cannot cross")
        shape["outer_profile"] = outer
        shape["inner_profile"] = inner
        shape["profile_winding"] = "CLOCKWISE_XZ"
        shape["profile_winding_normalized"] = outer_normalized or inner_normalized
        shape["depth_stations"] = _normalize_depth_stations(shape.get("depth_stations"), "ring extrusion")
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
    elif shape["family"] == "curve_sweep":
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
    else:
        profile, normalized = _normalize_closed_profile(shape.get("profile"), "sweep profile")
        profile.reverse()
        shape["profile"] = profile
        shape["profile_winding"] = "COUNTERCLOCKWISE_UV"
        shape["profile_winding_normalized"] = not normalized
        stations = shape.get("path_stations")
        if not isinstance(stations, list) or len(stations) < 2:
            raise ValueError("profile sweep needs at least two path stations")
        previous_point = None
        for index, station in enumerate(stations):
            if not isinstance(station, dict):
                raise ValueError(f"profile sweep path station {index} must be an object")
            point = station.get("point")
            if not isinstance(point, list) or len(point) != 3:
                raise ValueError(f"profile sweep path station {index}.point must be [x, y, z]")
            station["point"] = [_finite(value, f"profile sweep path station {index}.point") for value in point]
            if previous_point is not None and math.dist(previous_point, station["point"]) <= 1e-8:
                raise ValueError("profile sweep consecutive path points must be distinct")
            station["scale_u"] = _finite(station.get("scale_u", 1.0), f"profile sweep path station {index}.scale_u")
            station["scale_v"] = _finite(station.get("scale_v", 1.0), f"profile sweep path station {index}.scale_v")
            station["roll_degrees"] = _finite(station.get("roll_degrees", 0.0), f"profile sweep path station {index}.roll_degrees")
            if station["scale_u"] <= 0 or station["scale_v"] <= 0:
                raise ValueError("profile sweep station scales must be positive")
            previous_point = station["point"]
        if any(math.dist(stations[index - 1]["point"], stations[index + 1]["point"]) <= 1e-8 for index in range(1, len(stations) - 1)):
            raise ValueError("profile sweep centered path tangents must be non-zero")

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
