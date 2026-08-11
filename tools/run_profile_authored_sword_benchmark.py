"""Build and render a profile-authored fantasy sword benchmark in Blender.

This deliberately avoids ``bpy.ops.mesh.primitive_*``. Primary and secondary
forms come from explicit profiles, cross-sections, lathed rings, and a helical
wrap so the result exercises modeling decisions instead of primitive assembly.

Run:
    blender --background --factory-startup --python-exit-code 1 \
      --python tools/run_profile_authored_sword_benchmark.py -- OUTPUT_DIR
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def output_dir() -> Path:
    argv = sys.argv
    if "--" not in argv or len(argv[argv.index("--") + 1 :]) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    path = Path(argv[argv.index("--") + 1]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def material(name, color, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1.0)
    mat.metallic = metallic
    mat.roughness = roughness
    node = mat.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color, 1.0)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    return mat


def finish_mesh(obj, mat, bevel=0.0, bevel_segments=3):
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if bevel:
        modifier = obj.modifiers.new("Edge hierarchy", "BEVEL")
        modifier.width = bevel
        modifier.segments = bevel_segments
        modifier.limit_method = "ANGLE"
    triangulate = obj.modifiers.new("Evaluated triangle contract", "TRIANGULATE")
    triangulate.keep_custom_normals = True
    # Generate a real UV layer on the editable mesh. Smart projection is used
    # only after authored geometry exists; it is not a substitute for form.
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for other in bpy.context.selected_objects:
        if other != obj:
            other.select_set(False)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    return obj


def recalc(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def extruded_profile(name, points, depth, mat, bevel=0.035):
    """Create a closed solid from an authored x/z outline."""
    count = len(points)
    verts = [(x, -depth / 2, z) for x, z in points] + [(x, depth / 2, z) for x, z in points]
    faces = []
    # Opposite cap winding plus perimeter quads.
    faces.append(tuple(reversed(range(count))))
    faces.append(tuple(range(count, count * 2)))
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    recalc(mesh)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish_mesh(obj, mat, bevel)


def diamond_blade(name, rows, mat):
    """Create a blade from authored width/depth sections with a center ridge."""
    verts = []
    for z, half_width, half_depth in rows:
        verts.extend(
            [
                (-half_width, 0.0, z),
                (0.0, -half_depth, z),
                (half_width, 0.0, z),
                (0.0, half_depth, z),
            ]
        )
    faces = []
    for row in range(len(rows) - 1):
        a = row * 4
        b = (row + 1) * 4
        for side in range(4):
            nxt = (side + 1) % 4
            faces.append((a + side, a + nxt, b + nxt, b + side))
    faces.extend([(3, 2, 1, 0), tuple(range((len(rows) - 1) * 4, len(rows) * 4))])
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    recalc(mesh)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish_mesh(obj, mat, 0.018, 2)


def lathe(name, profile, segments, mat, bevel=0.015):
    """Create a closed rotational solid around Z from explicit radius/Z rows."""
    verts = []
    for radius, z in profile:
        for step in range(segments):
            angle = 2 * math.pi * step / segments
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    faces = []
    rows = len(profile)
    for row in range(rows - 1):
        for step in range(segments):
            nxt = (step + 1) % segments
            faces.append((row * segments + step, row * segments + nxt, (row + 1) * segments + nxt, (row + 1) * segments + step))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple((rows - 1) * segments + step for step in range(segments)))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    recalc(mesh)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish_mesh(obj, mat, bevel, 2)


def tube_from_polyline(name, points, radius, mat, resolution=2):
    """Create a closed tube using explicit transported cross-section rings.

    Blender's converted curve caps left non-manifold seam edges in the first
    benchmark attempt. Explicit ring connectivity makes closure independently
    verifiable and keeps the failed approach from becoming hidden debt.
    """
    points = [Vector(point) for point in points]
    sides = 6 + resolution * 2
    verts = []
    for index, point in enumerate(points):
        if index == 0:
            tangent = (points[1] - point).normalized()
        elif index == len(points) - 1:
            tangent = (point - points[index - 1]).normalized()
        else:
            tangent = (points[index + 1] - points[index - 1]).normalized()
        reference = Vector((0.0, 0.0, 1.0))
        if abs(tangent.dot(reference)) > 0.92:
            reference = Vector((0.0, 1.0, 0.0))
        normal_a = tangent.cross(reference).normalized()
        normal_b = tangent.cross(normal_a).normalized()
        for side in range(sides):
            angle = 2 * math.pi * side / sides
            vertex = point + radius * (math.cos(angle) * normal_a + math.sin(angle) * normal_b)
            verts.append(tuple(vertex))
    faces = []
    for ring in range(len(points) - 1):
        for side in range(sides):
            nxt = (side + 1) % sides
            faces.append((ring * sides + side, ring * sides + nxt, (ring + 1) * sides + nxt, (ring + 1) * sides + side))
    start_center = len(verts)
    verts.append(tuple(points[0]))
    end_center = len(verts)
    verts.append(tuple(points[-1]))
    for side in range(sides):
        nxt = (side + 1) % sides
        faces.append((start_center, nxt, side))
        base = (len(points) - 1) * sides
        faces.append((end_center, base + side, base + nxt))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    recalc(mesh)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish_mesh(obj, mat, 0.0)


def mirror_points(points):
    return [(-x, z) for x, z in reversed(points)]


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area(name, location, energy, size, color, target):
    data = bpy.data.lights.new(name + "_Data", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    return obj


def create_camera(name, location, ortho_scale, target):
    data = bpy.data.cameras.new(name + "_Data")
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    return obj


def render(scene, camera, path, transparent=False):
    scene.camera = camera
    scene.render.film_transparent = transparent
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    out = output_dir()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass

    steel = material("Tempered Steel", (0.22, 0.28, 0.34), 0.88, 0.22)
    steel_dark = material("Recessed Steel", (0.025, 0.045, 0.065), 0.75, 0.3)
    gold = material("Aged Brass", (0.38, 0.19, 0.045), 0.82, 0.25)
    gold_dark = material("Guard Recess", (0.085, 0.035, 0.012), 0.68, 0.34)
    leather = material("Blue Leather", (0.025, 0.075, 0.16), 0.05, 0.62)
    leather_edge = material("Wrap Edge", (0.07, 0.16, 0.3), 0.12, 0.5)
    gem = material("Pommel Ruby", (0.42, 0.005, 0.012), 0.3, 0.14)

    blade = diamond_blade(
        "Blade_Profiled",
        [
            (1.72, 0.72, 0.105),
            (2.10, 0.98, 0.13),
            (3.35, 0.72, 0.16),
            (4.65, 0.64, 0.17),
            (5.80, 0.84, 0.15),
            (6.35, 1.08, 0.14),
            (6.75, 1.05, 0.13),
            (7.10, 0.76, 0.10),
            (7.72, 0.06, 0.035),
        ],
        steel,
    )
    # A narrow raised central feature gives the broad blade a second plane
    # family without replacing its diamond cross-section.
    ridge = extruded_profile(
        "Blade_Central_Inlay",
        [(-0.055, 2.0), (-0.075, 5.95), (0.0, 6.72), (0.075, 5.95), (0.055, 2.0)],
        0.355,
        steel_dark,
        0.012,
    )
    ridge.location.y = -0.004

    left_upper = [(0.27, 1.76), (0.68, 1.90), (1.68, 1.37), (1.50, 1.24), (0.90, 1.44), (0.37, 1.54)]
    left_lower = [(0.30, 1.40), (0.80, 1.32), (1.90, 0.85), (1.55, 0.67), (0.75, 0.99), (0.34, 1.15)]
    guard_parts = [
        extruded_profile("Guard_Upper_Left", left_upper, 0.30, gold, 0.045),
        extruded_profile("Guard_Upper_Right", mirror_points(left_upper), 0.30, gold, 0.045),
        extruded_profile("Guard_Lower_Left", left_lower, 0.27, gold, 0.04),
        extruded_profile("Guard_Lower_Right", mirror_points(left_lower), 0.27, gold, 0.04),
        extruded_profile(
            "Guard_Central_Shield",
            [(-0.49, 2.08), (0.0, 2.48), (0.49, 2.08), (0.46, 1.08), (0.0, 0.70), (-0.46, 1.08)],
            0.36,
            gold,
            0.055,
        ),
        extruded_profile(
            "Guard_Shield_Recess",
            [(-0.25, 1.95), (0.0, 2.19), (0.25, 1.95), (0.17, 1.32), (0.0, 1.14), (-0.17, 1.32)],
            0.375,
            gold_dark,
            0.018,
        ),
    ]

    # Raised grooves follow the wing gesture and make the layered guard read
    # under grazing light. Curves are converted to closed mesh tubes.
    groove_paths = [
        [(0.43, -0.175, 1.68), (0.76, -0.175, 1.76), (1.38, -0.175, 1.42)],
        [(-0.43, -0.175, 1.68), (-0.76, -0.175, 1.76), (-1.38, -0.175, 1.42)],
        [(0.44, -0.16, 1.26), (0.84, -0.16, 1.19), (1.52, -0.16, 0.90)],
        [(-0.44, -0.16, 1.26), (-0.84, -0.16, 1.19), (-1.52, -0.16, 0.90)],
    ]
    grooves = [tube_from_polyline(f"Guard_Groove_{index:02d}", path, 0.026, gold_dark, 1) for index, path in enumerate(groove_paths, 1)]

    grip = lathe(
        "Grip_Core",
        [(0.22, -1.22), (0.24, -1.12), (0.24, 0.58), (0.275, 0.73)],
        16,
        leather,
        0.018,
    )
    collar_top = lathe("Grip_Upper_Collar", [(0.30, 0.61), (0.34, 0.72), (0.29, 0.84)], 16, gold, 0.018)
    collar_bottom = lathe("Grip_Lower_Collar", [(0.27, -1.27), (0.35, -1.17), (0.30, -1.04)], 16, gold, 0.018)

    helix = []
    turns = 6.25
    samples = 150
    for index in range(samples):
        t = index / (samples - 1)
        angle = 2 * math.pi * turns * t + math.pi * 0.1
        radius = 0.255
        z = -1.10 + 1.74 * t
        helix.append((radius * math.cos(angle), radius * math.sin(angle), z))
    wrap = tube_from_polyline("Grip_Helical_Wrap", helix, 0.032, leather_edge, 2)

    pommel = lathe(
        "Pommel_Faceted",
        [(0.25, -1.74), (0.42, -1.59), (0.44, -1.38), (0.33, -1.23)],
        12,
        gold,
        0.025,
    )
    pommel_recess = lathe("Pommel_Recess", [(0.17, -1.79), (0.29, -1.70), (0.30, -1.58)], 16, gold_dark, 0.012)
    ruby = lathe(
        "Pommel_Ruby",
        [(0.02, -1.95), (0.22, -1.89), (0.29, -1.80), (0.22, -1.70), (0.02, -1.66)],
        20,
        gem,
        0.01,
    )

    production_meshes = [blade, ridge, *guard_parts, *grooves, grip, collar_top, collar_bottom, wrap, pommel, pommel_recess, ruby]
    collection = bpy.data.collections.new("PROFILE_AUTHORED_SWORD")
    bpy.context.scene.collection.children.link(collection)
    for obj in production_meshes:
        for source_collection in list(obj.users_collection):
            source_collection.objects.unlink(obj)
        collection.objects.link(obj)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("Sword Review World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.009, 0.014, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.16
    scene.world = world

    target = Vector((0.0, 0.0, 2.9))
    add_area("Key", Vector((-5.0, -6.0, 8.5)), 3400, 4.0, (0.73, 0.86, 1.0), target)
    add_area("Fill", Vector((4.5, -4.0, 3.0)), 1150, 5.0, (1.0, 0.60, 0.34), target)
    add_area("Rim", Vector((3.0, 4.0, 7.0)), 4300, 3.0, (0.45, 0.65, 1.0), target)
    add_area("Isometric Softbox", Vector((7.0, -8.0, 8.0)), 2600, 5.5, (0.82, 0.90, 1.0), target)

    front = create_camera("Camera_Front", Vector((0.0, -14.0, 2.9)), 10.8, target)
    side = create_camera("Camera_Side", Vector((11.0, 0.0, 2.9)), 10.8, target)
    iso = create_camera("Camera_Isometric", Vector((5.0, -14.0, 5.0)), 11.1, target)
    render(scene, front, out / "front_beauty.png")
    render(scene, side, out / "side_beauty.png")
    render(scene, iso, out / "isometric_beauty.png")
    render(scene, front, out / "front_alpha.png", transparent=True)

    scene.render.film_transparent = False
    blend_path = out / "profile_authored_sword.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    report = {
        "benchmark": "profile_authored_fantasy_sword_001",
        "construction_contract": {
            "primitive_mesh_operators_used": 0,
            "primary_methods": ["authored x/z profile extrusion", "sectioned diamond blade", "lathed profile rings", "explicit closed helical tube"],
            "semantic_mesh_components": len(production_meshes),
            "required_components": ["blade", "central blade feature", "layered guard", "guard grooves", "grip core", "helical wrap", "collars", "pommel", "gem"],
        },
        "objects": [
            {
                "name": obj.name,
                "vertices": len(obj.data.vertices),
                "faces": len(obj.data.polygons),
                "uv_layers": len(obj.data.uv_layers),
                "modifiers": [modifier.type for modifier in obj.modifiers],
            }
            for obj in production_meshes
        ],
        "renders": ["front_beauty.png", "side_beauty.png", "isometric_beauty.png", "front_alpha.png"],
        "blend": str(blend_path),
    }
    (out / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PROFILE_SWORD_RESULT:" + json.dumps(report))


main()
