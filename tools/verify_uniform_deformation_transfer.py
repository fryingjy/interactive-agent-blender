"""Independent saved-scene verifier for the uniform deformation transfer lab.

This intentionally does not import the modeling script or its helper functions.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import bmesh
import bpy


def parse_args() -> tuple[Path, Path]:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 2:
        raise SystemExit("expected BLEND_PATH OUTPUT_JSON after --")
    return Path(values[0]).resolve(), Path(values[1]).resolve()


def expected_radius(z: float) -> float:
    t = z / 2.5
    return 0.55 + 0.50 * abs(t) ** 1.8 + 0.18 * max(0.0, -t) ** 2


def groups_by_z(obj: bpy.types.Object) -> list[tuple[float, list[float]]]:
    groups: dict[float, list[float]] = {}
    for vertex in obj.data.vertices:
        z = round(vertex.co.z, 7)
        groups.setdefault(z, []).append(math.hypot(vertex.co.x, vertex.co.y))
    return sorted((z, radii) for z, radii in groups.items())


def interpolate_error(groups: list[tuple[float, list[float]]]) -> tuple[float, float]:
    z_values = [group[0] for group in groups]
    radii = [statistics.mean(group[1]) for group in groups]
    errors = []
    for index in range(501):
        z = -2.5 + 5.0 * index / 500.0
        interval = min(len(z_values) - 2, max(0, next((i for i in range(len(z_values) - 1) if z_values[i + 1] >= z), len(z_values) - 2)))
        alpha = (z - z_values[interval]) / (z_values[interval + 1] - z_values[interval])
        radius = radii[interval] * (1.0 - alpha) + radii[interval + 1] * alpha
        errors.append(radius - expected_radius(z))
    return math.sqrt(sum(error * error for error in errors) / len(errors)), max(abs(error) for error in errors)


def inspect_object(obj: bpy.types.Object) -> dict[str, object]:
    groups = groups_by_z(obj)
    spacings = [b[0] - a[0] for a, b in zip(groups, groups[1:])]
    spacing_cv = statistics.pstdev(spacings) / statistics.mean(spacings)
    radius_variation = max(max(radii) - min(radii) for _, radii in groups)
    angular_gap_errors = []
    for z, _ in groups:
        angles = sorted(
            math.atan2(vertex.co.y, vertex.co.x) % (2.0 * math.pi)
            for vertex in obj.data.vertices
            if abs(vertex.co.z - z) < 1e-6
        )
        gaps = [
            (angles[(index + 1) % len(angles)] - angles[index]) % (2.0 * math.pi)
            for index in range(len(angles))
        ]
        angular_gap_errors.append(max(abs(gap - 2.0 * math.pi / 12.0) for gap in gaps))

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
    side_aspects = []
    for face in bm.faces:
        if len({round(vertex.co.z, 7) for vertex in face.verts}) != 2:
            continue
        lengths = [edge.calc_length() for edge in face.edges]
        side_aspects.append(max(lengths) / min(lengths))
    side_aspects.sort()
    p95 = side_aspects[min(len(side_aspects) - 1, math.ceil(0.95 * len(side_aspects)) - 1)]
    base = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "non_quad_faces": sum(1 for face in bm.faces if len(face.verts) != 4),
        "non_manifold_edges": sum(1 for edge in bm.edges if not edge.is_manifold),
        "degenerate_faces": sum(1 for face in bm.faces if face.calc_area() < 1e-10),
        "connected_components": components,
    }
    bm.free()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh()
    evaluated_bm = bmesh.new()
    evaluated_bm.from_mesh(evaluated_mesh)
    evaluated_stats = {
        "non_manifold_edges": sum(1 for edge in evaluated_bm.edges if not edge.is_manifold),
        "degenerate_faces": sum(1 for face in evaluated_bm.faces if face.calc_area() < 1e-10),
    }
    evaluated_bm.free()
    evaluated.to_mesh_clear()

    rmse, max_error = interpolate_error(groups)
    weight_attribute = obj.data.attributes.get("bevel_weight_edge")
    return {
        "base": base,
        "ring_count": len(groups),
        "vertices_per_ring": sorted({len(radii) for _, radii in groups}),
        "ring_radius_variation_max": radius_variation,
        "angular_gap_error_max": max(angular_gap_errors),
        "ring_spacing_cv": spacing_cv,
        "profile_rmse": rmse,
        "profile_max_abs_error": max_error,
        "side_quad_aspect_p95": p95,
        "modifier_types": [modifier.type for modifier in obj.modifiers],
        "bevel_limit_method": obj.modifiers[0].limit_method if obj.modifiers else None,
        "weighted_edge_count": sum(1 for value in weight_attribute.data if value.value > 0.999) if weight_attribute else 0,
        "shading_policy": obj.get("shading_policy"),
        "evaluated": evaluated_stats,
    }


def main() -> None:
    blend_path, output_path = parse_args()
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    expected_names = ["A_Manual_Stepped_Control", "B_Uniform_Ring_Candidate"]
    objects = {name: bpy.data.objects.get(name) for name in expected_names}
    control = inspect_object(objects[expected_names[0]]) if objects[expected_names[0]] else None
    candidate = inspect_object(objects[expected_names[1]]) if objects[expected_names[1]] else None
    checks = {
        "exact_objects_present": all(objects.values()),
        "base_topology_identical": bool(control and candidate and control["base"] == candidate["base"]),
        "base_mesh_counts_expected": bool(control and candidate and all(
            item["base"]["vertices"] == 156 and item["base"]["faces"] == 154
            for item in (control, candidate)
        )),
        "connected_all_quad_manifold": bool(control and candidate and all(
            item["base"]["connected_components"] == 1
            and item["base"]["non_quad_faces"] == 0
            and item["base"]["non_manifold_edges"] == 0
            and item["base"]["degenerate_faces"] == 0
            for item in (control, candidate)
        )),
        "twelve_vertices_per_ring": bool(control and candidate and all(
            item["ring_count"] == 13 and item["vertices_per_ring"] == [12]
            for item in (control, candidate)
        )),
        "rings_are_circular": bool(control and candidate and all(
            item["ring_radius_variation_max"] < 1e-6 and item["angular_gap_error_max"] < 1e-6
            for item in (control, candidate)
        )),
        "uniform_spacing_gate": bool(candidate and candidate["ring_spacing_cv"] <= 0.000001),
        "negative_control_spacing_gate": bool(control and control["ring_spacing_cv"] >= 0.25),
        "profile_rmse_improves": bool(control and candidate and candidate["profile_rmse"] <= control["profile_rmse"] * 0.60),
        "profile_max_error_improves": bool(control and candidate and candidate["profile_max_abs_error"] < control["profile_max_abs_error"]),
        "quad_density_improves": bool(control and candidate and candidate["side_quad_aspect_p95"] < control["side_quad_aspect_p95"]),
        "semantic_shading_policy": bool(control and candidate and all(
            item["modifier_types"] == ["BEVEL", "SUBSURF"]
            and item["bevel_limit_method"] == "WEIGHT"
            and item["weighted_edge_count"] == 24
            and item["shading_policy"] == "SMOOTH_BY_ANGLE"
            for item in (control, candidate)
        )),
        "evaluated_meshes_clean": bool(control and candidate and all(
            item["evaluated"]["non_manifold_edges"] == 0
            and item["evaluated"]["degenerate_faces"] == 0
            for item in (control, candidate)
        )),
    }
    result = {
        "blender_version": bpy.app.version_string,
        "blend_path": str(blend_path),
        "independent_of_modeling_script": True,
        "control": control,
        "candidate": candidate,
        "checks": checks,
        "pass": all(checks.values()),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["pass"] else 2)


if __name__ == "__main__":
    main()
