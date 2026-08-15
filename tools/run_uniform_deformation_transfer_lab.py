"""Transfer-test a video-derived deformation principle on a circular product form.

This is a deterministic controlled experiment, not evidence of adaptive modeling.
It compares a declared manual-step negative control against a uniform-ring candidate
with identical connected all-quad topology and modifier policy.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
import object_ops  # noqa: E402
import persistent_ids  # noqa: E402
from render_passes import render_diagnostic_pass  # noqa: E402


RADIAL_SEGMENTS = 12
RING_COUNT = 13
Z_MIN = -2.5
Z_MAX = 2.5
MANUAL_FRACTIONS = (0.0, 0.08, 0.16, 0.24, 0.32, 0.41, 0.59, 0.68, 0.76, 0.84, 0.91, 0.96, 1.0)
MANUAL_RADIUS_ERRORS = (0.0, 0.018, -0.024, 0.030, -0.026, 0.022, -0.036, 0.027, -0.020, 0.022, -0.016, 0.010, 0.0)


def parse_output_dir() -> Path:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    output = Path(values[0]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


def target_radius(z: float) -> float:
    t = z / 2.5
    return 0.55 + 0.50 * abs(t) ** 1.8 + 0.18 * max(0.0, -t) ** 2


def cap_faces(ring_start: int, reverse: bool) -> list[tuple[int, int, int, int]]:
    faces = []
    for offset in range((RADIAL_SEGMENTS // 2) - 1):
        face = (
            ring_start + offset,
            ring_start + offset + 1,
            ring_start + RADIAL_SEGMENTS - 2 - offset,
            ring_start + RADIAL_SEGMENTS - 1 - offset,
        )
        faces.append(tuple(reversed(face)) if reverse else face)
    return faces


def build_pedestal(name: str, z_values: list[float], radii: list[float], x_location: float, color) -> bpy.types.Object:
    vertices = []
    for z, radius in zip(z_values, radii):
        for segment in range(RADIAL_SEGMENTS):
            angle = 2.0 * math.pi * segment / RADIAL_SEGMENTS
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z))

    faces = []
    for ring in range(RING_COUNT - 1):
        lower = ring * RADIAL_SEGMENTS
        upper = (ring + 1) * RADIAL_SEGMENTS
        for segment in range(RADIAL_SEGMENTS):
            next_segment = (segment + 1) % RADIAL_SEGMENTS
            faces.append((
                lower + segment,
                lower + next_segment,
                upper + next_segment,
                upper + segment,
            ))
    faces.extend(cap_faces(0, reverse=True))
    faces.extend(cap_faces((RING_COUNT - 1) * RADIAL_SEGMENTS, reverse=False))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location.x = x_location

    material = bpy.data.materials.new(f"{name}_Material")
    material.diffuse_color = (*color, 1.0)
    obj.data.materials.append(material)

    persistent_ids.ensure_persistent_ids(name)
    edge_ids = persistent_ids.get_id_maps(name)["edges"]["index_to_id"]
    weighted = []
    for edge in mesh.edges:
        index0, index1 = edge.vertices
        z0 = mesh.vertices[index0].co.z
        z1 = mesh.vertices[index1].co.z
        angular_delta = abs((index0 % RADIAL_SEGMENTS) - (index1 % RADIAL_SEGMENTS))
        is_adjacent_perimeter_pair = angular_delta in {1, RADIAL_SEGMENTS - 1}
        if (
            abs(z0 - z1) < 1e-8
            and (abs(z0 - Z_MIN) < 1e-8 or abs(z0 - Z_MAX) < 1e-8)
            and is_adjacent_perimeter_pair
        ):
            weighted.append(edge_ids[edge.index])
    weight_result = object_ops.set_bevel_weight_by_ids(name, weighted, weight=1.0, clear_others=True)
    obj["transfer_weight_result"] = json.dumps(weight_result, sort_keys=True)

    bevel = obj.modifiers.new("Semantic cap edge radius", "BEVEL")
    bevel.limit_method = "WEIGHT"
    bevel.width = 0.035
    bevel.segments = 2
    subd = obj.modifiers.new("Uniform profile smoothing", "SUBSURF")
    subd.subdivision_type = "CATMULL_CLARK"
    subd.levels = 1
    subd.render_levels = 1
    object_ops.set_smooth_by_angle(name, angle=math.radians(30.0), keep_sharp_edges=True)
    return obj


def profile_metrics(z_values: list[float], radii: list[float]) -> dict[str, float]:
    spacings = [b - a for a, b in zip(z_values, z_values[1:])]
    spacing_cv = statistics.pstdev(spacings) / statistics.mean(spacings)
    samples = [Z_MIN + (Z_MAX - Z_MIN) * index / 500.0 for index in range(501)]
    errors = []
    for z in samples:
        interval = min(len(z_values) - 2, max(0, next((i for i in range(len(z_values) - 1) if z_values[i + 1] >= z), len(z_values) - 2)))
        z0, z1 = z_values[interval], z_values[interval + 1]
        alpha = 0.0 if z1 == z0 else (z - z0) / (z1 - z0)
        interpolated = radii[interval] * (1.0 - alpha) + radii[interval + 1] * alpha
        errors.append(interpolated - target_radius(z))
    return {
        "ring_spacing_cv": spacing_cv,
        "profile_rmse": math.sqrt(sum(error * error for error in errors) / len(errors)),
        "profile_max_abs_error": max(abs(error) for error in errors),
    }


def mesh_metrics(obj: bpy.types.Object) -> dict[str, object]:
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    components = 0
    unseen = set(bm.verts)
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
    non_manifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    degenerate = sum(1 for face in bm.faces if face.calc_area() < 1e-10)
    ngon_count = sum(1 for face in bm.faces if len(face.verts) != 4)
    side_aspects = []
    for face in bm.faces:
        unique_z = {round(vertex.co.z, 8) for vertex in face.verts}
        if len(unique_z) != 2:
            continue
        lengths = [edge.calc_length() for edge in face.edges]
        side_aspects.append(max(lengths) / min(lengths))
    bm.free()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh()
    evaluated_bm = bmesh.new()
    evaluated_bm.from_mesh(evaluated_mesh)
    evaluated_stats = {
        "vertices": len(evaluated_bm.verts),
        "faces": len(evaluated_bm.faces),
        "non_manifold_edges": sum(1 for edge in evaluated_bm.edges if not edge.is_manifold),
        "degenerate_faces": sum(1 for face in evaluated_bm.faces if face.calc_area() < 1e-10),
    }
    evaluated_bm.free()
    evaluated.to_mesh_clear()
    side_aspects.sort()
    p95_index = min(len(side_aspects) - 1, math.ceil(0.95 * len(side_aspects)) - 1)
    return {
        "base_vertices": len(mesh.vertices),
        "base_edges": len(mesh.edges),
        "base_faces": len(mesh.polygons),
        "connected_components": components,
        "non_manifold_edges": non_manifold,
        "degenerate_faces": degenerate,
        "non_quad_faces": ngon_count,
        "side_quad_aspect_p95": side_aspects[p95_index],
        "side_quad_aspect_max": max(side_aspects),
        "modifier_types": [modifier.type for modifier in obj.modifiers],
        "weighted_edge_count": sum(
            1 for value in mesh.attributes["bevel_weight_edge"].data if value.value > 0.999
        ),
        "shading_policy": obj.get("shading_policy"),
        "evaluated": evaluated_stats,
    }


def render_comparison(output: Path, objects: list[bpy.types.Object], label: str, wireframe: bool, isometric: bool) -> str:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_specular_highlight = True
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Transfer Lab World")
    scene.world.color = (0.035, 0.035, 0.045)
    for obj in objects:
        obj.show_wire = wireframe
        obj.show_all_edges = wireframe

    camera_data = bpy.data.cameras.new(f"Camera_{label}")
    camera = bpy.data.objects.new(f"Camera_{label}", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 7.0 if not isometric else 7.7
    camera.location = (7.5, -10.0, 5.5) if isometric else (0.0, -12.0, 0.0)
    direction = Vector((0.0, 0.0, 0.0)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    path = output / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    return str(path)


def render_base_cage_wire(output: Path, objects: list[bpy.types.Object]) -> dict[str, object]:
    modifier_states = {
        obj.name: [modifier.show_viewport for modifier in obj.modifiers]
        for obj in objects
    }
    for obj in objects:
        for modifier in obj.modifiers:
            modifier.show_viewport = False
    path = output / "comparison_front_wire.png"
    try:
        metadata = render_diagnostic_pass(
            [obj.name for obj in objects],
            str(path),
            "wireframe",
            view="front",
            resolution=1000,
            margin=1.12,
        )
    finally:
        for obj in objects:
            for modifier, state in zip(obj.modifiers, modifier_states[obj.name]):
                modifier.show_viewport = state
    return {"path": str(path), "metadata": metadata, "base_cage": True}


def main() -> None:
    output = parse_output_dir()
    bpy.ops.wm.read_factory_settings(use_empty=True)

    uniform_z = [Z_MIN + (Z_MAX - Z_MIN) * index / (RING_COUNT - 1) for index in range(RING_COUNT)]
    manual_z = [Z_MIN + (Z_MAX - Z_MIN) * fraction for fraction in MANUAL_FRACTIONS]
    uniform_radii = [target_radius(z) for z in uniform_z]
    manual_radii = [target_radius(z) + error for z, error in zip(manual_z, MANUAL_RADIUS_ERRORS)]

    control = build_pedestal("A_Manual_Stepped_Control", manual_z, manual_radii, -1.75, (0.58, 0.17, 0.10))
    candidate = build_pedestal("B_Uniform_Ring_Candidate", uniform_z, uniform_radii, 1.75, (0.08, 0.34, 0.62))

    control_metrics = {**profile_metrics(manual_z, manual_radii), **mesh_metrics(control)}
    candidate_metrics = {**profile_metrics(uniform_z, uniform_radii), **mesh_metrics(candidate)}
    assertions = {
        "both_connected": control_metrics["connected_components"] == candidate_metrics["connected_components"] == 1,
        "both_manifold": control_metrics["non_manifold_edges"] == candidate_metrics["non_manifold_edges"] == 0,
        "both_all_quad": control_metrics["non_quad_faces"] == candidate_metrics["non_quad_faces"] == 0,
        "identical_base_vertex_face_counts": (
            control_metrics["base_vertices"] == candidate_metrics["base_vertices"]
            and control_metrics["base_faces"] == candidate_metrics["base_faces"]
        ),
        "candidate_spacing_uniform": candidate_metrics["ring_spacing_cv"] <= 0.000001,
        "control_spacing_is_uneven": control_metrics["ring_spacing_cv"] >= 0.25,
        "candidate_profile_rmse_ratio": (
            candidate_metrics["profile_rmse"] <= control_metrics["profile_rmse"] * 0.60
        ),
        "candidate_max_profile_error_lower": (
            candidate_metrics["profile_max_abs_error"] < control_metrics["profile_max_abs_error"]
        ),
        "candidate_side_quad_p95_better": (
            candidate_metrics["side_quad_aspect_p95"] < control_metrics["side_quad_aspect_p95"]
        ),
        "semantic_cap_weights_complete": (
            control_metrics["weighted_edge_count"] == candidate_metrics["weighted_edge_count"] == 24
        ),
        "modifier_policy_matches": (
            control_metrics["modifier_types"] == candidate_metrics["modifier_types"] == ["BEVEL", "SUBSURF"]
            and control_metrics["shading_policy"] == candidate_metrics["shading_policy"] == "SMOOTH_BY_ANGLE"
        ),
        "evaluated_meshes_clean": all(
            metrics["evaluated"][key] == 0
            for metrics in (control_metrics, candidate_metrics)
            for key in ("non_manifold_edges", "degenerate_faces")
        ),
    }

    renders = {
        "front_solid": render_comparison(output, [control, candidate], "comparison_front_solid", False, False),
        "front_wire": render_base_cage_wire(output, [control, candidate]),
        "isometric_solid": render_comparison(output, [control, candidate], "comparison_isometric_solid", False, True),
    }
    blend_path = output / "uniform_deformation_transfer.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report = {
        "blender_version": bpy.app.version_string,
        "experiment_type": "deterministic controlled transfer; not adaptive modeling evidence",
        "source_video": "yi87Dap_WOc",
        "source_asset": "anvil waist",
        "transfer_asset": "12-sided circular lamp pedestal",
        "control": control_metrics,
        "candidate": candidate_metrics,
        "improvement": {
            "profile_rmse_ratio": candidate_metrics["profile_rmse"] / control_metrics["profile_rmse"],
            "profile_rmse_reduction_percent": 100.0 * (1.0 - candidate_metrics["profile_rmse"] / control_metrics["profile_rmse"]),
            "side_quad_aspect_p95_reduction_percent": 100.0 * (
                1.0 - candidate_metrics["side_quad_aspect_p95"] / control_metrics["side_quad_aspect_p95"]
            ),
        },
        "renders": renders,
        "blend_file": str(blend_path),
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (output / "lab_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
