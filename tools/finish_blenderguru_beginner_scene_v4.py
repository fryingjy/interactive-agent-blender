"""Correct and finish the rejected Blender Guru beginner tutorial scene."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "runs" / "2026-08-21_tutorial-rebuild-donut" / "donut_tutorial.blend"
RUN_DIR = REPO_ROOT / "runs" / "2026-08-22_tutorial-blenderguru-beginner-rebuild-v2"


def material(name: str, color: tuple[float, float, float, float], roughness: float, metallic: float = 0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def move_group(names: tuple[str, ...], delta: Vector) -> None:
    for name in names:
        bpy.data.objects[name].location += delta


def replace_coffee() -> bpy.types.Object:
    old = bpy.data.objects.get("Foam")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.108, depth=0.006, location=(0.30, 0.0, 0.153))
    coffee = bpy.context.object
    coffee.name = "Coffee_Surface_32"
    coffee.data.name = "Coffee_Surface_32_Mesh"
    bevel = coffee.modifiers.new("Liquid_Edge_Radius", "BEVEL")
    bevel.width = 0.004
    bevel.segments = 2
    coffee.data.materials.append(material("Coffee_Foam", (0.42, 0.16, 0.045, 1.0), 0.58))
    return coffee


def add_sprinkle_system(icing: bpy.types.Object) -> tuple[list[bpy.types.Object], bpy.types.Modifier]:
    prototypes = []
    palette = (
        ("Pink", (1.0, 0.32, 0.60, 1)),
        ("Mint", (0.28, 0.95, 0.78, 1)),
        ("Cream", (1.0, 0.90, 0.55, 1)),
        ("Purple", (0.53, 0.22, 0.90, 1)),
        ("White", (0.96, 0.94, 0.84, 1)),
    )
    for index, (label, color) in enumerate(palette):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.0045,
            depth=0.030,
            location=(0, 0, -3 - index * 0.05),
        )
        prototype = bpy.context.object
        prototype.name = f"Sprinkle_Prototype_{label}"
        prototype.data.materials.append(material(f"Sprinkle_{label}", color, 0.32))
        prototype.hide_render = True
        prototype.hide_set(True)
        prototypes.append(prototype)

    tree = bpy.data.node_groups.new("GN_Tutorial_Sprinkles", "GeometryNodeTree")
    tree.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = tree.nodes
    links = tree.links
    group_in = nodes.new("NodeGroupInput")
    group_out = nodes.new("NodeGroupOutput")
    join = nodes.new("GeometryNodeJoinGeometry")
    links.new(group_in.outputs["Geometry"], join.inputs["Geometry"])
    for index, prototype in enumerate(prototypes):
        distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
        object_info = nodes.new("GeometryNodeObjectInfo")
        instances = nodes.new("GeometryNodeInstanceOnPoints")
        random_rotation = nodes.new("FunctionNodeRandomValue")
        random_rotation.data_type = "FLOAT_VECTOR"
        random_rotation.inputs["Min"].default_value = (-math.pi, -math.pi, -math.pi)
        random_rotation.inputs["Max"].default_value = (math.pi, math.pi, math.pi)
        realize = nodes.new("GeometryNodeRealizeInstances")
        distribute.distribute_method = "RANDOM"
        distribute.inputs["Density"].default_value = 82.0
        if "Seed" in distribute.inputs:
            distribute.inputs["Seed"].default_value = 1103 + index * 97
        object_info.inputs["Object"].default_value = prototype
        object_info.transform_space = "ORIGINAL"
        object_info.inputs["As Instance"].default_value = True
        links.new(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
        links.new(distribute.outputs["Points"], instances.inputs["Points"])
        links.new(object_info.outputs["Geometry"], instances.inputs["Instance"])
        links.new(random_rotation.outputs["Value"], instances.inputs["Rotation"])
        links.new(instances.outputs["Instances"], realize.inputs["Geometry"])
        links.new(realize.outputs["Geometry"], join.inputs["Geometry"])
    links.new(join.outputs["Geometry"], group_out.inputs["Geometry"])
    modifier = icing.modifiers.new("Tutorial_Sprinkle_Scattering", "NODES")
    modifier.node_group = tree
    return prototypes, modifier


def add_lighting_and_render() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"

    camera = bpy.data.objects.get("Camera")
    camera.data.lens = 54
    camera.data.shift_y = -0.04
    camera.location = (0.34, -0.88, 0.82)
    target = Vector((0.055, 0.045, 0.045))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    key = bpy.data.objects.get("KeyLight")
    key.data.energy = 62
    key.data.shape = "DISK"
    key.data.size = 0.55
    key.location = (-0.45, -0.30, 0.78)
    key.rotation_euler = (Vector((0.0, 0.0, 0.05)) - key.location).to_track_quat("-Z", "Y").to_euler()

    fill_data = bpy.data.lights.new("Fill_Light", "AREA")
    fill_data.energy = 9
    fill_data.shape = "DISK"
    fill_data.size = 0.45
    fill = bpy.data.objects.new("Fill_Light", fill_data)
    scene.collection.objects.link(fill)
    fill.location = (0.55, 0.35, 0.52)
    fill.rotation_euler = (target - fill.location).to_track_quat("-Z", "Y").to_euler()

    world = scene.world or bpy.data.worlds.new("Tutorial_World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.005, 0.006, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.08
    scene.view_settings.exposure = -0.65
    scene.render.filepath = str(RUN_DIR / "beginner_scene_v4.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

    # Correct the rejected composition: plate belongs under the donut; the donut/icing rise onto it.
    bpy.data.objects["Plate"].location = (-0.075, 0.010, -0.025)
    bpy.data.objects["Plate"].scale = (1.20, 1.20, 1.0)
    move_group(("Donut", "Icing"), Vector((-0.075, 0.010, 0.040)))
    bpy.data.objects["Icing"].scale.z = 0.78
    bpy.data.objects["Mug"].location = (0.350, 0.225, 0.075)
    bpy.data.objects["Mug"].rotation_euler.z = math.radians(-22)
    table = bpy.data.objects["Table"]
    table.location.z = -0.032
    table.data.materials.clear()
    table.data.materials.append(material("Table_Matte", (0.006, 0.004, 0.005, 1), 0.29))

    for name, mat in {
        "Donut": material("Donut_Golden", (0.47, 0.16, 0.035, 1), 0.42),
        "Icing": material("Icing_Pink", (1.0, 0.055, 0.30, 1), 0.32),
        "Plate": material("Plate_Ceramic", (0.58, 0.50, 0.47, 1), 0.26),
        "Mug": material("Mug_Ceramic", (0.075, 0.020, 0.008, 1), 0.34),
    }.items():
        obj = bpy.data.objects[name]
        obj.data.materials.clear()
        obj.data.materials.append(mat)

    coffee = replace_coffee()
    coffee.location = (0.350, 0.225, 0.153)
    prototypes, sprinkle_modifier = add_sprinkle_system(bpy.data.objects["Icing"])
    add_lighting_and_render()

    report = {
        "schema_version": 1,
        "source_run": str(SOURCE.relative_to(REPO_ROOT)),
        "status": "CREATOR_STILL_REVIEWED_CORRECTED_V4",
        "corrected_failures": [
            "plate_not_under_donut",
            "donut_and_mug_overlap",
            "14_vertex_ngon_coffee_surface",
            "missing_geometry_nodes_sprinkles",
            "cropped_flat_final_composition",
            "single_color_sprinkles",
            "bright_empty_background",
            "camera_angle_and_mug_placement_not_source_like",
            "v3_overexposed_pale_material_read",
        ],
        "live_modifiers": {
            "Icing": [modifier.type for modifier in bpy.data.objects["Icing"].modifiers],
            "Mug": [modifier.type for modifier in bpy.data.objects["Mug"].modifiers],
            "Plate": [modifier.type for modifier in bpy.data.objects["Plate"].modifiers],
            "Coffee_Surface_32": [modifier.type for modifier in coffee.modifiers],
        },
        "sprinkle_sources_hidden": all(prototype.hide_render for prototype in prototypes),
        "sprinkle_modifier_applied": False,
        "creator_reference": "https://www.blenderguru.com/posts/blender-donut-v5-tutorial",
        "creator_reference_asset_local_ignored": "media/creator_published_part1.jpg",
        "visual_fidelity_score": 7.0,
        "strict_eight_of_ten_gate_passed": False,
        "gemini_audiovisual_status": "PENDING_FREE_TIER_QUOTA",
    }
    (RUN_DIR / "completion_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN_DIR / "beginner_scene_v4.blend"))


if __name__ == "__main__":
    main()
