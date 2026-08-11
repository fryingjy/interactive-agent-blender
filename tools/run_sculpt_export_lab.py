"""Interactive-context sculpt stroke plus OBJ/GLB export round trips.

Run in non-background Blender because Sculpt brush operators need a real VIEW_3D area.
The script always writes a report and exits Blender.
"""

from __future__ import annotations

import json
import math
import traceback
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_sculpt-export"
OUT.mkdir(parents=True, exist_ok=True)


def mesh_stats(obj):
    obj.data.calc_loop_triangles()
    return {
        "vertices": len(obj.data.vertices),
        "edges": len(obj.data.edges),
        "faces": len(obj.data.polygons),
        "triangles": len(obj.data.loop_triangles),
        "bounds": [round(v, 6) for axis in zip(*[obj.matrix_world @ Vector(corner) for corner in obj.bound_box]) for v in (min(axis), max(axis))],
        "materials": len(obj.data.materials),
        "uv_layers": len(obj.data.uv_layers),
    }


def find_view3d():
    window = bpy.context.window_manager.windows[0]
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            region = next(r for r in area.regions if r.type == "WINDOW")
            return window, area, region
    raise RuntimeError("No VIEW_3D area available")


def sculpt_stroke(report):
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = "BrushSculpt"
    before = [v.co.copy() for v in obj.data.vertices]
    window, area, region = find_view3d()
    with bpy.context.temp_override(window=window, area=area, region=region, active_object=obj, object=obj):
        bpy.ops.object.mode_set(mode="SCULPT")
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        space = area.spaces.active
        space.region_3d.view_distance = 3.0
        space.region_3d.view_matrix = space.region_3d.view_matrix
        x, y = region.width // 2, region.height // 2
        stroke = [
            {"name": "", "location": (0.0, -1.0, 0.0), "mouse": (x, y), "mouse_event": (x, y), "pressure": 1.0, "size": 80.0, "time": 0.0, "is_start": True, "x_tilt": 0.0, "y_tilt": 0.0},
            {"name": "", "location": (0.15, -0.98, 0.0), "mouse": (x + 18, y), "mouse_event": (x + 18, y), "pressure": 1.0, "size": 80.0, "time": 0.1, "is_start": False, "x_tilt": 0.0, "y_tilt": 0.0},
        ]
        result = bpy.ops.sculpt.brush_stroke(stroke=stroke, mode="NORMAL")
        bpy.ops.object.mode_set(mode="OBJECT")
    after = [v.co.copy() for v in obj.data.vertices]
    displacements = [(a - b).length for a, b in zip(after, before)]
    moved = sum(d > 1e-6 for d in displacements)
    report["sculpt"] = {
        "operator_result": sorted(result),
        "vertex_count": len(before),
        "moved_vertices": moved,
        "max_displacement": max(displacements),
        "mean_moved_displacement": sum(d for d in displacements if d > 1e-6) / moved if moved else 0.0,
        "pass": "FINISHED" in result and moved > 0,
    }


def create_export_asset():
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cube_add(location=(4, 0, 0))
    obj = bpy.context.object
    obj.name = "ExportSource"
    obj.scale = (1.5, 0.75, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("ExportBevel", "BEVEL")
    bevel.width = 0.12
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    mat = bpy.data.materials.new("ExportMaterial")
    mat.diffuse_color = (0.12, 0.36, 0.8, 1.0)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def round_trip_exports(report):
    source = create_export_asset()
    source_stats = mesh_stats(source)
    obj_path = OUT / "export_asset.obj"
    glb_path = OUT / "export_asset.glb"
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    obj_result = bpy.ops.wm.obj_export(filepath=str(obj_path), export_selected_objects=True, export_materials=True)
    glb_result = bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True, export_apply=True)

    source.hide_set(True)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.obj_import(filepath=str(obj_path))
    obj_imports = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    obj_stats = mesh_stats(obj_imports[0]) if len(obj_imports) == 1 else None
    for item in bpy.context.selected_objects:
        item.hide_set(True)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    glb_imports = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    glb_stats = mesh_stats(glb_imports[0]) if len(glb_imports) == 1 else None
    report["exports"] = {
        "source": source_stats,
        "obj": {"operator_result": sorted(obj_result), "file_bytes": obj_path.stat().st_size, "imported_meshes": len(obj_imports), "stats": obj_stats},
        "glb": {"operator_result": sorted(glb_result), "file_bytes": glb_path.stat().st_size, "imported_meshes": len(glb_imports), "stats": glb_stats},
    }
    for key in ("obj", "glb"):
        item = report["exports"][key]
        stats = item["stats"]
        bounds_match = stats and all(abs(a - b) <= 1e-5 for a, b in zip(stats["bounds"], source_stats["bounds"]))
        # OBJ commonly preserves polygons; glTF is triangle-based and may split vertices where
        # normals/UVs differ. Triangle surface count and world bounds are the invariant checks.
        item["pass"] = bool(
            "FINISHED" in item["operator_result"] and item["file_bytes"] > 0 and
            item["imported_meshes"] == 1 and stats and
            stats["triangles"] == source_stats["triangles"] and bounds_match and
            stats["uv_layers"] >= 1 and stats["materials"] >= 1
        )
        item["verification_basis"] = "triangulated surface count, world bounds, UV layer, material"


def main():
    report = {"lab": "interactive_sculpt_and_export_roundtrip", "blender_version": bpy.app.version_string, "failures": []}
    try:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        sculpt_stroke(report)
        round_trip_exports(report)
        report["assertions"] = {
            "actual_brush_moved_vertices": report["sculpt"]["pass"],
            "obj_roundtrip": report["exports"]["obj"]["pass"],
            "glb_roundtrip": report["exports"]["glb"]["pass"],
        }
        report["pass"] = all(report["assertions"].values())
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "sculpt_export_lab.blend"))
    except Exception as exc:
        report["failures"].append({"error": str(exc), "traceback": traceback.format_exc()})
        report["pass"] = False
    (OUT / "sculpt_export_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "DONE").write_text("done", encoding="utf-8")
    print("SCULPT_EXPORT_RESULT:" + json.dumps(report))
    bpy.ops.wm.quit_blender()


main()
