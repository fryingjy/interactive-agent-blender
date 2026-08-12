"""Corrective pass for the vintage telephone's remaining untreated trim: the
clock face, both panel trim strips, and 12 dial apertures. All 15 have real
sharp edges (per the no-Bevel dihedral triage) and zero bevel treatment,
identical construction pattern to the boombox's 11 corrected parts -- none
carry any existing modifier.

Closes the last item from the no-Bevel triage's remaining-work list.
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

# Builds on the already-corrected handset file, not the original production
# file, so this output cumulatively carries both fixes instead of the trim
# fix alone reverting the handset back to untreated.
SOURCE = ROOT / "runs/2026-08-12_telephone-handset-bevel-corrective/heldout_vintage_telephone_production_corrected.blend"
ORIGINAL_PUBLISHED = ROOT / "runs/2026-08-11_heldout-vintage-telephone/production/heldout_vintage_telephone_production.blend"
OUT = ROOT / "runs" / "2026-08-12_telephone-trim-bevel-corrective"
SHARP_THRESHOLD_DEG = 25.0

DIAL_APERTURES = ["Dial_Aperture"] + [f"Dial_Aperture_{i:02d}" for i in range(1, 12)]
CANDIDATE_WIDTHS = {
    "Clock_Face": [0.010, 0.006, 0.004],
    "Lower_Panel_Trim": [0.010, 0.006, 0.004],
    "Upper_Face_Trim": [0.015, 0.010, 0.006],
}
for _name in DIAL_APERTURES:
    CANDIDATE_WIDTHS[_name] = [0.006, 0.004, 0.003]


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


def winding_inconsistent_edge_count(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    inconsistent = 0
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        f1, f2 = edge.link_faces
        loop1 = next(l for l in f1.loops if l.edge == edge)
        loop2 = next(l for l in f2.loops if l.edge == edge)
        if loop1.vert == loop2.vert:
            inconsistent += 1
    bm.free()
    return inconsistent


def recalculate_normals_outside(obj):
    """Blender's "Recalculate Outside" equivalent: normalizes face winding so
    a topologically-manifold-but-normal-inconsistent mesh (which reports 0
    non-manifold edges at the base level, yet still makes Bevel produce
    non-manifold results at every width) becomes actually consistent."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def apply_policy(obj_name):
    obj = bpy.data.objects[obj_name]
    before_inconsistent = winding_inconsistent_edge_count(obj)
    if before_inconsistent:
        recalculate_normals_outside(obj)
    after_inconsistent = winding_inconsistent_edge_count(obj)
    weighted = sharp_edge_ids(obj)
    result = {
        "name": obj_name,
        "sharp_edge_count": len(weighted),
        "winding_inconsistent_edges_before": before_inconsistent,
        "winding_inconsistent_edges_after_repair": after_inconsistent,
        "attempts": [],
    }
    accepted_width = None
    for width in CANDIDATE_WIDTHS[obj_name]:
        set_bevel_weight_by_ids(obj_name, weighted, weight=1.0, clear_others=True)
        existing = [m for m in obj.modifiers if m.type == "BEVEL"]
        bevel = existing[0] if existing else obj.modifiers.new("Semantic weighted edge radius", "BEVEL")
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
        # A whole-scene/front render makes these small parts' rim bevels nearly
        # invisible (edge-on to the camera); isolate one edge-on side profile.
        render_diagnostic_pass(
            ["Clock_Face"], str(OUT / f"clock_face_rim_profile_{label}.png"), "matcap", view="side", resolution=900, margin=1.05,
        )


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    targets = list(CANDIDATE_WIDTHS.keys())
    results = {name: apply_policy(name) for name in targets}

    OUT.mkdir(parents=True, exist_ok=True)
    corrected_path = OUT / "heldout_vintage_telephone_production_trim_corrected.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(corrected_path))

    bpy.ops.wm.open_mainfile(filepath=str(corrected_path))
    audits = {name: hard_surface_shading_audit(name) for name, r in results.items() if r["status"] == "APPLIED"}
    housing_undisturbed = "WEIGHT" in hard_surface_shading_audit("Main_Housing")["bevel_limit_methods_present"]
    handset_undisturbed = hard_surface_shading_audit("Handset")["status"] == "PASS"

    render_matcap_pair(SOURCE, corrected_path)

    report = {
        "blender_version": bpy.app.version_string,
        "source_file": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "original_published_file": str(ORIGINAL_PUBLISHED.relative_to(ROOT)).replace("\\", "/"),
        "results": results,
        "post_correction_audit": audits,
        "all_applied": all(r["status"] == "APPLIED" for r in results.values()),
        "all_pass_audit": all(a["status"] == "PASS" for a in audits.values()),
        "housing_weight_bevel_undisturbed": housing_undisturbed,
        "handset_correction_undisturbed": handset_undisturbed,
    }
    (OUT / "correction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "post_correction_audit"}, indent=2))
    raise SystemExit(0 if report["all_applied"] and report["all_pass_audit"] and housing_undisturbed and handset_undisturbed else 2)


if __name__ == "__main__":
    main()
