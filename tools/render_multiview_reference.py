"""Render neutral orthographic reference views from a permitted local GLTF.

The source mesh is treated as a visual reference only: this tool records file
provenance, auto-frames evaluated bounds, and renders pixels. It does not emit
or inspect source topology statistics for the modeling agent.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "blender_ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from render_passes import render_silhouette

VIEWS = {
    "front": Vector((0.0, -1.0, 0.0)),
    "side": Vector((1.0, 0.0, 0.0)),
    "top": Vector((0.0, 0.0, 1.0)),
    "isometric": Vector((1.0, -1.0, 0.8)).normalized(),
}


def args():
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) not in (2, 3, 4):
        raise SystemExit("expected SOURCE_GLTF OUTPUT_DIR [ASSET_PAGE] [EXCLUDE_NAME_REGEX] after --")
    asset_page = values[2] if len(values) == 3 else None
    if len(values) >= 3:
        asset_page = values[2]
    exclude_name_regex = values[3] if len(values) == 4 else None
    return Path(values[0]).resolve(), Path(values[1]).resolve(), asset_page, exclude_name_regex


def assign_neutral_material(objects):
    material = bpy.data.materials.new("Neutral reference clay")
    material.use_nodes = True
    principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = (0.16, 0.19, 0.23, 1.0)
    principled.inputs["Metallic"].default_value = 0.08
    principled.inputs["Roughness"].default_value = 0.42
    for obj in objects:
        obj.data.materials.clear()
        obj.data.materials.append(material)


def combined_bounds(objects):
    points = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        points.extend(obj.matrix_world @ vertex.co for vertex in mesh.vertices)
        evaluated.to_mesh_clear()
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return minimum, maximum


def render_beauty(output, objects, center, diagonal, view):
    scene = bpy.context.scene
    direction = VIEWS[view]
    bpy.ops.object.camera_add(location=center + direction * diagonal * 2.2)
    camera = bpy.context.object
    camera.name = f"Reference_{view}_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = diagonal * 1.12
    camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    scene.camera = camera
    for obj in bpy.data.objects:
        obj.hide_render = obj not in objects and obj is not camera and obj.type != "LIGHT"
    shading = scene.display.shading
    scene.render.engine = "BLENDER_WORKBENCH"
    shading.type = "SOLID"
    shading.light = "STUDIO"
    shading.color_type = "SINGLE"
    shading.single_color = (0.32, 0.36, 0.42)
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    scene.render.filepath = str(output / f"reference_{view}_beauty.png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)


def main():
    source, output, asset_page, exclude_name_regex = args()
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    excluded = []
    pattern = re.compile(exclude_name_regex, re.IGNORECASE) if exclude_name_regex else None
    objects = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if pattern and pattern.search(obj.name):
            excluded.append(obj.name)
            obj.hide_render = True
            continue
        objects.append(obj)
    if not objects:
        raise SystemExit("GLTF imported no mesh objects")
    assign_neutral_material(objects)
    names = [obj.name for obj in objects]
    minimum, maximum = combined_bounds(objects)
    center = (minimum + maximum) * 0.5
    diagonal = (maximum - minimum).length

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.055, 0.055, 0.055)
    silhouettes = []
    for view in ("front", "side", "top"):
        silhouettes.append(render_silhouette(names, str(output / f"reference_{view}_mask.png"), view=view, resolution=720, margin=1.12, frame_name=names))
        render_beauty(output, objects, center, diagonal, view)
    render_beauty(output, objects, center, diagonal, "isometric")

    manifest = {
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "license": "CC0 via Poly Haven",
        "asset_page": asset_page,
        "neutral_material_override": True,
        "neutral_review_engine": "BLENDER_WORKBENCH_STUDIO_CAVITY",
        "excluded_source_objects": excluded,
        "exclude_name_regex": exclude_name_regex,
        "use_boundary": "Source geometry is used only to produce neutral reference renders; its topology is not evaluated as modeling guidance or copied into the candidate.",
        "views": ["front", "side", "top", "isometric"],
        "silhouette_reports": silhouettes,
    }
    (output / "reference_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


main()
