"""Reproduce and transfer the verified orthographic reference-image setup lesson."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-16_reference-image-alignment-transfer"
if str(ROOT / "blender_ops") not in sys.path:
    sys.path.insert(0, str(ROOT / "blender_ops"))

import modeler_server


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)


def write_card(path: Path, *, vertical: bool):
    width = height = 256
    image = bpy.data.images.new(path.stem, width=width, height=height, alpha=True)
    pixels = [1.0] * (width * height * 4)
    for y in range(height):
        for x in range(width):
            index = (y * width + x) * 4
            border = x in range(28, 34) or x in range(222, 228) or y in range(28, 34) or y in range(222, 228)
            axis_mark = (abs(x - 128) < 3) if vertical else (abs(y - 128) < 3)
            landmark = (x - 128) ** 2 + (y - (176 if vertical else 80)) ** 2 < 11 ** 2
            if border:
                pixels[index:index + 4] = [0.08, 0.12, 0.18, 1.0]
            elif axis_mark:
                pixels[index:index + 4] = [0.10, 0.35, 0.75, 1.0]
            elif landmark:
                pixels[index:index + 4] = [0.85, 0.08, 0.05, 1.0]
            else:
                pixels[index:index + 4] = [0.92, 0.92, 0.88, 1.0]
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def add_proxy(name, axis, location, color, custom_rotation=None):
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=location)
    obj = bpy.context.object
    obj.name = name
    if axis == "FRONT":
        obj.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
    elif axis == "RIGHT":
        obj.rotation_euler = (0.0, math.pi / 2.0, 0.0)
    elif axis == "CUSTOM":
        obj.rotation_euler = custom_rotation
    material = bpy.data.materials.new(f"{name}_Material")
    material.diffuse_color = (*color, 1.0)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Visible edge", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 2
    return obj


def add_anchor(name, location):
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=location)
    cube = bpy.context.object
    cube.name = name
    material = bpy.data.materials.new(f"{name}_Material")
    material.diffuse_color = (0.12, 0.14, 0.18, 1.0)
    cube.data.materials.append(material)
    bevel = cube.modifiers.new("Edge radius", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 3
    return cube


def render_group(name, objects, output_path):
    for obj in bpy.context.scene.objects:
        obj.hide_render = obj not in objects
    camera_data = bpy.data.cameras.new(f"{name}_Camera")
    camera = bpy.data.objects.new(f"{name}_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (6.0, -7.0, 5.0)
    direction = -camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 6.0
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
    for obj in bpy.context.scene.objects:
        obj.hide_render = False


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    front_path = OUT / "project_owned_front_card.png"
    right_path = OUT / "project_owned_right_card.png"
    write_card(front_path, vertical=True)
    write_card(right_path, vertical=False)
    typed_server = modeler_server.ModelerServer()
    create_reference = typed_server.cmd_create_reference_image
    audit_references = typed_server.cmd_audit_reference_images

    failure = create_reference(
        "Perspective_Control",
        front_path,
        "CUSTOM",
        collection_name="PERSPECTIVE_FAILURE_CONTROL",
        calibrated=False,
        custom_rotation=(math.radians(63), 0.0, math.radians(27)),
    )
    reproduction = create_reference(
        "Front_Orthographic_Reproduction",
        front_path,
        "FRONT",
        collection_name="ORTHOGRAPHIC_REPRODUCTION",
    )
    transfer_front = create_reference(
        "Transfer_Front",
        front_path,
        "FRONT",
        collection_name="MULTIVIEW_TRANSFER",
    )
    transfer_right = create_reference(
        "Transfer_Right",
        right_path,
        "RIGHT",
        collection_name="MULTIVIEW_TRANSFER",
    )
    duplicate_front = create_reference(
        "Duplicate_Control_Front",
        front_path,
        "FRONT",
        collection_name="DUPLICATED_SINGLE_IMAGE_CONTROL",
    )
    duplicate_right = create_reference(
        "Duplicate_Control_Right",
        front_path,
        "RIGHT",
        collection_name="DUPLICATED_SINGLE_IMAGE_CONTROL",
    )

    audits = {
        "perspective_failure": audit_references("PERSPECTIVE_FAILURE_CONTROL"),
        "orthographic_reproduction": audit_references("ORTHOGRAPHIC_REPRODUCTION"),
        "multiview_transfer": audit_references(
            "MULTIVIEW_TRANSFER", require_distinct_sources=True
        ),
        "duplicated_single_image_control": audit_references(
            "DUPLICATED_SINGLE_IMAGE_CONTROL", require_distinct_sources=True
        ),
    }

    visual_groups = {
        "perspective_failure": [
            add_anchor("Failure_Anchor", (0.0, 0.0, 0.0)),
            add_proxy(
                "Failure_Card_Proxy",
                "CUSTOM",
                (0.0, 0.0, 0.0),
                (0.75, 0.12, 0.08),
                custom_rotation=(math.radians(63), 0.0, math.radians(27)),
            ),
        ],
        "orthographic_reproduction": [
            add_anchor("Reproduction_Anchor", (0.0, 0.0, 0.0)),
            add_proxy("Front_Card_Proxy", "FRONT", (0.0, 0.35, 0.0), (0.10, 0.45, 0.80)),
        ],
        "multiview_transfer": [
            add_anchor("Transfer_Anchor", (0.0, 0.0, 0.0)),
            add_proxy("Transfer_Front_Proxy", "FRONT", (0.0, 0.5, 0.0), (0.10, 0.45, 0.80)),
            add_proxy("Transfer_Right_Proxy", "RIGHT", (0.5, 0.0, 0.0), (0.08, 0.65, 0.30)),
        ],
    }
    for group_name, objects in visual_groups.items():
        render_group(group_name, objects, OUT / f"{group_name}_solid.png")

    checks = {
        "perspective_control_rejected": not audits["perspective_failure"]["pass"],
        "orthographic_reproduction_passes": audits["orthographic_reproduction"]["pass"],
        "different_source_multiview_transfer_passes": audits["multiview_transfer"]["pass"],
        "duplicated_single_image_not_true_multiview": not audits["duplicated_single_image_control"]["pass"],
        "all_reference_images_remain_editable_empties": all(
            obj.type == "EMPTY" and obj.empty_display_type == "IMAGE"
            for obj in bpy.data.objects
            if "reference_view_axis" in obj
        ),
    }
    report = {
        "experiment": "verified orthographic reference setup reproduction and different-view transfer",
        "blender_version": bpy.app.version_string,
        "source_episode_review": "runs/2026-08-16_real-video-reference-setup-review/episode_review.json",
        "source_range_analysis": "runs/2026-08-16_real-video-reference-setup-review/gemini_range_0024_0124.json",
        "typed_operation": "ModelerServer.cmd_create_reference_image -> blender_ops.object_ops.create_reference_image",
        "created": [failure, reproduction, transfer_front, transfer_right, duplicate_front, duplicate_right],
        "audits": audits,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": (
            "The run validates editable Image Empty creation, principal-axis alignment, and rejection "
            "of a duplicated single image as distinct multi-view evidence. It does not establish that "
            "arbitrary photographs are orthographic or prove reference-to-model fidelity."
        ),
    }
    (OUT / "reference_image_alignment_transfer_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "reference_image_alignment_transfer.blend"))
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
