"""Finish materials, typography, organization, and presentation for the tutorial model."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = REPO_ROOT / "runs" / "2026-08-22_tutorial-polygon-runway-ramen-machine"
SOURCE = RUN_DIR / "ramen_machine_components_v2.blend"


def make_material(name, color, roughness=0.4, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color[:3], color[3] if len(color) > 3 else 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = mat.diffuse_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission[:3], 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        else:
            bsdf.inputs["Emission"].default_value = (*emission[:3], 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def assign(name, mat):
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def live_bevel(name, width, segments=2):
    obj = bpy.data.objects[name]
    existing = obj.modifiers.get("Live_Manufactured_Bevel")
    if existing:
        obj.modifiers.remove(existing)
    modifier = obj.modifiers.new("Live_Manufactured_Bevel", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    modifier.harden_normals = True
    modifier.show_viewport = True
    modifier.show_render = True


def smooth_radial(name):
    obj = bpy.data.objects[name]
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def add_text(name, body, location, rotation, size, material, font):
    curve = bpy.data.curves.new(name + "_Curve", "FONT")
    curve.body = body
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.025
    curve.bevel_depth = 0.010
    curve.bevel_resolution = 2
    curve.resolution_u = 8
    curve.font = font
    curve.materials.append(material)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    return obj


def organize_collections():
    scene = bpy.context.scene
    for collection_name in ("MODEL_PRIMARY", "MODEL_ASSEMBLIES", "MODEL_DETAILS", "SIGNAGE", "LIGHTING"):
        if collection_name not in bpy.data.collections:
            collection = bpy.data.collections.new(collection_name)
            scene.collection.children.link(collection)
    primary = {"ramen_machine_housing"}
    details = {
        "right_side_cable", "right_side_cable_secondary", "noodle_strand_01", "noodle_strand_02",
        "chopstick_left", "chopstick_right", "egg_white", "egg_yolk", "control_button_red",
        "control_button_yellow", "control_button_green", "stool_base_left", "stool_base_right",
    }
    signage = {"front_ramen_text", "side_number_26"}
    for obj in list(scene.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            target = bpy.data.collections["LIGHTING"]
        elif obj.name in signage:
            target = bpy.data.collections["SIGNAGE"]
        elif obj.name in primary:
            target = bpy.data.collections["MODEL_PRIMARY"]
        elif obj.name in details:
            target = bpy.data.collections["MODEL_DETAILS"]
        else:
            target = bpy.data.collections["MODEL_ASSEMBLIES"]
        if obj.name not in target.objects:
            target.objects.link(obj)
        for collection in list(obj.users_collection):
            if collection != target:
                collection.objects.unlink(obj)


def add_camera_and_lights():
    scene = bpy.context.scene
    camera_data = bpy.data.cameras.new("Tutorial_Final_Camera")
    camera = bpy.data.objects.new("Tutorial_Final_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (10.0, -12.5, 9.2)
    target = Vector((0.0, -0.15, 2.45))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.lens = 58
    scene.camera = camera

    def area(name, location, energy, color, size):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = color
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
        return obj

    area("Key_Warm", (-4.8, -5.5, 10.0), 950, (1.0, 0.48, 0.32), 5.0)
    area("Fill_Cool", (6.5, -1.0, 6.5), 700, (0.28, 0.50, 1.0), 4.0)
    area("Rim_Magenta", (0.0, 5.0, 7.5), 820, (1.0, 0.16, 0.48), 3.5)
    area("Front_Soft", (0.0, -7.0, 4.5), 720, (0.58, 0.72, 1.0), 4.5)


def main():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

    navy = make_material("Housing_Navy_Metal", (0.035, 0.075, 0.14, 1), 0.24, 0.62)
    dark = make_material("Platform_Dark", (0.018, 0.028, 0.055, 1), 0.35, 0.32)
    red = make_material("Trim_Red", (0.55, 0.025, 0.055, 1), 0.23, 0.42)
    pink = make_material("Seat_Pink", (0.86, 0.055, 0.19, 1), 0.28, 0.20)
    steel = make_material("Brushed_Steel", (0.22, 0.29, 0.37, 1), 0.22, 0.88)
    warm = make_material("Counter_Warm", (0.70, 0.26, 0.055, 1), 0.37, 0.12)
    noodle = make_material("Noodle_Cream", (0.92, 0.58, 0.20, 1), 0.48, 0.0)
    egg_white = make_material("Egg_White", (0.95, 0.89, 0.70, 1), 0.42, 0.0)
    yolk = make_material("Egg_Yolk", (1.0, 0.30, 0.035, 1), 0.31, 0.0)
    green = make_material("Button_Green", (0.03, 0.72, 0.32, 1), 0.24, 0.12)
    yellow = make_material("Button_Yellow", (1.0, 0.64, 0.03, 1), 0.24, 0.12)
    neon = make_material("Sign_Neon", (0.95, 0.65, 0.28, 1), 0.25, 0.0, (1.0, 0.18, 0.04), 7.0)

    for name in ("ramen_machine_housing", "side_armor_plate"):
        assign(name, navy)
    for name in ("floor_platform", "side_electrical_box"):
        assign(name, dark)
    for name in ("lower_housing_trim", "front_sign_frame", "roof_ramen_bowl"):
        assign(name, red)
    assign("service_counter", warm)
    for name in ("right_side_cable", "right_side_cable_secondary", "stool_base_left", "stool_base_right"):
        assign(name, steel)
    for name in ("stool_seat_left", "stool_seat_right", "control_button_red"):
        assign(name, pink)
    for name in ("noodle_strand_01", "noodle_strand_02"):
        assign(name, noodle)
    for name in ("chopstick_left", "chopstick_right"):
        assign(name, warm)
    assign("egg_white", egg_white)
    assign("egg_yolk", yolk)
    assign("control_button_yellow", yellow)
    assign("control_button_green", green)

    housing = bpy.data.objects["ramen_machine_housing"]
    housing.data.materials.append(steel)
    housing.data.materials.append(dark)
    for polygon in housing.data.polygons:
        if polygon.center.z > 2.05:
            polygon.material_index = 1
        elif polygon.normal.y < -0.9 and abs(polygon.center.z) < 0.72 and polygon.center.y > -1.15:
            polygon.material_index = 2

    for name, width in {
        "floor_platform": 0.10,
        "lower_housing_trim": 0.055,
        "service_counter": 0.055,
        "side_electrical_box": 0.060,
        "side_armor_plate": 0.045,
        "egg_white": 0.035,
    }.items():
        live_bevel(name, width, 3 if name == "floor_platform" else 2)

    for name in (
        "roof_ramen_bowl", "stool_seat_left", "stool_seat_right", "egg_yolk",
        "control_button_red", "control_button_yellow", "control_button_green",
    ):
        smooth_radial(name)

    for name in ("roof_ramen_bowl", "noodle_strand_01", "noodle_strand_02", "chopstick_left", "chopstick_right"):
        obj = bpy.data.objects[name]
        obj.scale.x = 1.18
        obj.scale.y = 1.18
    bpy.data.objects["egg_white"].scale.x = 1.12
    bpy.data.objects["egg_white"].scale.y = 1.12
    bpy.data.objects["egg_yolk"].scale.x = 1.12
    bpy.data.objects["egg_yolk"].scale.y = 1.12

    font_path = Path("C:/Windows/Fonts/YuGothB.ttc")
    font = bpy.data.fonts.load(str(font_path)) if font_path.exists() else bpy.data.fonts.get("Bfont")
    add_text("front_ramen_text", "ラーメン", (0.0, -1.43, 3.575), (math.pi / 2, 0.0, 0.0), 0.50, neon, font)
    add_text("side_number_26", "26", (1.94, 0.35, 3.48), (0.0, -math.pi / 2, 0.0), 0.56, neon, font)

    add_camera_and_lights()
    organize_collections()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Tutorial_Ramen_World")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.006, 0.009, 0.022, 1)
    background.inputs["Strength"].default_value = 0.18
    scene.render.filepath = str(RUN_DIR / "ramen_machine_material_v4.png")
    bpy.ops.render.render(write_still=True)

    modifiers = {
        obj.name: [{"name": modifier.name, "type": modifier.type, "applied": False} for modifier in obj.modifiers]
        for obj in scene.objects if obj.modifiers
    }
    report = {
        "schema_version": 1,
        "record_type": "TUTORIAL_PRODUCTION_PASS",
        "source": "https://www.youtube.com/watch?v=K7__BjW4UWE",
        "blender_version": bpy.app.version_string,
        "object_count": len(scene.objects),
        "mesh_count": sum(obj.type == "MESH" for obj in scene.objects),
        "curve_count": sum(obj.type in {"CURVE", "FONT"} for obj in scene.objects),
        "collections": sorted(collection.name for collection in bpy.data.collections),
        "live_modifiers": modifiers,
        "modifiers_applied": False,
        "source_thumbnail_review": "PENDING_FINAL_COMPARISON",
    }
    (RUN_DIR / "production_pass_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN_DIR / "ramen_machine_tutorial_final.blend"))


if __name__ == "__main__":
    main()
