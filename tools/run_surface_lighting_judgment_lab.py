"""Test whether a neutral directional review rig reveals a localized surface defect.

The geometry, material, camera, exposure, and render engine are fixed.  Only the
lighting rig changes.  A flat frontal-light failure control is compared with an
asymmetric key/fill/rim rig derived from Blender's Three Point Lighting lesson.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_surface-lighting-judgment"
OUT.mkdir(parents=True, exist_ok=True)


def activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_render = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def make_pair():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=1.0)
    clean = bpy.context.object
    clean.name = "ReviewSurface_Clean"
    clean.scale = (1.35, 0.62, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    defect = clean.copy()
    defect.data = clean.data.copy()
    defect.name = "ReviewSurface_LocalDent"
    bpy.context.scene.collection.objects.link(defect)
    # Localized front-surface depression with a faint rebound ring.  Silhouette
    # is intentionally untouched so this is a highlight/surface test.
    for vertex in defect.data.vertices:
        co = vertex.co
        if co.y >= 0.0:
            continue
        dx = co.x - 0.32
        dz = co.z - 0.18
        distance = math.sqrt(dx * dx + dz * dz)
        if distance < 0.34:
            gaussian = math.exp(-((distance / 0.17) ** 2))
            rebound = 0.28 * math.exp(-(((distance - 0.25) / 0.055) ** 2))
            co.y += 0.065 * gaussian - 0.018 * rebound
    clean.hide_render = True
    defect.hide_render = True
    return clean, defect


def material_for(*objects):
    material = bpy.data.materials.new("NeutralReviewMaterial")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.22, 0.24, 0.27, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = 0.32
    for obj in objects:
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def point_at(obj, target=(0.0, 0.0, 0.0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area(name, location, energy, size, color=(1.0, 1.0, 1.0)):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    point_at(light)
    return light


def clear_lights():
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)


def set_rig(kind):
    clear_lights()
    if kind == "flat_front_failure":
        add_area("FlatFront", (0.0, -4.5, 0.0), 1200, 12.0)
    elif kind == "key_fill_rim_review":
        add_area("Key", (4.8, -1.2, 1.0), 1400, 0.65)
        add_area("Fill", (-3.5, -3.0, 0.7), 100, 4.0, (0.75, 0.86, 1.0))
        add_area("Rim", (2.2, 2.0, 2.8), 1250, 1.8, (1.0, 0.78, 0.58))
    else:
        raise ValueError(kind)


def render(obj, rig, label):
    for candidate in (bpy.data.objects["ReviewSurface_Clean"], bpy.data.objects["ReviewSurface_LocalDent"]):
        candidate.hide_render = candidate != obj
    set_rig(rig)
    path = OUT / f"{label}.png"
    scene = bpy.context.scene
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    # Render Result may expose an empty pixel sequence after write_still in a
    # background process.  Reload the durable artifact before measurement.
    image = bpy.data.images.load(str(path), check_existing=False)
    pixels = list(image.pixels[:])
    bpy.data.images.remove(image)
    return path, pixels


def image_difference(a, b):
    if len(a) != len(b):
        raise ValueError("render buffers differ")
    rgb_abs = []
    changed = 0
    for index in range(0, len(a), 4):
        delta = (abs(a[index] - b[index]) + abs(a[index + 1] - b[index + 1]) + abs(a[index + 2] - b[index + 2])) / 3.0
        rgb_abs.append(delta)
        if delta > 0.015:
            changed += 1
    return {
        "mean_absolute_rgb": sum(rgb_abs) / len(rgb_abs),
        "max_absolute_rgb": max(rgb_abs),
        "pixels_over_0_015": changed,
        "pixel_count": len(rgb_abs),
    }


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    clean, defect = make_pair()
    material_for(clean, defect)
    bpy.ops.object.camera_add(location=(0.0, -6.2, 0.15))
    camera = bpy.context.object
    point_at(camera, (0.0, 0.0, 0.05))
    camera.data.lens = 66
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.008, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"

    outputs = {}
    buffers = {}
    for rig in ("flat_front_failure", "key_fill_rim_review"):
        for obj, variant in ((clean, "clean"), (defect, "defect")):
            path, pixels = render(obj, rig, f"{rig}_{variant}")
            outputs[f"{rig}_{variant}"] = str(path)
            buffers[f"{rig}_{variant}"] = pixels
    flat = image_difference(buffers["flat_front_failure_clean"], buffers["flat_front_failure_defect"])
    review = image_difference(buffers["key_fill_rim_review_clean"], buffers["key_fill_rim_review_defect"])
    ratio = review["mean_absolute_rgb"] / flat["mean_absolute_rgb"] if flat["mean_absolute_rgb"] else float("inf")
    report = {
        "lab": "surface_lighting_judgment",
        "blender_version": bpy.app.version_string,
        "controlled_variables": ["topology", "material", "camera", "engine", "resolution", "exposure"],
        "defect": "localized 0.065-unit front-surface dent with rebound ring; silhouette unchanged",
        "flat_front_failure": flat,
        "key_fill_rim_review": review,
        "diagnostic_to_flat_mean_difference_ratio": ratio,
        "outputs": outputs,
        "assertions": {
            "defect_changes_pixels_under_both_rigs": flat["pixels_over_0_015"] > 0 and review["pixels_over_0_015"] > 0,
            "asymmetric_review_reveals_more_mean_difference": ratio > 1.25,
            "asymmetric_review_reveals_more_changed_pixels": review["pixels_over_0_015"] > flat["pixels_over_0_015"],
        },
    }
    report["pass"] = all(report["assertions"].values())
    (OUT / "surface_lighting_judgment_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "surface_lighting_judgment.blend"))
    print("SURFACE_LIGHTING_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("diagnostic lighting did not outperform flat-front control")


main()
