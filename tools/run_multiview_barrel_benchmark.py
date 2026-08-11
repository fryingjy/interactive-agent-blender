"""Build staged measured-reference industrial barrel candidates.

Usage: blender --background --factory-startup --python this_file.py -- STAGE
Stages deliberately separate primary silhouette, secondary form, and fittings.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from profile_mesh import capped_cylinder, revolve_closed_profile
from render_passes import render_diagnostic_pass, render_silhouette

OUT = ROOT / "runs" / "2026-08-11_multiview-barrel"
COLLECTION_NAME = "MeasuredBarrel"


def material(name, color, metallic, roughness):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1.0)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return value


def body_profile(stage):
    # Authored normalized radius-height cross-section.  Stage 2 replaces the
    # simple wall with measured major hoops and eleven shallow corrugations.
    outer = [(1.49, -2.35), (1.49, 2.35)]
    if stage >= 2:
        # One continuous manufactured skin: rolled lower seam, quiet lower
        # panel, lower major hoop, corrugated band, upper major hoop, quiet
        # upper panel, and rolled top seam.  Every adjacent profile pair
        # becomes a connected circumferential quad strip.
        outer = [
            (1.50, -2.40), (1.54, -2.39),
            (1.56, -2.35), (1.53, -2.31), (1.49, -2.28),
            (1.49, -1.00), (1.49, -0.98), (1.54, -0.95),
            (1.56, -0.92), (1.54, -0.89), (1.49, -0.86),
        ]
        for index in range(11):
            center = -0.75 + index * 0.15
            outer.extend(((1.49, center - 0.052), (1.52, center), (1.49, center + 0.052)))
        outer.extend([
            (1.49, 0.81), (1.54, 0.83), (1.56, 0.86),
            (1.54, 0.89), (1.49, 0.92), (1.49, 2.28),
            (1.53, 2.31), (1.56, 2.35), (1.54, 2.39),
            (1.50, 2.40),
        ])
    # Return down the inside to close a real thin-walled shell.
    return outer + [(1.44, 2.35), (1.44, -2.35)]


def ring(name, center_z, radius, tube_radius, collection, material_value):
    profile = []
    for index in range(16):
        angle = 2 * math.pi * index / 16
        profile.append((radius + tube_radius * math.cos(angle), center_z + tube_radius * math.sin(angle)))
    obj = revolve_closed_profile(name, profile, segments=96, collection=collection)
    obj.data.materials.append(material_value)
    return obj


def add_uv_and_bevel(obj, width=0.012):
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="GeneratedUV")
    bevel = obj.modifiers.new("Manufactured_Edge_Soften", "BEVEL")
    bevel.width = width
    bevel.segments = 2
    bevel.limit_method = "ANGLE"


def build(stage):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    red = material("Painted_Red_Steel", (0.24, 0.018, 0.012), 0.72, 0.34)
    steel = material("Exposed_Steel", (0.32, 0.34, 0.36), 0.9, 0.22)
    body = revolve_closed_profile("Barrel_Body_Profile", body_profile(stage), segments=96, collection=collection)
    body.data.materials.append(red)
    # The profile already contains the support loops that define every edge.
    # A blanket angle bevel is both unnecessary and can collapse the tight
    # rolled-seam loops into zero-area evaluated faces.
    objects = [body]
    # The lid is a primary mass because the top-view silhouette must be a
    # filled disk, not the annulus produced by the wall alone.
    lid = capped_cylinder("Recessed_Top_Lid", radius=1.455, z_bottom=2.31, z_top=2.35, segments=96, collection=collection)
    lid.data.materials.append(red)
    add_uv_and_bevel(lid, 0.008)
    objects.append(lid)
    if stage >= 3:
        # Coordinates are converted from measured top-view fractions into a
        # centered diameter-3 coordinate system (image Y maps to world Y).
        fittings = (
            ("Large_Bung", 0.762, 0.855, 0.18, 0.075),
            ("Small_Vent", -0.965, -1.00, 0.1125, 0.055),
        )
        for name, x_value, y_value, radius, height in fittings:
            fitting = capped_cylinder(name, radius=radius, z_bottom=2.34, z_top=2.34 + height, segments=48, collection=collection)
            fitting.location.x = x_value
            fitting.location.y = y_value
            fitting.data.materials.append(steel)
            add_uv_and_bevel(fitting, 0.01)
            objects.append(fitting)
            objects.append(ring(name + "_Collar", 2.355, radius * 1.08, radius * 0.12, collection, steel))
            objects[-1].location.x = x_value
            objects[-1].location.y = y_value
    return objects


def point_at(obj, target=(0.0, 0.0, 0.0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area_light(name, location, energy, size, color=(1.0, 1.0, 1.0)):
    data = bpy.data.lights.new(name + "Data", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj)


def render_beauty(stage_dir, objects):
    scene = bpy.context.scene
    camera_data = bpy.data.cameras.new("Barrel_Review_Camera_Data")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 6.8
    camera = bpy.data.objects.new("Barrel_Review_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    add_area_light("Warm_Key", (-4.0, -5.0, 7.0), 1150, 4.0, (1.0, 0.72, 0.58))
    add_area_light("Cool_Fill", (5.0, -3.0, 3.0), 850, 4.0, (0.55, 0.72, 1.0))
    add_area_light("Top_Rim", (1.0, 3.0, 7.0), 1000, 3.0)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    for label, location in (
        ("front", (0.0, -11.0, 0.0)),
        ("top", (0.0, 0.0, 11.0)),
        ("isometric", (7.5, -7.5, 6.8)),
    ):
        camera.location = location
        point_at(camera)
        scene.render.filepath = str(stage_dir / f"candidate_{label}_beauty.png")
        bpy.ops.render.render(write_still=True)


def render_stage(stage, objects):
    stage_dir = OUT / f"stage{stage}"
    stage_dir.mkdir(parents=True, exist_ok=True)
    names = [obj.name for obj in objects]
    renders = []
    for view in ("front", "side", "top", "isometric"):
        renders.append(render_diagnostic_pass(names, str(stage_dir / f"candidate_{view}_solid.png"), "solid", view=view, resolution=720, margin=1.28))
        if view != "isometric":
            renders.append(render_silhouette(names, str(stage_dir / f"candidate_{view}_mask.png"), view=view, resolution=720, margin=1.28))
    if stage == 3:
        render_beauty(stage_dir, objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(stage_dir / f"barrel_stage{stage}.blend"))
    report = {
        "stage": stage,
        "intent": {1: "primary silhouette and proportion", 2: "secondary corrugation, hoops, seams, and recessed lid", 3: "top-view fitting placement and manufactured edge finish"}[stage],
        "construction": "explicit authored radial profiles revolved around Z; no mesh primitive operators",
        "mesh_primitive_operator_calls": 0,
        "body_topology": "single connected all-quad revolved shell; corrugations, major hoops, and rolled seams are continuous profile loops",
        "objects": names,
        "renders": renders,
    }
    (stage_dir / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("BARREL_STAGE_RESULT:" + json.dumps(report))


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1 or args[0] not in {"1", "2", "3"}:
        raise SystemExit("expected stage 1, 2, or 3 after --")
    stage = int(args[0])
    render_stage(stage, build(stage))


main()
