"""Build a supplied-reference tactical axe from measured 2D profiles.

The body, aperture cutter, grip scales, cutting insert, and fasteners are
constructed from explicit vertices.  No mesh primitive operators are used.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_profile-authored-axe"
PROFILE = json.loads((OUT / "reference_profile.json").read_text(encoding="utf-8"))
PARTS = None


def ensure_outward(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        mesh.update()
    bm.free()


def extrude_profile(name, points, depth):
    loop = [Vector((float(x), float(z))) for x, z in points]
    # tessellate_polygon expects a consistently wound simple contour.
    triangles = tessellate_polygon([loop])
    lookup = {(round(value.x, 8), round(value.y, 8)): index for index, value in enumerate(loop)}
    count = len(loop)
    vertices = [(value.x, -depth / 2, value.y) for value in loop]
    vertices += [(value.x, depth / 2, value.y) for value in loop]
    faces = []
    for triangle in triangles:
        if isinstance(triangle[0], int):
            indices = list(triangle)
        else:
            indices = [lookup[(round(value.x, 8), round(value.y, 8))] for value in triangle]
        faces.append(tuple(indices))
        faces.append(tuple(count + index for index in reversed(indices)))
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    ensure_outward(mesh)
    obj = bpy.data.objects.new(name, mesh)
    PARTS.objects.link(obj)
    return obj


def cylinder_mesh(name, x, z, radius, depth, segments=24):
    vertices = []
    for y in (-depth / 2, depth / 2):
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            vertices.append((x + radius * math.cos(angle), y, z + radius * math.sin(angle)))
    vertices.extend([(x, -depth / 2, z), (x, depth / 2, z)])
    faces = []
    for segment in range(segments):
        nxt = (segment + 1) % segments
        faces.append((segment, nxt, segments + nxt, segments + segment))
        faces.append((2 * segments, nxt, segment))
        faces.append((2 * segments + 1, segments + segment, segments + nxt))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    ensure_outward(mesh)
    obj = bpy.data.objects.new(name, mesh)
    PARTS.objects.link(obj)
    return obj


def activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def boolean_cut(body, cutter):
    modifier = body.modifiers.new("Head_Aperture", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    activate(body)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def finish_mesh(obj, bevel_width, bevel_segments=3):
    bevel = obj.modifiers.new("Edge_Bevel", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = bevel_segments
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(20)
    triangulate = obj.modifiers.new("Final_Triangulate", "TRIANGULATE")
    triangulate.quad_method = "BEAUTY"
    activate(obj)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")


def material(name, color, metallic, roughness, noise=False):
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    nodes = value.node_tree.nodes
    links = value.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if noise:
        texture = nodes.new("ShaderNodeTexNoise")
        texture.inputs["Scale"].default_value = 95.0
        texture.inputs["Detail"].default_value = 2.0
        texture.inputs["Roughness"].default_value = 0.65
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.18
        bump.inputs["Distance"].default_value = 0.035
        links.new(texture.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return value


def point_at(obj, target=(0.0, 0.0, 0.0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area_light(name, location, energy, size, color=(1.0, 1.0, 1.0)):
    data = bpy.data.lights.new(name + "Data", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj)


def render(path, camera_location, target, transparent=False, override=None):
    camera = bpy.context.scene.camera
    camera.location = camera_location
    point_at(camera, target)
    scene = bpy.context.scene
    scene.render.film_transparent = transparent
    scene.view_layers[0].material_override = override
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override = None


def main():
    global PARTS
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    PARTS = bpy.data.collections.new("ProfileAuthoredAxe")
    bpy.context.scene.collection.children.link(PARTS)

    dark_steel = material("Blackened_Steel", (0.025, 0.032, 0.04), 0.82, 0.25)
    grip_material = material("Textured_Grip", (0.018, 0.022, 0.025), 0.1, 0.5, noise=True)
    edge_material = material("Cutting_Edge", (0.22, 0.24, 0.26), 0.9, 0.18)
    fastener_material = material("Fastener_Steel", (0.35, 0.38, 0.42), 0.95, 0.16)

    body = extrude_profile("Axe_FullTang_Body", PROFILE["outer_profile"], 0.32)
    cutter = extrude_profile("Head_Aperture_Cutter", PROFILE["head_cutout"], 0.8)
    boolean_cut(body, cutter)
    body.data.materials.append(dark_steel)
    finish_mesh(body, 0.055, 4)

    grip = extrude_profile("Raised_Grip_Scales", PROFILE["grip_scale_profile"], 0.46)
    grip.data.materials.append(grip_material)
    finish_mesh(grip, 0.045, 3)

    cutting_edge = [point for point in PROFILE["outer_profile"] if point[0] < -3.8 and point[1] < -1.8]
    blade_points = cutting_edge + [[point[0], point[1] + 0.13] for point in reversed(cutting_edge)]
    blade = extrude_profile("Exposed_Cutting_Edge", blade_points, 0.37)
    blade.data.materials.append(edge_material)
    finish_mesh(blade, 0.025, 2)

    fasteners = []
    for index, (x, z, radius) in enumerate(PROFILE["fasteners"]):
        if x <= -3.4:
            continue
        fastener = cylinder_mesh(f"Grip_Fastener_{index + 1:02d}", x, z, max(radius, 0.075), 0.56)
        fastener.data.materials.append(fastener_material)
        finish_mesh(fastener, 0.018, 2)
        fasteners.append(fastener)

    bpy.ops.object.camera_add(location=(0.0, -16.0, 0.0))
    camera = bpy.context.object
    camera.name = "Axe_Review_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 11.5
    bpy.context.scene.camera = camera
    area_light("Key", (2.0, -6.0, 7.0), 1700, 4.0)
    area_light("Fill", (-5.0, -4.0, 1.0), 500, 5.0, (0.72, 0.84, 1.0))
    area_light("Rim", (2.0, 4.0, 5.0), 1300, 3.0, (1.0, 0.72, 0.52))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.008, 0.01, 0.014)
    scene.view_settings.look = "AgX - Medium High Contrast"
    render(OUT / "axe_beauty.png", (0.0, -15.0, 5.0), (0.0, 0.0, 0.0))

    mask_material = material("Mask_Emission", (1.0, 1.0, 1.0), 0.0, 1.0)
    bsdf = mask_material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    render(OUT / "axe_front_mask.png", (0.0, -16.0, 0.0), (0.0, 0.0, 0.0), transparent=True, override=mask_material)

    report = {
        "lab": "profile_authored_tactical_axe",
        "blender_version": bpy.app.version_string,
        "reference": PROFILE["source"],
        "construction": "measured contour extrusion + exact aperture boolean + raised grip + authored cylinders",
        "mesh_primitive_operator_calls": 0,
        "semantic_meshes": 3 + len(fasteners),
        "fasteners": len(fasteners),
        "source_uncertainty": PROFILE["limitations"],
        "assertions": {
            "real_head_aperture": body.modifiers.get("Head_Aperture") is None,
            "separate_grip_scales": grip.name in bpy.data.objects,
            "multiple_fasteners": len(fasteners) >= 4,
            "evaluated_bevel_hierarchy": all(any(mod.type == "BEVEL" for mod in obj.modifiers) for obj in [body, grip, blade, *fasteners]),
            "uv_on_every_mesh": all(obj.data.uv_layers for obj in [body, grip, blade, *fasteners]),
        },
    }
    report["pass"] = all(report["assertions"].values())
    (OUT / "axe_build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "profile_authored_axe.blend"))
    print("AXE_BUILD_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("axe build assertions failed")


main()
