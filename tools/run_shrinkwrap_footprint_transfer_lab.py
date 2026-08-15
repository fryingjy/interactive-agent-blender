"""Test vertex-group-scoped Shrinkwrap Project for curved-host mounting feet.

The fixture is a closed all-quad mounting block whose 25 lower-footprint
vertices are grouped separately from its 25 upper structure vertices.
Controls distinguish scoped conformance, destructive unscoped conformance,
wrong projection direction, and transfer from a sphere to a cylinder.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_shrinkwrap-footprint-transfer"
GRID = 5
NAMES = (
    "A_Sphere_Scoped",
    "B_Sphere_Unscoped",
    "C_Sphere_WrongDirection",
    "D_Cylinder_Scoped_Transfer",
)


def host(name: str, center_x: float, kind: str):
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0, location=(center_x, 0.0, 0.0))
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1.0, depth=2.4, location=(center_x, 0.0, 0.0), rotation=(math.pi / 2, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    for face in obj.data.polygons:
        face.use_smooth = True
    obj.color = (0.12, 0.18, 0.24, 1.0)
    return obj


def mount(name: str, center_x: float):
    values = [-0.44, -0.22, 0.0, 0.22, 0.44]
    vertices = []
    for z in (1.16, 1.58):
        vertices.extend((center_x + x, y, z) for y in values for x in values)
    faces = []
    for layer in (0, 1):
        start = layer * GRID * GRID
        for y in range(GRID - 1):
            for x in range(GRID - 1):
                a = start + y * GRID + x
                b = a + 1
                d = start + (y + 1) * GRID + x
                c = d + 1
                faces.append((a, d, c, b) if layer == 0 else (a, b, c, d))
    perimeter = []
    perimeter.extend(range(GRID))
    perimeter.extend(row * GRID + GRID - 1 for row in range(1, GRID))
    perimeter.extend((GRID - 1) * GRID + x for x in range(GRID - 2, -1, -1))
    perimeter.extend(row * GRID for row in range(GRID - 2, 0, -1))
    top_offset = GRID * GRID
    for index, lower in enumerate(perimeter):
        next_lower = perimeter[(index + 1) % len(perimeter)]
        faces.append((lower, next_lower, top_offset + next_lower, top_offset + lower))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    group = obj.vertex_groups.new(name="MountFootprint")
    group.add(list(range(GRID * GRID)), 1.0, "REPLACE")
    obj.color = (0.62, 0.27, 0.09, 1.0)
    return obj


def add_project(obj, target, *, scoped: bool, negative: bool):
    modifier = obj.modifiers.new("Project mounting footprint", "SHRINKWRAP")
    modifier.target = target
    modifier.wrap_method = "PROJECT"
    modifier.wrap_mode = "ON_SURFACE"
    modifier.use_project_x = False
    modifier.use_project_y = False
    modifier.use_project_z = True
    modifier.use_negative_direction = negative
    modifier.use_positive_direction = not negative
    modifier.offset = 0.015
    modifier.vertex_group = "MountFootprint" if scoped else ""
    return modifier


def evaluated_points(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def health(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
        "minimum_face_area": min(face.calc_area() for face in bm.faces),
        "signed_volume": bm.calc_volume(signed=True),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def record(obj, target, kind: str, scoped: bool, negative: bool):
    base = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    final = evaluated_points(obj)
    lower = range(GRID * GRID)
    upper = range(GRID * GRID, GRID * GRID * 2)
    lower_moves = [(final[index] - base[index]).length for index in lower]
    upper_moves = [(final[index] - base[index]).length for index in upper]
    center_x = target.location.x
    surface_errors = []
    for index in lower:
        point = final[index]
        local_x = point.x - center_x
        if kind == "sphere":
            expected_z = math.sqrt(max(0.0, 1.0 - local_x * local_x - point.y * point.y)) + 0.015
        else:
            expected_z = math.sqrt(max(0.0, 1.0 - local_x * local_x)) + 0.015
        surface_errors.append(abs(point.z - expected_z))
    return {
        "host_kind": kind,
        "scoped": scoped,
        "negative_projection": negative,
        "modifier_vertex_group": obj.modifiers[0].vertex_group,
        "lower_vertices_moved": sum(value > 1e-5 for value in lower_moves),
        "lower_mean_displacement": sum(lower_moves) / len(lower_moves),
        "upper_vertices_moved": sum(value > 1e-5 for value in upper_moves),
        "upper_max_displacement": max(upper_moves),
        "lower_surface_error_mean": sum(surface_errors) / len(surface_errors),
        "lower_surface_error_max": max(surface_errors),
        "health": health(obj),
    }


def render(path: Path, hosts, mounts):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "MATCAP"
    scene.display.shading.studio_light = "hard_surface_grey.exr"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 520
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Evidence World")
    scene.world.color = (0.02, 0.025, 0.035)
    bpy.ops.object.camera_add(location=(8.8, -14.5, 7.2))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 13.5
    camera.rotation_euler = (Vector((0.0, 0.0, 0.5)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    specs = (
        (NAMES[0], -5.1, "sphere", True, True),
        (NAMES[1], -1.7, "sphere", False, True),
        (NAMES[2], 1.7, "sphere", True, False),
        (NAMES[3], 5.1, "cylinder", True, True),
    )
    records = {}
    hosts = []
    mounts = []
    for name, x, kind, scoped, negative in specs:
        target = host(f"{name}_Host", x, kind)
        source = mount(name, x)
        add_project(source, target, scoped=scoped, negative=negative)
        hosts.append(target)
        mounts.append(source)
        records[name] = record(source, target, kind, scoped, negative)

    scoped_sphere = records[NAMES[0]]
    unscoped = records[NAMES[1]]
    wrong = records[NAMES[2]]
    transfer = records[NAMES[3]]
    assertions = {
        "scoped_sphere_moves_all_footprint_vertices": scoped_sphere["lower_vertices_moved"] == GRID * GRID,
        "scoped_sphere_preserves_all_upper_structure_vertices": scoped_sphere["upper_vertices_moved"] == 0 and scoped_sphere["upper_max_displacement"] < 1e-6,
        "unscoped_control_deforms_upper_structure": unscoped["upper_vertices_moved"] == GRID * GRID and unscoped["upper_max_displacement"] > 0.2,
        "wrong_direction_control_is_noop": wrong["lower_vertices_moved"] == 0 and wrong["upper_vertices_moved"] == 0,
        "cylinder_transfer_moves_only_footprint": transfer["lower_vertices_moved"] == GRID * GRID and transfer["upper_vertices_moved"] == 0,
        "scoped_footprints_land_near_analytic_hosts": scoped_sphere["lower_surface_error_max"] < 0.04 and transfer["lower_surface_error_max"] < 0.04,
        "successful_scoped_mounts_remain_closed_quad_manifold": all(item["health"]["non_manifold_edges"] == 0 and item["health"]["ngons"] == 0 and item["health"]["degenerate_faces"] == 0 and item["health"]["signed_volume"] > 0.1 for item in (scoped_sphere, transfer)),
        "unscoped_control_collapses_into_degenerate_geometry": unscoped["health"]["degenerate_faces"] > 0 and unscoped["health"]["signed_volume"] < 1e-5,
        "wrong_direction_noop_preserves_clean_base": wrong["health"]["degenerate_faces"] == 0 and wrong["health"]["signed_volume"] > 0.1,
    }
    render_path = OUT / "shrinkwrap_footprint_matcap.png"
    render(render_path, hosts, mounts)
    report = {
        "lab": "vertex_group_scoped_shrinkwrap_project_attachment",
        "blender_version": bpy.app.version_string,
        "fixture": "closed 50-vertex/48-quad mount with a 25-vertex lower footprint group and 25 ungrouped upper vertices",
        "records": records,
        "assertions": assertions,
        "scope_boundary": [
            "This validates deformation of a separate secondary mount's contact footprint; it does not weld the mount into the host mesh.",
            "Use separate construction only when the design calls for a movable, bolted, or assembled component. A continuous cast/welded form still requires connected topology or a deliberate boolean/retopology workflow.",
            "Projection direction is local-axis dependent and must be tested; a valid modifier can be a complete no-op.",
        ],
        "render": render_path.name,
        "pass": all(assertions.values()) and render_path.exists() and render_path.stat().st_size > 0,
    }
    (OUT / "shrinkwrap_footprint_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "shrinkwrap_footprint_transfer.blend"))
    print("SHRINKWRAP_FOOTPRINT_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
