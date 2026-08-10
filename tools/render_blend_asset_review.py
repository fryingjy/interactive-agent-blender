"""Render selected mesh objects from an already-open .blend under a neutral review rig.

Usage after Blender's own arguments:
    -- OUTPUT.png object_name [object_name ...]

The source file is never saved. Existing materials, cameras, lights, and non-target meshes are
temporarily excluded from the render so examples can be compared under one controlled setup.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args():
    argv = sys.argv
    if "--" not in argv:
        raise SystemExit("expected output and object names after --")
    values = argv[argv.index("--") + 1 :]
    if len(values) < 2:
        raise SystemExit("expected OUTPUT.png and at least one object name")
    return Path(values[0]).resolve(), values[1:]


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area(name, location, energy, size, target):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    point_at(light, target)


def main():
    output, names = args()
    output.parent.mkdir(parents=True, exist_ok=True)
    targets = []
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            raise SystemExit(f"missing mesh object: {name}")
        targets.append(obj)
    # Legacy examples can carry render/color-management enum state that is no
    # longer valid in the current Blender build.  Isolate review in a fresh
    # scene while reusing the requested object datablocks read-only.
    scene = bpy.data.scenes.new("AssetReview")
    bpy.context.window.scene = scene
    for obj in targets:
        scene.collection.objects.link(obj)
    target_set = set(targets)
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj.hide_render = obj not in target_set
    corners = [obj.matrix_world @ Vector(corner) for obj in targets for corner in obj.bound_box]
    mins = Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs = Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    center = (mins + maxs) * 0.5
    width = maxs.x - mins.x
    height = maxs.z - mins.z
    depth = maxs.y - mins.y

    material = bpy.data.materials.new("NeutralAssetReview")
    material.use_nodes = True
    # A neutral diffuse clay is deliberately used instead of a metal.  A metal
    # without a controlled reflection environment can collapse into a black
    # silhouette even when the geometry and lamps are valid.
    material.diffuse_color = (0.34, 0.39, 0.46, 1.0)
    material.metallic = 0.0
    material.roughness = 0.38
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (0.34, 0.39, 0.46, 1.0)
    principled.inputs["Metallic"].default_value = 0.0
    principled.inputs["Roughness"].default_value = 0.38
    for obj in targets:
        obj.data.materials.clear()
        obj.data.materials.append(material)

    for obj in list(bpy.data.objects):
        if obj.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.camera_add(location=(center.x, mins.y - max(6.0, depth * 6.0), center.z))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(height * 1.18, width * 1.18, 1.0)
    point_at(camera, center)
    scene.camera = camera
    extent = max(width, height, depth, 1.0)
    # Power scales with the asset extent because the lamps and their emitting
    # area scale with it.  This keeps a 3-unit dagger and a 13-unit greatsword
    # in the same useful exposure range.
    add_area("ReviewKey", center + Vector((-extent * 1.4, -extent * 1.6, extent * 1.2)), 1800 * extent, extent * 0.7, center)
    add_area("ReviewFill", center + Vector((extent * 1.2, -extent * 1.2, extent * 0.2)), 450 * extent, extent, center)
    add_area("ReviewRim", center + Vector((extent * 0.8, extent * 1.0, extent)), 2100 * extent, extent * 0.55, center)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("AssetReviewWorld")
    scene.world.color = (0.008, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.render.render(write_still=True)
    print(f"ASSET_REVIEW_RENDER:{output}")


main()
