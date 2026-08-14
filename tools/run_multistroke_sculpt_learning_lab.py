"""Interactive multi-stroke sculpt study derived from Blender's sculpt fundamentals.

This is deliberately not a primitive-assembly asset.  It starts from one dense,
non-spherical continuous surface, performs real Sculpt Mode brush operators in a
VIEW_3D context, and measures both useful form development and an over-smoothing
failure control.  Run in a normal (hidden is fine) Blender process, not --background.
"""

from __future__ import annotations

import json
import traceback
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_multistroke-sculpt-learning"
OUT.mkdir(parents=True, exist_ok=True)


def find_view3d():
    window = bpy.context.window_manager.windows[0]
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            region = next(region for region in area.regions if region.type == "WINDOW")
            return window, area, region
    raise RuntimeError("No VIEW_3D area available; this is an interactive-context lab")


def activate(obj):
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def volume(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    value = abs(bm.calc_volume(signed=True))
    bm.free()
    return value


def stats(obj):
    coords = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return {
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "volume": volume(obj),
        "bounds": {
            axis: [min(co[index] for co in coords), max(co[index] for co in coords)]
            for index, axis in enumerate(("x", "y", "z"))
        },
    }


def make_fixture():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1.0)
    obj = bpy.context.object
    obj.name = "OrganicMask_Sculpt"
    # An applied ellipsoid creates a continuous, non-spherical base whose front
    # plane and silhouette can be developed by brush strokes.
    obj.scale = (1.12, 0.72, 1.34)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def stroke_path(view_cx, view_cy, start_x, start_y, points, dx, dy, size, pressure):
    result = []
    for index in range(points):
        mouse_x = start_x + dx * index
        mouse_y = start_y + dy * index
        # brush_stroke can report FINISHED while doing nothing when scripted
        # events omit a valid surface location.  Front view maps X/Z to screen;
        # the negative-Y value places events on the visible ellipsoid surface.
        world_x = (mouse_x - view_cx) / 150.0
        world_z = (mouse_y - view_cy) / 150.0
        result.append({
            "name": "",
            "location": (world_x, -0.70, world_z),
            "mouse": (mouse_x, mouse_y),
            "mouse_event": (mouse_x, mouse_y),
            "pressure": pressure,
            "size": size,
            "time": index * 0.04,
            "is_start": index == 0,
            "x_tilt": 0.0,
            "y_tilt": 0.0,
        })
    return result


def apply_stroke(tool, stroke):
    bpy.ops.wm.tool_set_by_id(name=tool)
    result = bpy.ops.sculpt.brush_stroke(stroke=stroke, mode="NORMAL")
    if "FINISHED" not in result:
        raise RuntimeError(f"{tool} stroke failed: {sorted(result)}")
    return sorted(result)


def render_object(obj, path):
    activate(obj)
    bpy.ops.object.shade_smooth_by_angle()
    bpy.ops.object.camera_add(location=(3.6, -7.2, 2.7))
    camera = bpy.context.object
    direction = obj.location - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 58
    bpy.context.scene.camera = camera
    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.5, 5.0))
    bpy.context.object.data.energy = 850
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 4.0
    bpy.ops.object.light_add(type="AREA", location=(4.0, -2.0, 1.0))
    bpy.context.object.data.energy = 500
    bpy.context.object.data.size = 3.0
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    scene.world.color = (0.018, 0.018, 0.025)
    bpy.ops.render.render(write_still=True)


def main():
    report = {
        "lab": "multi_stroke_sculpt_learning",
        "blender_version": bpy.app.version_string,
        "lesson_claims_tested": [
            "form is built by moving surface volume, not by assembling parts",
            "brush radius and strength change the scale of the edit",
            "smoothing averages vertices and can remove volume",
        ],
        "failures": [],
    }
    try:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        sculpt = make_fixture()
        baseline = stats(sculpt)
        before = [vertex.co.copy() for vertex in sculpt.data.vertices]
        window, area, region = find_view3d()
        with bpy.context.temp_override(window=window, area=area, region=region, active_object=sculpt, object=sculpt):
            bpy.ops.object.mode_set(mode="SCULPT")
            bpy.ops.view3d.view_axis(type="FRONT", align_active=True)
            bpy.ops.view3d.view_selected(use_all_regions=False)
            cx, cy = region.width // 2, region.height // 2
            operations = []
            # Broad primary/secondary volume passes: forehead ridge, paired cheek
            # masses and a vertical nose plane.  Every item is a real brush call.
            for args in (
                (cx - 95, cy + 95, 7, 28, 0, 64.0, 0.42),
                (cx - 95, cy + 40, 7, 28, 0, 58.0, 0.36),
                (cx - 110, cy - 35, 5, 22, 4, 54.0, 0.34),
                (cx + 20, cy - 18, 5, 22, -4, 54.0, 0.34),
                (cx, cy + 78, 7, 0, -24, 38.0, 0.30),
            ):
                operations.append({"tool": "Draw", "result": apply_stroke("builtin_brush.Draw", stroke_path(cx, cy, *args))})
            # Two crease passes articulate a deliberately non-symmetric brow/cheek
            # transition so this is not just a smooth inflated blob.
            for args in (
                (cx - 95, cy + 58, 6, 25, -5, 28.0, 0.44),
                (cx - 65, cy - 12, 5, 24, 5, 25.0, 0.38),
            ):
                operations.append({"tool": "Crease", "result": apply_stroke("builtin_brush.Crease", stroke_path(cx, cy, *args))})
            bpy.ops.object.mode_set(mode="OBJECT")

        developed = stats(sculpt)
        after = [vertex.co.copy() for vertex in sculpt.data.vertices]
        displacements = [(a - b).length for a, b in zip(after, before)]
        moved = sum(distance > 1e-6 for distance in displacements)

        # Failure control: repeated broad smoothing on a copy.  The lesson warns
        # that smoothing is also volume loss; this branch measures that cost.
        over = sculpt.copy()
        over.data = sculpt.data.copy()
        over.name = "OrganicMask_OverSmoothed_FAILURE"
        bpy.context.scene.collection.objects.link(over)
        sculpt.hide_set(True)
        activate(over)
        with bpy.context.temp_override(window=window, area=area, region=region, active_object=over, object=over):
            bpy.ops.object.mode_set(mode="SCULPT")
            bpy.ops.view3d.view_axis(type="FRONT", align_active=True)
            bpy.ops.view3d.view_selected(use_all_regions=False)
            cx, cy = region.width // 2, region.height // 2
            smooth_results = []
            for offset in (-70, -30, 10, 50, 90):
                smooth_results.append(apply_stroke("builtin_brush.Smooth", stroke_path(cx, cy, cx - 110, cy + offset, 10, 25, 0, 95.0, 1.0)))
            bpy.ops.object.mode_set(mode="OBJECT")
        oversmoothed = stats(over)
        over.hide_set(True)
        sculpt.hide_set(False)

        report.update({
            "fixture": "single continuous applied ellipsoid; no assembled primitive parts",
            "operations": operations,
            "baseline": baseline,
            "developed": developed,
            "over_smoothed_failure": {
                "stats": oversmoothed,
                "smooth_results": smooth_results,
                "volume_change_from_developed": oversmoothed["volume"] - developed["volume"],
                "volume_change_fraction": (oversmoothed["volume"] - developed["volume"]) / developed["volume"],
            },
            "moved_vertices": moved,
            "max_displacement": max(displacements),
        })
        report["assertions"] = {
            "seven_real_brush_strokes_finished": len(operations) == 7,
            "multi_stroke_form_moved_many_vertices": moved >= 400,
            "form_changed_measurably": max(displacements) > 0.05,
            "smoothing_changed_volume": abs(report["over_smoothed_failure"]["volume_change_fraction"]) > 0.0005,
        }
        report["pass"] = all(report["assertions"].values())
        render_object(sculpt, OUT / "developed_sculpt.png")
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "multistroke_sculpt_learning.blend"))
    except Exception as exc:
        report["failures"].append({"error": str(exc), "traceback": traceback.format_exc()})
        report["pass"] = False
    (OUT / "multistroke_sculpt_learning_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "DONE").write_text("done", encoding="utf-8")
    print("MULTISTROKE_SCULPT_RESULT:" + json.dumps(report))
    bpy.ops.wm.quit_blender()


main()
