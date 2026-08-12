"""Corrective pass for the 11 boombox objects the no-Bevel triage found have
real sharp edges (58-139 degree max dihedral) and zero bevel treatment: four
cassette reels, four fascia fasteners, two speaker cones, and the telescoping
antenna. None of these carry any existing modifier, so unlike the telephone
handset there is no stack-order concern -- the new Bevel is simply appended.

The original production file is left untouched; this writes a new file in
its own run directory, matching the watering-can/telephone corrective
pattern.
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

SOURCE = ROOT / "runs/2026-08-11_heldout-boombox/final/heldout_boombox.blend"
OUT = ROOT / "runs" / "2026-08-12_boombox-secondary-bevel-corrective"
SHARP_THRESHOLD_DEG = 25.0

# Candidate widths sized from each object's own dimensions (see the dihedral
# triage / dimension inspection recorded in this run's session report),
# tried most-generous-first and narrowed only if evaluation is unsafe.
CANDIDATE_WIDTHS = {
    "Cassette reel": [0.008, 0.005, 0.003],
    "Cassette reel.001": [0.008, 0.005, 0.003],
    "Cassette reel.002": [0.008, 0.005, 0.003],
    "Cassette reel.003": [0.008, 0.005, 0.003],
    "Fascia fastener": [0.005, 0.003, 0.002],
    "Fascia fastener.001": [0.005, 0.003, 0.002],
    "Fascia fastener.002": [0.005, 0.003, 0.002],
    "Fascia fastener.003": [0.005, 0.003, 0.002],
    "Speaker cone L": [0.015, 0.010, 0.006],
    "Speaker cone R": [0.015, 0.010, 0.006],
    "Telescoping antenna": [0.006, 0.004, 0.003],
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
        # A whole-scene view makes these small parts nearly invisible; the speaker
        # cone's rim profile edge-on is the clearest single before/after specimen.
        render_diagnostic_pass(
            ["Speaker cone L"], str(OUT / f"speaker_cone_rim_profile_{label}.png"), "matcap", view="side", resolution=900, margin=1.05,
        )


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    results = {name: apply_policy(name) for name in CANDIDATE_WIDTHS}

    OUT.mkdir(parents=True, exist_ok=True)
    corrected_path = OUT / "heldout_boombox_corrected.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(corrected_path))

    bpy.ops.wm.open_mainfile(filepath=str(corrected_path))
    audits = {name: hard_surface_shading_audit(name) for name, r in results.items() if r["status"] == "APPLIED"}

    render_matcap_pair(SOURCE, corrected_path)

    report = {
        "blender_version": bpy.app.version_string,
        "source_file": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "results": results,
        "post_correction_audit": audits,
        "all_applied": all(r["status"] == "APPLIED" for r in results.values()),
        "all_pass_audit": all(a["status"] == "PASS" for a in audits.values()),
    }
    (OUT / "correction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("post_correction_audit",)}, indent=2))
    raise SystemExit(0 if report["all_applied"] and report["all_pass_audit"] else 2)


if __name__ == "__main__":
    main()
