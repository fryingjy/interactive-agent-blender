"""Finish the typed Blender Guru lightbulb lesson as a source-like multi-bulb scene."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = REPO_ROOT / "runs" / "2026-08-22_tutorial-blenderguru-lightbulb"
SOURCE = RUN_DIR / "lightbulb_typed_model_v3.blend"


def material(name, color, roughness=0.35, metallic=0.0, transmission=0.0, emission=None, strength=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = color[3]
    if color[3] < 1.0:
        mat.surface_render_method = "BLENDED"
        mat.use_transparent_shadow = True
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission
    bsdf.inputs["IOR"].default_value = 1.45
    if emission:
        socket = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
        bsdf.inputs[socket].default_value = (*emission[:3], 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def smooth_mesh(obj):
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def link_to_collection(obj, collection):
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    for old in list(obj.users_collection):
        if old != collection:
            old.objects.unlink(obj)


def duplicate_assembly(source_objects, collection, name, location, rotation, scale=1.0, glowing=False):
    root = bpy.data.objects.new(name, None)
    collection.objects.link(root)
    root.location = location
    root.rotation_euler = rotation
    root.scale = (scale, scale, scale)
    copies = []
    for source in source_objects:
        copy = source.copy()
        copy.data = source.data.copy() if glowing and source.name in {"Bulb_Glass_Envelope", "Bulb_Tungsten_Coil"} else source.data
        copy.name = f"{name}_{source.name}"
        collection.objects.link(copy)
        copy.parent = root
        copy.matrix_parent_inverse.identity()
        copy.location = source.location
        copy.rotation_euler = source.rotation_euler
        copies.append(copy)
    return root, copies


def add_camera(scene):
    data = bpy.data.cameras.new("Lightbulb_Final_Camera")
    camera = bpy.data.objects.new("Lightbulb_Final_Camera", data)
    bpy.data.collections["LIGHTING"].objects.link(camera)
    camera.location = (0.2, -17.5, 7.2)
    target = Vector((0.0, 0.7, 1.25))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    data.lens = 47
    data.dof.use_dof = True
    data.dof.focus_object = bpy.data.objects["Hero_Glowing_Bulb"]
    data.dof.aperture_fstop = 2.6
    scene.camera = camera


def add_area(name, location, energy, color, size, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.data.collections["LIGHTING"].objects.link(obj)
    obj.location = location
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def main():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene

    for name in ("BULB_MASTER", "BULB_INSTANCES", "ENVIRONMENT", "LIGHTING"):
        collection = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        if collection.name not in scene.collection.children:
            scene.collection.children.link(collection)

    master_names = (
        "Bulb_Glass_Envelope", "Bulb_Metal_Shell", "Bulb_Contact_Tip", "Bulb_Internal_Stem",
        "Bulb_Lead_Left", "Bulb_Lead_Right", "Bulb_Tungsten_Coil", "Bulb_Screw_Thread",
    )
    master = [bpy.data.objects[name] for name in master_names]
    for obj in master:
        link_to_collection(obj, bpy.data.collections["BULB_MASTER"])

    glass = material("Clear_Bulb_Glass", (0.16, 0.20, 0.27, 0.14), 0.08, transmission=0.28, emission=(0.02, 0.03, 0.05), strength=0.08)
    steel = material("Bulb_Shell_Steel", (0.23, 0.25, 0.28, 1), 0.22, metallic=0.92)
    dark = material("Contact_Dark", (0.025, 0.018, 0.015, 1), 0.42)
    internal = material("Internal_Wire", (0.22, 0.16, 0.10, 1), 0.26, metallic=0.75)
    tungsten = material("Tungsten_Dark", (0.08, 0.035, 0.012, 1), 0.30, metallic=0.45)
    glow_glass = material("Hero_Glow_Glass", (1.0, 0.38, 0.07, 0.42), 0.12, transmission=0.25, emission=(1.0, 0.20, 0.025), strength=2.3)
    glow_wire = material("Hero_Glow_Filament", (1.0, 0.32, 0.05, 1), 0.2, emission=(1.0, 0.12, 0.01), strength=13.0)

    for name in ("Bulb_Glass_Envelope", "Bulb_Internal_Stem"):
        assign(bpy.data.objects[name], glass)
    for name in ("Bulb_Metal_Shell", "Bulb_Screw_Thread"):
        assign(bpy.data.objects[name], steel)
    assign(bpy.data.objects["Bulb_Contact_Tip"], dark)
    for name in ("Bulb_Lead_Left", "Bulb_Lead_Right"):
        assign(bpy.data.objects[name], internal)
    assign(bpy.data.objects["Bulb_Tungsten_Coil"], tungsten)

    for obj in master:
        smooth_mesh(obj)
    glass_obj = bpy.data.objects["Bulb_Glass_Envelope"]
    subdiv = glass_obj.modifiers.new("Live_Glass_Subdivision", "SUBSURF")
    subdiv.levels = 1
    subdiv.render_levels = 1

    master_root = bpy.data.objects.new("Master_Bulb_Root", None)
    bpy.data.collections["BULB_MASTER"].objects.link(master_root)
    master_root.location = (-7.0, 2.8, 1.35)
    master_root.rotation_euler = (math.radians(86), math.radians(-18), math.radians(12))
    for obj in master:
        obj.parent = master_root
        obj.matrix_parent_inverse.identity()

    layouts = [
        (-5.2, 1.7, 1.35, 78, 18, -22, 0.92), (-3.2, 2.5, 1.35, 95, -12, 32, 1.00),
        (-1.0, 2.8, 1.35, 84, 24, -15, 0.90), (1.5, 2.4, 1.35, 92, -20, 18, 0.96),
        (4.0, 2.6, 1.35, 75, 28, 38, 0.88), (6.2, 1.9, 1.35, 100, -16, -28, 1.00),
        (-6.3, -0.8, 1.35, 88, -24, 20, 1.05), (-3.8, -0.4, 1.35, 70, 30, -40, 0.90),
        (-1.4, -0.8, 1.35, 98, 14, 12, 1.08), (1.2, -0.7, 1.35, 82, -32, -16, 0.94),
        (3.8, -0.5, 1.35, 105, 12, 24, 1.02), (6.2, -0.8, 1.35, 74, -22, -12, 0.90),
        (-5.0, -3.2, 1.35, 96, 20, 30, 1.03), (-2.2, -3.0, 1.35, 76, -20, -35, 0.92),
        (2.6, -3.0, 1.35, 88, 28, 22, 1.08), (5.3, -3.1, 1.35, 102, -18, -18, 0.95),
    ]
    for index, (x, y, z, rx, ry, rz, scale) in enumerate(layouts):
        duplicate_assembly(
            master,
            bpy.data.collections["BULB_INSTANCES"],
            f"Bulb_Copy_{index:02d}",
            (x, y, z),
            tuple(math.radians(angle) for angle in (rx, ry, rz)),
            scale,
        )

    hero_root, hero_parts = duplicate_assembly(
        master,
        bpy.data.collections["BULB_INSTANCES"],
        "Hero_Glowing_Bulb",
        (0.8, 1.9, 1.38),
        (math.radians(84), math.radians(-12), math.radians(-18)),
        0.90,
        glowing=True,
    )
    for obj in hero_parts:
        if obj.name.endswith("Bulb_Glass_Envelope"):
            assign(obj, glow_glass)
        elif obj.name.endswith("Bulb_Tungsten_Coil"):
            assign(obj, glow_wire)

    floor_mat = material("Reflective_Floor", (0.23, 0.21, 0.20, 1), 0.17, metallic=0.12)
    stripe_mat = material("Floor_Stripe_Black", (0.005, 0.004, 0.005, 1), 0.20)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.02))
    floor = bpy.context.object
    floor.name = "Reflective_Floor"
    assign(floor, floor_mat)
    link_to_collection(floor, bpy.data.collections["ENVIRONMENT"])
    for x in (-6.0, -2.0, 2.0, 6.0):
        bpy.ops.mesh.primitive_cube_add(location=(x, 0.0, 0.0), scale=(0.55, 10.0, 0.018))
        stripe = bpy.context.object
        stripe.name = f"Floor_Stripe_{x:+.0f}"
        assign(stripe, stripe_mat)
        link_to_collection(stripe, bpy.data.collections["ENVIRONMENT"])

    target = Vector((0.0, 0.7, 1.2))
    add_area("Warm_Hero_Key", (1.0, -1.0, 6.5), 1300, (1.0, 0.34, 0.12), 5.0, target)
    add_area("Cool_Side_Fill", (-7.0, -2.0, 4.5), 520, (0.18, 0.32, 0.70), 5.5, target)
    add_area("Soft_Back_Rim", (6.0, 5.0, 5.0), 420, (0.55, 0.23, 0.12), 4.0, target)
    add_area("Large_Front_Fill", (0.0, -9.0, 8.0), 980, (0.40, 0.52, 0.78), 8.0, target)
    add_camera(scene)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 650
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.20
    world = scene.world or bpy.data.worlds.new("Lightbulb_World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.0015, 0.003, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.10

    compositor = bpy.data.node_groups.new("Lightbulb_Compositor", "CompositorNodeTree")
    scene.compositing_node_group = compositor
    nodes = compositor.nodes
    links = compositor.links
    layers = nodes.new("CompositorNodeRLayers")
    glare = nodes.new("CompositorNodeGlare")
    glare.inputs["Type"].default_value = "Fog Glow"
    glare.inputs["Quality"].default_value = "High"
    glare.inputs["Threshold"].default_value = 0.65
    glare.inputs["Size"].default_value = 0.72
    compositor.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    composite = nodes.new("NodeGroupOutput")
    links.new(layers.outputs["Image"], glare.inputs["Image"])
    links.new(glare.outputs["Image"], composite.inputs["Image"])

    scene.render.filepath = str(RUN_DIR / "lightbulb_scene_v4.png")
    bpy.ops.render.render(write_still=True)
    report = {
        "schema_version": 1,
        "record_type": "TUTORIAL_PRODUCTION_PASS",
        "source_page": "https://www.blenderguru.com/posts/lightbulb-tutorial",
        "source_blend": str(SOURCE.relative_to(REPO_ROOT)),
        "blender_version": bpy.app.version_string,
        "bulb_assembly_count": 18,
        "master_components": list(master_names),
        "glass_subdivision_live": True,
        "modifiers_applied": False,
        "creator_finished_result_review": "PENDING_RENDER_COMPARISON",
    }
    report["rejected_predecessors"] = [
        "lightbulb_scene_v1.png: non-emissive glass collapsed into black silhouettes and hero glow dominated",
        "lightbulb_scene_v2.png: added fill exposed that Eevee transmission remained visually opaque",
    ]
    report["thread_correction"] = "v4 uses a finer 4.5-turn live Bezier helix instead of the coarse three-turn ridge"
    (RUN_DIR / "production_report_v4.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN_DIR / "lightbulb_tutorial_scene_v4.blend"))


if __name__ == "__main__":
    main()
