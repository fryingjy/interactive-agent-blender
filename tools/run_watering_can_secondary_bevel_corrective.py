"""Corrective pass: the watering-can spout and handle were identified by
run_no_bevel_dihedral_triage.py as primary structural components with real
sharp edges (up to 92 degrees) and zero bevel treatment -- only the vessel
had a WEIGHT-limited Bevel. This adds the same semantic-weight/WEIGHT-Bevel/
Smooth-by-Angle policy to Connected_Tapered_Spout and Arched_Handle.

The original production file is left untouched. This writes a new file in
its own run directory, matching the established "preserve prior evidence,
build a corrective on top" pattern used for the connected-camera correction.
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

SOURCE = ROOT / "runs/2026-08-11_heldout-watering-can/production/heldout_watering_can_production.blend"
OUT = ROOT / "runs" / "2026-08-12_watering-can-secondary-bevel-corrective"
ALL_OBJECTS = [
    "Connected_Vessel", "Connected_Tapered_Spout", "Arched_Handle",
    "Opening_Rim", "Opening_Shadow", "Rose_Head", "WateringCan_Baked_Badge",
]

SHARP_THRESHOLD_DEG = 25.0
CANDIDATE_WIDTHS = {
    "Connected_Tapered_Spout": [0.015, 0.010, 0.006],
    "Arched_Handle": [0.010, 0.006, 0.004],
}


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


def evaluate_bevel_only(obj):
    """Temporarily disable every other modifier, evaluate, check manifoldness,
    then restore. Returns (non_manifold_count, degenerate_count)."""
    saved_show = {m.name: m.show_viewport for m in obj.modifiers}
    for m in obj.modifiers:
        m.show_viewport = m.type == "BEVEL"
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    bm.free()
    eval_obj.to_mesh_clear()
    for m in obj.modifiers:
        m.show_viewport = saved_show[m.name]
    return non_manifold, degenerate


def apply_policy(obj_name):
    obj = bpy.data.objects[obj_name]
    weighted = sharp_edge_ids(obj)
    result = {"name": obj_name, "sharp_edge_count": len(weighted), "attempts": []}
    accepted_width = None
    for width in CANDIDATE_WIDTHS[obj_name]:
        set_bevel_weight_by_ids(obj_name, weighted, weight=1.0, clear_others=True)
        existing = [m for m in obj.modifiers if m.type == "BEVEL"]
        bevel = existing[0] if existing else obj.modifiers.new("Semantic weighted edge radius", "BEVEL")
        bevel.limit_method = "WEIGHT"
        bevel.width = width
        bevel.segments = 2
        non_manifold, degenerate = evaluate_bevel_only(obj)
        result["attempts"].append({"width": width, "evaluated_non_manifold_edges": non_manifold, "evaluated_degenerate_faces": degenerate})
        if non_manifold == 0 and degenerate == 0:
            accepted_width = width
            break
        obj.modifiers.remove(bevel)
    result["accepted_width"] = accepted_width
    if accepted_width is None:
        result["status"] = "REJECTED_ALL_WIDTHS_UNSAFE"
        return result
    set_smooth_by_angle(obj_name, angle=0.5235987756, keep_sharp_edges=True)
    result["status"] = "APPLIED"
    return result


def render_matcap_pair(before_path, after_path):
    OUT.mkdir(parents=True, exist_ok=True)
    for label, path in (("before", before_path), ("after", after_path)):
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        scene.display.shading.light = "MATCAP"
        scene.display.shading.studio_light = "hard_surface_grey.exr"
        for view in ("front", "isometric"):
            render_diagnostic_pass(
                ALL_OBJECTS, str(OUT / f"matcap_{label}_{view}.png"), "matcap", view=view, resolution=768,
            )


def evaluated_health(obj_name):
    obj = bpy.data.objects[obj_name]
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
        "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
        "ngons": sum(1 for f in bm.faces if len(f.verts) > 4),
    }
    bm.free()
    eval_obj.to_mesh_clear()
    return health


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    results = {}
    for name in ("Connected_Tapered_Spout", "Arched_Handle"):
        results[name] = apply_policy(name)

    OUT.mkdir(parents=True, exist_ok=True)
    corrected_path = OUT / "heldout_watering_can_production_corrected.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(corrected_path))

    # Reopen the saved file rather than trusting in-memory state: the audit and
    # evaluated-mesh checks below run against exactly what was written to disk.
    bpy.ops.wm.open_mainfile(filepath=str(corrected_path))
    audits = {name: hard_surface_shading_audit(name) for name in results if results[name]["status"] == "APPLIED"}
    evaluated = {name: evaluated_health(name) for name in ("Connected_Vessel", "Connected_Tapered_Spout", "Arched_Handle")}
    render_matcap_pair(SOURCE, corrected_path)
    report = {
        "blender_version": bpy.app.version_string,
        "source_file": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "results": results,
        "evaluated_health": evaluated,
        "post_correction_audit": audits,
        "all_applied": all(r["status"] == "APPLIED" for r in results.values()),
    }
    (OUT / "correction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["all_applied"] else 2)


if __name__ == "__main__":
    main()
