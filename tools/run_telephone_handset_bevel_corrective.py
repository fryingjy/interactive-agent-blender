"""Corrective pass: the vintage telephone's Handset was identified by
run_no_bevel_dihedral_triage.py as a primary structural component (its own
session report calls it "one closed connected 162-quad longitudinal skin,"
on par with the housing) with real sharp edges (up to 71.82 degrees) and
zero bevel treatment -- only Main_Housing had a WEIGHT-limited Bevel.

Unlike the watering-can spout/handle, Handset already has a Subdivision
modifier with no Bevel before it, so the new Bevel must be inserted at the
correct stack position, not simply appended.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
import persistent_ids  # noqa: E402
from object_ops import hard_surface_shading_audit, set_bevel_weight_by_ids, set_smooth_by_angle  # noqa: E402
from render_passes import render_diagnostic_pass  # noqa: E402

SOURCE = ROOT / "runs/2026-08-11_heldout-vintage-telephone/production/heldout_vintage_telephone_production.blend"
OUT = ROOT / "runs" / "2026-08-12_telephone-handset-bevel-corrective"
TARGET = "Handset"
CANDIDATE_WIDTHS = [0.015, 0.010, 0.006]
SHARP_THRESHOLD_DEG = 25.0

ALL_OBJECTS = None  # filled from the scene at render time


def sharp_edge_ids(obj):
    persistent_ids.ensure_persistent_ids(obj.name)
    index_to_id = persistent_ids.get_id_maps(obj.name)["edges"]["index_to_id"]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    sharp = []
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        try:
            angle_deg = math.degrees(edge.calc_face_angle())
        except Exception:
            continue
        if angle_deg > SHARP_THRESHOLD_DEG and edge.index in index_to_id:
            sharp.append(int(index_to_id[edge.index]))
    bm.free()
    return sorted(sharp)


def evaluated_health(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    health = {
        "evaluated_vertices": len(bm.verts),
        "evaluated_faces": len(bm.faces),
        "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
        "degenerate_faces": sum(1 for f in bm.faces if f.calc_area() < 1e-8),
    }
    bm.free()
    eval_obj.to_mesh_clear()
    return health


def apply_policy(obj_name):
    obj = bpy.data.objects[obj_name]
    weighted = sharp_edge_ids(obj)
    result = {"name": obj_name, "sharp_edge_count": len(weighted), "attempts": []}
    subd_index = next((i for i, m in enumerate(obj.modifiers) if m.type == "SUBSURF"), None)
    accepted_width = None
    for width in CANDIDATE_WIDTHS:
        set_bevel_weight_by_ids(obj_name, weighted, weight=1.0, clear_others=True)
        existing = [m for m in obj.modifiers if m.type == "BEVEL"]
        if existing:
            bevel = existing[0]
        else:
            bevel = obj.modifiers.new("Semantic weighted edge radius", "BEVEL")
            bevel_index = len(obj.modifiers) - 1
            if subd_index is not None and bevel_index > subd_index:
                obj.modifiers.move(bevel_index, subd_index)
        bevel.limit_method = "WEIGHT"
        bevel.width = width
        bevel.segments = 2
        health = evaluated_health(obj)
        result["attempts"].append({"width": width, **health})
        if health["non_manifold_edges"] == 0 and health["degenerate_faces"] == 0:
            accepted_width = width
            break
        obj.modifiers.remove(bevel)
    result["accepted_width"] = accepted_width
    if accepted_width is None:
        result["status"] = "REJECTED_ALL_WIDTHS_UNSAFE"
        return result
    result["modifier_order_after"] = [m.type for m in obj.modifiers]
    set_smooth_by_angle(obj_name, angle=0.5235987756, keep_sharp_edges=True)
    result["status"] = "APPLIED"
    return result


def render_matcap_pair(before_path, after_path):
    OUT.mkdir(parents=True, exist_ok=True)
    for label, path in (("before", before_path), ("after", after_path)):
        bpy.ops.wm.open_mainfile(filepath=str(path))
        all_objects = [o.name for o in bpy.data.objects if o.type == "MESH"]
        scene = bpy.context.scene
        scene.display.shading.light = "MATCAP"
        scene.display.shading.studio_light = "hard_surface_grey.exr"
        for view in ("front", "isometric"):
            render_diagnostic_pass(
                all_objects, str(OUT / f"matcap_{label}_{view}.png"), "matcap", view=view, resolution=768,
            )


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    result = apply_policy(TARGET)

    OUT.mkdir(parents=True, exist_ok=True)
    corrected_path = OUT / "heldout_vintage_telephone_production_corrected.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(corrected_path))

    bpy.ops.wm.open_mainfile(filepath=str(corrected_path))
    audit = hard_surface_shading_audit(TARGET) if result["status"] == "APPLIED" else None
    housing_audit_unchanged = "WEIGHT" in hard_surface_shading_audit("Main_Housing")["bevel_limit_methods_present"]

    render_matcap_pair(SOURCE, corrected_path)

    report = {
        "blender_version": bpy.app.version_string,
        "source_file": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "result": result,
        "post_correction_audit": audit,
        "housing_weight_bevel_undisturbed": housing_audit_unchanged,
    }
    (OUT / "correction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if result["status"] == "APPLIED" and housing_audit_unchanged else 2)


if __name__ == "__main__":
    main()
