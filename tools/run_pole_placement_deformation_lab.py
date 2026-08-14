"""Test retopology pole placement on a bending non-face tube.

The Blender Studio lesson argues that loop redirection/poles should serve
patch structure and stay out of important deformation/crease zones when
possible. This lab puts the same diagonal 5-pole pair either far from or
inside the bend zone, then compares both to an all-quad reference after
Subdivision Surface and the same analytic 92-degree bend.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def output_dir():
    argv = sys.argv
    if "--" not in argv or len(argv[argv.index("--") + 1 :]) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    path = Path(argv[argv.index("--") + 1]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def mat(name, color, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    node = material.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color, 1.0)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = 0.32
    return material


def make_tube(name, diagonal_ring, material):
    radial = 12
    axis_rows = [-3.0, -2.55, -2.1, -1.7, -1.35, -1.05, -0.78, -0.52, -0.28, 0.0, 0.28, 0.52, 0.78, 1.05, 1.35, 1.7, 2.1, 2.55, 3.0]
    verts = []
    # The longitudinal axis is Y while Simple Deform bends around Z. The
    # previous Z-long/Z-bend attempt left the centerline straight and was
    # rejected after visual inspection.
    for axis in axis_rows:
        for side in range(radial):
            angle = 2 * math.pi * side / radial
            radius = 0.66 + 0.04 * math.cos(axis * 1.3)
            verts.append((radius * math.cos(angle), axis, radius * math.sin(angle)))
    faces = []
    for ring in range(len(axis_rows) - 1):
        for side in range(radial):
            nxt = (side + 1) % radial
            a = ring * radial + side
            b = ring * radial + nxt
            c = (ring + 1) * radial + nxt
            d = (ring + 1) * radial + side
            if diagonal_ring is not None and ring == diagonal_ring and side == 6:
                # Same local density in both test variants. The added diagonal
                # raises the two endpoint valences from four to five.
                faces.extend([(a, b, c), (a, c, d)])
            else:
                faces.append((a, b, c, d))
    faces.append(tuple(reversed(range(radial))))
    top = (len(axis_rows) - 1) * radial
    faces.append(tuple(top + side for side in range(radial)))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    group = obj.vertex_groups.new(name="BendZone")
    indices = [ring * radial + side for ring, axis in enumerate(axis_rows) if abs(axis) <= 0.8 for side in range(radial)]
    group.add(indices, 1.0, "REPLACE")

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)

    subdiv = obj.modifiers.new("Deformation subdivision", "SUBSURF")
    subdiv.levels = 2
    subdiv.render_levels = 2
    obj.modifiers.new("Evaluated triangle contract", "TRIANGULATE")
    return obj, radial, axis_rows


def evaluated_mesh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    return evaluated, mesh


def bend_mesh(mesh, angle_degrees=92):
    """Map a Y-long tube into a circular arc while preserving cross-sections."""
    total_length = 6.0
    bend_angle = math.radians(angle_degrees)
    radius = total_length / bend_angle
    for vertex in mesh.vertices:
        x, axis, z = vertex.co
        theta = axis / radius
        center = Vector((radius * (1 - math.cos(theta)), radius * math.sin(theta), 0.0))
        in_plane_normal = Vector((math.cos(theta), -math.sin(theta), 0.0))
        vertex.co = center + x * in_plane_normal + Vector((0.0, 0.0, z))
    mesh.update()


def bent_evaluated_copy(obj, depsgraph):
    evaluated, temporary = evaluated_mesh(obj, depsgraph)
    mesh = temporary.copy()
    evaluated.to_mesh_clear()
    bend_mesh(mesh)
    return mesh


def bvh_from_mesh(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    return bm, BVHTree.FromBMesh(bm)


def distances_to_reference(mesh, group_index, reference_bvh):
    all_distances = []
    bend_distances = []
    bend_vertices_with_weights = 0
    for vertex in mesh.vertices:
        _, _, _, distance = reference_bvh.find_nearest(vertex.co)
        all_distances.append(float(distance))
        weight = next((item.weight for item in vertex.groups if item.group == group_index), 0.0)
        if weight > 0.5:
            bend_distances.append(float(distance))
            bend_vertices_with_weights += 1
    return {
        "all_mean": sum(all_distances) / len(all_distances),
        "all_max": max(all_distances),
        "bend_zone_mean": sum(bend_distances) / len(bend_distances),
        "bend_zone_max": max(bend_distances),
        "bend_zone_vertices": bend_vertices_with_weights,
    }


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_label(text, x):
    curve = bpy.data.curves.new("Label_" + text, "FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.size = 0.32
    curve.extrude = 0.006
    obj = bpy.data.objects.new("Label_" + text, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, -4.25, 0.0)
    return obj


def main():
    out = output_dir()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    gray = mat("All Quad Reference", (0.20, 0.25, 0.30), 0.35)
    green = mat("Pole Away", (0.05, 0.30, 0.12), 0.15)
    red = mat("Pole In Bend", (0.42, 0.045, 0.025), 0.12)
    reference, radial, axis_rows = make_tube("Reference_All_Quads", None, gray)
    away, _, _ = make_tube("Pole_Pair_Away", 2, green)
    bend, _, _ = make_tube("Pole_Pair_In_Bend", 9, red)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    ref_mesh = bent_evaluated_copy(reference, depsgraph)
    away_mesh = bent_evaluated_copy(away, depsgraph)
    bend_mesh_result = bent_evaluated_copy(bend, depsgraph)
    ref_bm, ref_bvh = bvh_from_mesh(ref_mesh)
    away_metrics = distances_to_reference(away_mesh, away.vertex_groups["BendZone"].index, ref_bvh)
    bend_metrics = distances_to_reference(bend_mesh_result, bend.vertex_groups["BendZone"].index, ref_bvh)
    ref_bm.free()

    for source in (reference, away, bend):
        source.hide_render = True
    for name, mesh, source, x_offset in [
        ("Bent_All_Quads", ref_mesh, reference, -5.0),
        ("Bent_Pole_Away", away_mesh, away, 0.0),
        ("Bent_Pole_In_Articulation", bend_mesh_result, bend, 5.0),
    ]:
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location.x = x_offset
        obj.data.materials.append(source.data.materials[0])

    # Distances compare identically bent local geometry; offsets are only for
    # presentation and are intentionally excluded from geometry metrics.
    ratio = bend_metrics["bend_zone_mean"] / max(away_metrics["bend_zone_mean"], 1e-12)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("Pole Review World")
    world.color = (0.012, 0.014, 0.018)
    scene.world = world
    target = Vector((0.0, 0.0, 0.0))
    for name, location, energy, size in [
        ("Key", (-5.0, -7.0, 6.0), 2600, 4.0),
        ("Fill", (6.0, -5.0, 1.0), 900, 5.0),
        ("Rim", (0.0, 4.0, 5.0), 3200, 3.0),
    ]:
        data = bpy.data.lights.new(name + "_Data", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = location
        point_at(light, target)
    camera_data = bpy.data.cameras.new("Camera_Data")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 8.0
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0.0, -13.0, 0.0)
    point_at(camera, target)
    scene.camera = camera
    add_label("ALL QUADS", -5.0)
    add_label("POLES AWAY", 0.0)
    add_label("POLES IN BEND", 5.0)
    # The first camera is intentionally edge-on to the bend direction. It
    # hides articulation and is retained as a review-camera failure.
    scene.render.filepath = str(out / "failed_edge_on_comparison.png")
    bpy.ops.render.render(write_still=True)
    camera.location = (0.0, 0.0, 14.0)
    camera.data.ortho_scale = 16.0
    point_at(camera, target)
    scene.render.filepath = str(out / "pole_placement_comparison.png")
    bpy.ops.render.render(write_still=True)
    blend_path = out / "pole_placement_deformation.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    report = {
        "source_principle": "Use poles/loop redirection to delimit patches and keep them away from important creases or deformation zones when possible.",
        "different_shape": "non-face articulated tapered hose",
        "controlled_variables": {
            "radial_segments": radial,
            "axial_rows": len(axis_rows),
            "subdivision_levels": 2,
            "bend_degrees": 92,
            "deformation": "identical analytic circular-arc mapping after evaluated Subdivision Surface",
            "test_topology_difference": "one identical diagonal producing two 5-valence endpoints, placed either at axial cell 2 or bend-center cell 9",
        },
        "pole_away": away_metrics,
        "pole_in_bend": bend_metrics,
        "bend_zone_mean_error_ratio_bad_over_good": ratio,
        "pass": ratio > 1.25 and bend_metrics["bend_zone_max"] > away_metrics["bend_zone_max"],
        "rejected_attempt": "The first experiment aligned the tube length and Bend modifier axis incorrectly, so the centerline stayed straight; its apparent ratio was invalid and was replaced by an explicit analytic bend.",
        "limitations": [
            "This is a controlled subdivided tube with an analytic bend, not a rigged face.",
            "A single diagonal creates a 5-pole pair through triangles; it does not cover every all-quad redirection pattern.",
            "Nearest-surface error measures geometric deviation from the all-quad control, not animation appeal.",
        ],
        "artifact": str(blend_path),
    }
    (out / "pole_placement_deformation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("POLE_PLACEMENT_RESULT:" + json.dumps(report))
    raise SystemExit(0 if report["pass"] else 1)


main()
