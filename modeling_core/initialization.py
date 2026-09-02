"""Initialize generic component hypotheses from hash-bound masks and registered cameras."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from scipy.optimize import least_squares, lsq_linear

from .camera import camera_intrinsics
from .hypothesis import validate_hypothesis
from .render import project_vertices, view_rotation_matrix


SUPPORTED_INITIAL_FAMILIES = {
    "section_loft",
    "profile_extrusion",
    "profile_revolution",
    "profile_ring_extrusion",
}


def _component_masks(bundle: dict[str, Any], component_id: str) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    masks = {}
    views = []
    for record in bundle.get("views", []):
        evidence = record.get("component_evidence") or {}
        observation = evidence.get("observations", {}).get(component_id)
        if observation is None:
            continue
        label_record = evidence.get("label_map", {})
        path = Path(label_record.get("path", ""))
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != label_record.get("sha256"):
            raise ValueError(f"{component_id}: component label map is stale or missing")
        labels = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        label = observation.get("label")
        if labels is None or not isinstance(label, int) or isinstance(label, bool):
            raise ValueError(f"{component_id}: component label evidence is invalid")
        mask = labels == label
        view = copy.deepcopy(record.get("solver_view"))
        if not isinstance(view, dict) or not mask.any():
            raise ValueError(f"{component_id}: component mask or solver view is missing")
        if view.get("id") != record.get("view_id") or record["view_id"] in masks:
            raise ValueError(f"{component_id}: solver view identity is inconsistent or duplicated")
        expected = (view["image_size"][1], view["image_size"][0])
        if mask.shape != expected:
            raise ValueError(f"{component_id}: component mask does not match its solver view")
        masks[record["view_id"]] = mask
        views.append(view)
    if len(masks) < 2:
        raise ValueError(f"{component_id}: initialization requires at least two registered component views")
    return masks, views


def _mask_observation(mask: np.ndarray, view: dict[str, Any]) -> dict[str, Any]:
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    width, height = view["image_size"]
    canvas = min(width, height)
    scale = float(view["world_scale"])
    center_x = 0.5 * (x0 + x1)
    center_y = 0.5 * (y0 + y1)
    horizontal = ((center_x - width * 0.5) / canvas - float(view["offset_x"])) * scale
    vertical = ((height * 0.5 - center_y) / canvas - float(view["offset_y"])) * scale
    return {
        "bbox_pixels": [x0, y0, x1, y1],
        "projected_center": [horizontal, vertical],
        "projected_half_extents": [0.5 * (x1 - x0 + 1) * scale / canvas, 0.5 * (y1 - y0 + 1) * scale / canvas],
        "world_per_pixel": scale / canvas,
    }


def solve_orthographic_component_bounds(
    masks: dict[str, np.ndarray],
    views: list[dict[str, Any]],
    *,
    maximum_relative_residual: float = 0.2,
) -> dict[str, Any]:
    """Solve an axis-aligned world box from registered orthographic silhouette bounds."""
    if not 0 < maximum_relative_residual <= 1:
        raise ValueError("maximum_relative_residual must be in (0, 1]")
    view_map = {view["id"]: view for view in views}
    if len(view_map) != len(views) or set(masks) != set(view_map):
        raise ValueError("component masks and solver views must have unique matching ids")
    rows = []
    centers = []
    extent_rows = []
    projected_extents = []
    observations = {}
    pixel_scales = []
    used_views = []
    for view_id, mask in masks.items():
        view = view_map[view_id]
        if view.get("projection", "orthographic") != "orthographic":
            continue
        observation = _mask_observation(mask, view)
        rotation = view_rotation_matrix(view)
        rows.extend((rotation[0], rotation[2]))
        centers.extend(observation["projected_center"])
        extent_rows.extend((np.abs(rotation[0]), np.abs(rotation[2])))
        projected_extents.extend(observation["projected_half_extents"])
        observations[view_id] = observation
        pixel_scales.append(observation["world_per_pixel"])
        used_views.append(view_id)
    if len(used_views) < 2:
        return {"status": "UNDERCONSTRAINED", "issues": ["at least two orthographic component views are required"], "used_view_ids": used_views}
    center_matrix = np.asarray(rows, dtype=float)
    extent_matrix = np.asarray(extent_rows, dtype=float)
    center_rank = int(np.linalg.matrix_rank(center_matrix, tol=1e-8))
    extent_rank = int(np.linalg.matrix_rank(extent_matrix, tol=1e-8))
    if center_rank < 3 or extent_rank < 3:
        return {
            "status": "UNDERCONSTRAINED",
            "issues": [f"registered views constrain center rank {center_rank}/3 and extent rank {extent_rank}/3"],
            "used_view_ids": used_views,
            "center_rank": center_rank,
            "extent_rank": extent_rank,
            "observations": observations,
        }
    center, _residuals, _rank, singular_values = np.linalg.lstsq(center_matrix, np.asarray(centers), rcond=None)
    extent_fit = lsq_linear(extent_matrix, np.asarray(projected_extents), bounds=(1e-8, np.inf))
    extents = extent_fit.x
    if not extent_fit.success or np.any(extents <= max(pixel_scales) * 0.25):
        return {"status": "REJECTED", "issues": ["nonnegative extent solve failed or collapsed an axis"], "used_view_ids": used_views}
    center_residual = center_matrix @ center - np.asarray(centers)
    extent_residual = extent_matrix @ extents - np.asarray(projected_extents)
    residual = float(max(np.max(np.abs(center_residual)), np.max(np.abs(extent_residual))))
    relative_residual = residual / max(float(np.max(extents)), 1e-8)
    if relative_residual > maximum_relative_residual:
        return {
            "status": "REJECTED",
            "issues": [f"registered silhouette bounds disagree by relative residual {relative_residual:.3f}"],
            "used_view_ids": used_views,
            "center_rank": center_rank,
            "extent_rank": extent_rank,
            "maximum_world_residual": residual,
            "relative_residual": relative_residual,
            "observations": observations,
        }
    uncertainty = min(0.35, max(0.08, relative_residual * 2.0, max(pixel_scales) * 2.0 / float(np.min(extents))))
    return {
        "status": "SOLVED",
        "method": "ORTHOGRAPHIC_LINEAR_BOUNDS",
        "used_view_ids": used_views,
        "center": center.tolist(),
        "half_extents": extents.tolist(),
        "center_rank": center_rank,
        "extent_rank": extent_rank,
        "condition_number": float(singular_values[0] / singular_values[-1]),
        "maximum_world_residual": residual,
        "relative_uncertainty": uncertainty,
        "world_per_pixel": max(pixel_scales),
        "observations": observations,
    }


def _perspective_camera(view: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    matrix = np.asarray(view.get("world_to_camera"), dtype=float)
    if matrix.shape != (3, 4) or not np.isfinite(matrix).all():
        raise ValueError(f"perspective view {view.get('id')} requires a finite calibrated 3x4 world_to_camera matrix")
    rotation, translation = matrix[:, :3], matrix[:, 3]
    if not np.allclose(rotation @ rotation.T, np.eye(3), atol=1e-4) or np.linalg.det(rotation) < 0.99:
        raise ValueError(f"perspective view {view.get('id')} has a non-rigid calibration matrix")
    center = -rotation.T @ translation
    return rotation, translation, center


def _perspective_ray(view: dict[str, Any], pixel: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    rotation, _translation, center = _perspective_camera(view)
    width, height = view["image_size"]
    intrinsics = camera_intrinsics(tuple(view["image_size"]), float(view["vertical_fov_degrees"]))
    canvas = min(width, height)
    adjusted_x = float(pixel[0]) - float(view.get("offset_x", 0.0)) * canvas
    adjusted_y = float(pixel[1]) + float(view.get("offset_y", 0.0)) * canvas
    camera_direction = np.asarray([
        (adjusted_x - intrinsics[0, 2]) / intrinsics[0, 0],
        (adjusted_y - intrinsics[1, 2]) / intrinsics[1, 1],
        1.0,
    ])
    world_direction = rotation.T @ camera_direction
    world_direction /= np.linalg.norm(world_direction)
    return center, world_direction


def _box_corners(center: np.ndarray, extents: np.ndarray) -> np.ndarray:
    signs = np.asarray([
        [x, y, z]
        for x in (-1.0, 1.0)
        for y in (-1.0, 1.0)
        for z in (-1.0, 1.0)
    ])
    return center + signs * extents


def solve_perspective_component_bounds(
    masks: dict[str, np.ndarray],
    views: list[dict[str, Any]],
    *,
    maximum_normalized_bbox_residual: float = 0.035,
) -> dict[str, Any]:
    """Fit an axis-aligned world box to calibrated perspective silhouette bounds."""
    if not 0 < maximum_normalized_bbox_residual <= 0.25:
        raise ValueError("maximum_normalized_bbox_residual must be in (0, 0.25]")
    view_map = {view["id"]: view for view in views}
    if len(view_map) != len(views) or set(masks) != set(view_map):
        raise ValueError("component masks and solver views must have unique matching ids")
    calibrated = []
    observations = {}
    ray_origins = []
    ray_directions = []
    for view_id, mask in masks.items():
        view = view_map[view_id]
        if view.get("projection") != "perspective" or view.get("world_to_camera") is None:
            continue
        _rotation, _translation, camera_center = _perspective_camera(view)
        ys, xs = np.nonzero(mask)
        bbox = np.asarray([xs.min(), ys.min(), xs.max(), ys.max()], dtype=float)
        pixel_center = (0.5 * (bbox[0] + bbox[2]), 0.5 * (bbox[1] + bbox[3]))
        origin, direction = _perspective_ray(view, pixel_center)
        calibrated.append(view)
        observations[view_id] = {"bbox_pixels": bbox.tolist(), "camera_center": camera_center.tolist()}
        ray_origins.append(origin)
        ray_directions.append(direction)
    if len(calibrated) < 2:
        return {"status": "UNDERCONSTRAINED", "issues": ["at least two calibrated perspective component views are required"], "used_view_ids": [view["id"] for view in calibrated]}
    identity = np.eye(3)
    triangulation_matrix = sum(identity - np.outer(direction, direction) for direction in ray_directions)
    triangulation_rhs = sum((identity - np.outer(direction, direction)) @ origin for origin, direction in zip(ray_origins, ray_directions))
    rank = int(np.linalg.matrix_rank(triangulation_matrix, tol=1e-8))
    condition = float(np.linalg.cond(triangulation_matrix))
    if rank < 3 or condition > 1e8:
        return {
            "status": "UNDERCONSTRAINED",
            "issues": [f"perspective center rays have rank {rank}/3 or condition {condition:.3g}"],
            "used_view_ids": [view["id"] for view in calibrated],
            "triangulation_rank": rank,
            "condition_number": condition,
        }
    center = np.linalg.solve(triangulation_matrix, triangulation_rhs)
    angular_sizes = []
    depths = []
    pixel_world_scales = []
    for view in calibrated:
        rotation, translation, _camera_center = _perspective_camera(view)
        camera_point = rotation @ center + translation
        if camera_point[2] <= 1e-4:
            return {"status": "REJECTED", "issues": [f"triangulated center is behind perspective view {view['id']}"]}
        bbox = np.asarray(observations[view["id"]]["bbox_pixels"])
        focal = camera_intrinsics(tuple(view["image_size"]), float(view["vertical_fov_degrees"]))[0, 0]
        half_pixels = 0.5 * np.asarray([bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1])
        angular_sizes.extend((half_pixels / focal * camera_point[2]).tolist())
        depths.append(float(camera_point[2]))
        pixel_world_scales.append(float(camera_point[2] / focal))
    initial_extent = max(float(np.median(angular_sizes)), max(pixel_world_scales))
    initial = np.concatenate((center, np.log(np.full(3, initial_extent))))
    median_depth = float(np.median(depths))
    center_span = max(initial_extent * 4.0, median_depth * 0.35)
    minimum_extent = max(max(pixel_world_scales) * 0.5, initial_extent * 0.08)
    maximum_extent = min(median_depth * 0.75, initial_extent * 6.0)
    if not np.isfinite([center_span, minimum_extent, maximum_extent]).all() or maximum_extent <= minimum_extent:
        return {
            "status": "REJECTED",
            "issues": ["calibrated perspective bounds do not admit a finite positive extent interval"],
            "used_view_ids": [view["id"] for view in calibrated],
        }
    lower = np.concatenate((center - center_span, np.log(np.full(3, minimum_extent))))
    upper = np.concatenate((center + center_span, np.log(np.full(3, maximum_extent))))

    def residual(parameters: np.ndarray) -> np.ndarray:
        trial_center = parameters[:3]
        trial_extents = np.exp(parameters[3:])
        corners = _box_corners(trial_center, trial_extents)
        values = []
        for view in calibrated:
            try:
                projected = project_vertices(corners, view)
                predicted = np.asarray([
                    projected[:, 0].min(), projected[:, 1].min(),
                    projected[:, 0].max(), projected[:, 1].max(),
                ])
                observed = np.asarray(observations[view["id"]]["bbox_pixels"])
                values.extend(((predicted - observed) / max(view["image_size"])).tolist())
            except ValueError:
                values.extend([1.0, 1.0, 1.0, 1.0])
        return np.asarray(values)

    fit = least_squares(residual, initial, bounds=(lower, upper), max_nfev=800, xtol=1e-10, ftol=1e-10, gtol=1e-10)
    fitted_center = fit.x[:3]
    fitted_extents = np.exp(fit.x[3:])
    final_residuals = residual(fit.x)
    maximum_residual = float(np.max(np.abs(final_residuals)))
    if not fit.success or maximum_residual > maximum_normalized_bbox_residual:
        return {
            "status": "REJECTED",
            "issues": [f"calibrated perspective boxes disagree by normalized residual {maximum_residual:.4f}"],
            "used_view_ids": [view["id"] for view in calibrated],
            "maximum_normalized_bbox_residual": maximum_residual,
            "observations": observations,
        }
    ray_miss = max(float(np.linalg.norm(np.cross(fitted_center - origin, direction))) for origin, direction in zip(ray_origins, ray_directions))
    uncertainty = min(0.4, max(0.1, maximum_residual * 5.0, ray_miss / max(float(np.max(fitted_extents)), 1e-8)))
    return {
        "status": "SOLVED",
        "method": "CALIBRATED_PERSPECTIVE_BBOX_FIT",
        "used_view_ids": [view["id"] for view in calibrated],
        "center": fitted_center.tolist(),
        "half_extents": fitted_extents.tolist(),
        "triangulation_rank": rank,
        "condition_number": condition,
        "maximum_normalized_bbox_residual": maximum_residual,
        "maximum_ray_miss": ray_miss,
        "relative_uncertainty": uncertainty,
        "world_per_pixel": max(pixel_world_scales),
        "observations": observations,
    }


def solve_registered_component_bounds(masks: dict[str, np.ndarray], views: list[dict[str, Any]]) -> dict[str, Any]:
    """Prefer a full-rank orthographic solve, then calibrated perspective evidence."""
    orthographic = solve_orthographic_component_bounds(masks, views)
    if orthographic["status"] == "SOLVED":
        return orthographic
    perspective = solve_perspective_component_bounds(masks, views)
    if perspective["status"] == "SOLVED":
        perspective["orthographic_attempt"] = orthographic
        return perspective
    return {
        "status": "UNDERCONSTRAINED" if "UNDERCONSTRAINED" in {orthographic["status"], perspective["status"]} else "REJECTED",
        "issues": [
            *(f"orthographic: {issue}" for issue in orthographic.get("issues", [])),
            *(f"perspective: {issue}" for issue in perspective.get("issues", [])),
        ],
        "orthographic_attempt": orthographic,
        "perspective_attempt": perspective,
    }


def _canonical_profile_view(views: list[dict[str, Any]], solved_view_ids: set[str]) -> dict[str, Any] | None:
    candidates = []
    for view in views:
        if view["id"] not in solved_view_ids:
            continue
        if view.get("projection", "orthographic") == "orthographic":
            rotation = view_rotation_matrix(view)
            alignment = min(abs(float(rotation[0, 0])), abs(float(rotation[2, 2])))
        elif view.get("projection") == "perspective" and view.get("world_to_camera") is not None:
            rotation, _translation, _center = _perspective_camera(view)
            alignment = min(abs(float(rotation[0, 0])), abs(float(rotation[1, 2])), abs(float(rotation[2, 1])))
        else:
            continue
        candidates.append((alignment, view))
    if not candidates or max(candidates, key=lambda item: item[0])[0] < 0.85:
        return None
    return copy.deepcopy(max(candidates, key=lambda item: item[0])[1])


def _pixel_to_local_xz(
    points: np.ndarray,
    view: dict[str, Any],
    center: np.ndarray,
) -> list[list[float]]:
    if view.get("projection", "orthographic") == "perspective":
        world_xz = []
        for point in points:
            origin, direction = _perspective_ray(view, (float(point[0]), float(point[1])))
            if abs(float(direction[1])) <= 1e-8:
                raise ValueError("perspective profile ray is parallel to the solved X/Z plane")
            distance = (float(center[1]) - float(origin[1])) / float(direction[1])
            if distance <= 0:
                raise ValueError("perspective profile ray intersects the solved X/Z plane behind the camera")
            world = origin + distance * direction
            world_xz.append([float(world[0] - center[0]), float(world[2] - center[2])])
        return world_xz
    width, height = view["image_size"]
    canvas = min(width, height)
    scale = float(view["world_scale"])
    horizontal = ((points[:, 0] - width * 0.5) / canvas - float(view["offset_x"])) * scale
    vertical = ((height * 0.5 - points[:, 1]) / canvas - float(view["offset_y"])) * scale
    rotation = view_rotation_matrix(view)
    matrix = rotation[[0, 2]][:, [0, 2]]
    rhs = np.column_stack((horizontal, vertical)) - np.asarray([
        rotation[0, 1] * center[1],
        rotation[2, 1] * center[1],
    ])
    world_xz = np.linalg.solve(matrix, rhs.T).T
    world_xz -= center[[0, 2]]
    return world_xz.tolist()


def _external_profile(mask: np.ndarray, view: dict[str, Any], center: np.ndarray) -> list[list[float]]:
    contours, _hierarchy = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(contour, True)
    approximation = cv2.approxPolyDP(contour, max(1.0, perimeter * 0.01), True)[:, 0, :].astype(float)
    if len(approximation) < 4:
        raise ValueError("component contour cannot initialize a four-point profile")
    return _pixel_to_local_xz(approximation, view, center)


def _resample_contour(contour: np.ndarray, count: int) -> np.ndarray:
    points = contour[:, 0, :].astype(float)
    closed = np.vstack((points, points[0]))
    lengths = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    samples = np.linspace(0.0, cumulative[-1], count, endpoint=False)
    result = []
    for sample in samples:
        index = min(int(np.searchsorted(cumulative, sample, side="right") - 1), len(points) - 1)
        factor = (sample - cumulative[index]) / max(lengths[index], 1e-12)
        result.append(closed[index] + factor * (closed[index + 1] - closed[index]))
    return np.asarray(result)


def _ring_profiles(mask: np.ndarray, view: dict[str, Any], center: np.ndarray, count: int = 12) -> tuple[list[list[float]], list[list[float]]]:
    contours, hierarchy = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None:
        raise ValueError("component mask has no contour hierarchy")
    hierarchy = hierarchy[0]
    outers = [index for index, item in enumerate(hierarchy) if item[3] == -1]
    outer_index = max(outers, key=lambda index: cv2.contourArea(contours[index]))
    holes = [index for index, item in enumerate(hierarchy) if item[3] == outer_index]
    if len(holes) != 1:
        raise ValueError("ring extrusion initialization requires exactly one enclosed hole")
    outer = _resample_contour(contours[outer_index], count)
    inner = _resample_contour(contours[holes[0]], count)
    return _pixel_to_local_xz(outer, view, center), _pixel_to_local_xz(inner, view, center)


def _width_profile(mask: np.ndarray, view: dict[str, Any], center: np.ndarray, samples: int = 5) -> list[tuple[float, float]]:
    ys, _xs = np.nonzero(mask)
    rows = np.linspace(int(ys.min()), int(ys.max()), samples).round().astype(int)
    result = []
    for row in rows:
        xs = np.flatnonzero(mask[row])
        if not len(xs):
            continue
        endpoints = np.asarray([[xs.min(), row], [xs.max(), row]], dtype=float)
        local = np.asarray(_pixel_to_local_xz(endpoints, view, center))
        result.append((float(local[:, 1].mean()), float(abs(local[1, 0] - local[0, 0]) * 0.5)))
    result.sort()
    return result


def _candidate_variables(center: np.ndarray, extents: np.ndarray, uncertainty: float, world_per_pixel: float) -> list[dict[str, Any]]:
    variables = []
    for index, axis in enumerate("xyz"):
        translation_span = max(world_per_pixel * 2.0, extents[index] * uncertainty)
        variables.append({"pointer": f"/shape/translate_{axis}", "bounds": [float(center[index] - translation_span), float(center[index] + translation_span)]})
        variables.append({"pointer": f"/shape/scale_{axis}", "bounds": [float(max(0.5, 1.0 - uncertainty)), float(1.0 + uncertainty)]})
    return variables


def _base_candidate(component_id: str, family: str, shape: dict[str, Any], views: list[dict[str, Any]], variables: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "candidate_id": f"{component_id}-{family}",
        "shape": shape,
        "views": copy.deepcopy(views),
        "variables": copy.deepcopy(variables),
        "acceptance": {"max_mean_view_loss": 0.18, "max_each_view_loss": 0.25, "require_hole_count_match": True},
        "initialization": {"source": "REGISTERED_COMPONENT_MASK_BOUNDS", "component_id": component_id},
    }


def initialize_component_candidates(
    bundle: dict[str, Any],
    assembly_hypotheses: dict[str, Any],
) -> dict[str, Any]:
    """Create executable generic candidates without target-specific coordinates."""
    if bundle.get("record_type") != "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE" or not bundle.get("accepted_for_shape_solving"):
        raise ValueError("candidate initialization requires an accepted multiview bundle")
    if assembly_hypotheses.get("record_type") != "ASSEMBLY_HYPOTHESIS_SET" or assembly_hypotheses.get("target_id") != bundle.get("target_id"):
        raise ValueError("candidate initialization requires matching assembly hypotheses")
    if assembly_hypotheses.get("target_variant") not in {None, bundle.get("target_variant")}:
        raise ValueError("candidate initialization requires the same target variant")
    component_ids = [component.get("component_id") for component in assembly_hypotheses.get("components", [])]
    if any(not component_id for component_id in component_ids) or len(component_ids) != len(set(component_ids)):
        raise ValueError("assembly components must have unique non-empty ids")
    bundled_components = set(bundle.get("component_support", component_ids))
    if set(component_ids) != bundled_components:
        raise ValueError("assembly components must exactly match bundled component support")
    candidates_by_component = {}
    reports = {}
    for component in assembly_hypotheses.get("components", []):
        component_id = component["component_id"]
        masks, views = _component_masks(bundle, component_id)
        bounds = solve_registered_component_bounds(masks, views)
        report = {"bounds": bounds, "families": {}}
        candidates = []
        if bounds["status"] == "SOLVED":
            center = np.asarray(bounds["center"], dtype=float)
            extents = np.asarray(bounds["half_extents"], dtype=float)
            profile_view = _canonical_profile_view(views, set(bounds["used_view_ids"]))
            if profile_view is None:
                report["issues"] = ["no registered view has a stable X/Z profile plane"]
            else:
                mask = masks[profile_view["id"]]
                variables = _candidate_variables(center, extents, bounds["relative_uncertainty"], bounds["world_per_pixel"])
                declared = [item["family"] for item in component.get("representation_candidates", [])]
                width_profile = _width_profile(mask, profile_view, center)
                for family in declared:
                    try:
                        if family == "section_loft":
                            depth_ratio = extents[1] / max(extents[0], 1e-8)
                            shape = {
                                "family": family,
                                "segments": 12,
                                "cross_section": "box",
                                "translate_x": float(center[0]), "translate_y": float(center[1]), "translate_z": float(center[2]),
                                "stations": [
                                    {"z": z, "half_width": max(width, bounds["world_per_pixel"]), "half_depth": max(width * depth_ratio, bounds["world_per_pixel"]), "power": 4.0}
                                    for z, width in width_profile
                                ],
                            }
                        elif family == "profile_extrusion":
                            shape = {
                                "family": family,
                                "translate_x": float(center[0]), "translate_y": float(center[1]), "translate_z": float(center[2]),
                                "profile": _external_profile(mask, profile_view, center),
                                "depth_stations": [{"y": float(-extents[1])}, {"y": float(extents[1])}],
                            }
                        elif family == "profile_ring_extrusion":
                            outer, inner = _ring_profiles(mask, profile_view, center)
                            shape = {
                                "family": family,
                                "translate_x": float(center[0]), "translate_y": float(center[1]), "translate_z": float(center[2]),
                                "outer_profile": outer,
                                "inner_profile": inner,
                                "depth_stations": [{"y": float(-extents[1])}, {"y": float(extents[1])}],
                            }
                        elif family == "profile_revolution":
                            radial_error = abs(extents[0] - extents[1]) / max(extents[0], extents[1])
                            if radial_error > 0.25:
                                raise ValueError(f"solved transverse extents are not radial enough ({radial_error:.3f})")
                            shape = {
                                "family": family,
                                "segments": 12,
                                "translate_x": float(center[0]), "translate_y": float(center[1]), "translate_z": float(center[2]),
                                "profile": [[max(width, bounds["world_per_pixel"]), z] for z, width in width_profile],
                            }
                        else:
                            raise ValueError("family has no evidence-derived initializer")
                        candidates.append(validate_hypothesis(_base_candidate(component_id, family, shape, views, variables)))
                        report["families"][family] = {"status": "INITIALIZED"}
                    except ValueError as error:
                        report["families"][family] = {"status": "NOT_INITIALIZED", "reason": str(error)}
        candidates_by_component[component_id] = candidates
        report["candidate_count"] = len(candidates)
        report["status"] = "READY" if len(candidates) >= 2 else "INSUFFICIENT_FAMILY_COVERAGE"
        reports[component_id] = report
    ready = bool(reports) and all(report["status"] == "READY" for report in reports.values())
    return {
        "schema_version": 1,
        "record_type": "INITIALIZED_COMPONENT_CANDIDATE_SET",
        "target_id": bundle.get("target_id"),
        "target_variant": bundle.get("target_variant"),
        "components": candidates_by_component,
        "initialization_reports": reports,
        "source_evidence": {
            view.get("view_id"): {
                "source_sha256": view.get("source_sha256"),
                "mask_sha256": (view.get("component_evidence") or {}).get("label_map", {}).get("sha256"),
                "projection": (view.get("solver_view") or {}).get("projection", "orthographic"),
            }
            for view in bundle.get("views", [])
        },
        "ready_for_component_fitting": ready,
        "claim_boundary": "Initialization is derived from full-rank registered orthographic bounds or calibrated multiview perspective bounds. It does not infer camera calibration, component correspondence, hidden concavity, sweep paths, multiple holes, or final topology.",
    }
