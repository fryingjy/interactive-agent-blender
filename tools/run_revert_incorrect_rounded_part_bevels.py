"""Corrective reversal, driven by direct user visual review against the reference
photos: Rose_Head, Connected_Tapered_Spout, Arched_Handle (watering can) and
Handset (telephone) were incorrectly given WEIGHT-limited Bevel treatment based
on a blanket ">25 degree dihedral" heuristic. That heuristic conflates two
different things:

1. Shading hardness -- already handled correctly by Smooth by Angle alone,
   from geometric angle, with no bevel needed.
2. Physical edge rounding/chamfer -- a real geometric operation that should
   only be applied where the reference actually shows a machined/radiused
   seam, not wherever a low-segment-count round member happens to have a
   local facet angle above a fixed threshold.

All four objects are cylindrical/tapered round forms in their reference photos
(a spray nozzle, a tapered spout, an arched handle, a bakelite handset) with
no visible hard seams. The correct treatment is Smooth by Angle alone, relying
on segment count for the rounded read, matching Connected_Vessel's own
successful strategy (real WEIGHT bevel only at genuine rim/shoulder seams,
smooth shading elsewhere). This reverts the bevel weighting on all four while
preserving their Smooth by Angle policy and everything else already correct
about them (the semantic-intent recording mechanism itself was not wrong;
applying it to the wrong edges was).
"""
import json
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from object_ops import hard_surface_shading_audit  # noqa: E402

CAN_SOURCE = ROOT / "runs/2026-08-12_watering-can-final-bevel-corrective/heldout_watering_can_production_fully_corrected.blend"
CAN_OUT = ROOT / "runs" / "2026-08-12_watering-can-rounded-parts-bevel-reverted"
CAN_TARGETS = ["Rose_Head", "Connected_Tapered_Spout", "Arched_Handle"]

TELEPHONE_SOURCE = ROOT / "runs/2026-08-12_telephone-trim-bevel-corrective/heldout_vintage_telephone_production_trim_corrected.blend"
TELEPHONE_OUT = ROOT / "runs" / "2026-08-12_telephone-handset-bevel-reverted"
TELEPHONE_TARGETS = ["Handset"]


def remove_bevel_weighting(obj_name):
    obj = bpy.data.objects[obj_name]
    for modifier in list(obj.modifiers):
        if modifier.type == "BEVEL" and modifier.limit_method == "WEIGHT":
            obj.modifiers.remove(modifier)
    attr = obj.data.attributes.get("bevel_weight_edge")
    if attr is not None:
        obj.data.attributes.remove(attr)
    obj.pop("hard_surface_intended_bevel_edge_ids", None)
    obj.data.update()


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
    }
    bm.free()
    eval_obj.to_mesh_clear()
    return health


def process(source, out_dir, targets, corrected_filename, extra_objects_for_render):
    out_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    for name in targets:
        remove_bevel_weighting(name)
    corrected_path = out_dir / corrected_filename
    bpy.ops.wm.save_as_mainfile(filepath=str(corrected_path))

    bpy.ops.wm.open_mainfile(filepath=str(corrected_path))
    health = {name: evaluated_health(name) for name in targets}
    audits = {name: hard_surface_shading_audit(name) for name in targets}

    from render_passes import render_diagnostic_pass  # local import after sys.path setup
    scene = bpy.context.scene
    scene.display.shading.light = "MATCAP"
    scene.display.shading.studio_light = "hard_surface_grey.exr"
    all_objects = [o.name for o in bpy.data.objects if o.type == "MESH"]
    for view in ("front", "isometric"):
        render_diagnostic_pass(all_objects, str(out_dir / f"reverted_{view}.png"), "matcap", view=view, resolution=768)

    report = {
        "blender_version": bpy.app.version_string,
        "source_file": str(source.relative_to(ROOT)).replace("\\", "/"),
        "reverted_objects": targets,
        "evaluated_health": health,
        "post_revert_audit_status": {name: audits[name]["status"] for name in targets},
        "all_clean": all(h["non_manifold_edges"] == 0 and h["degenerate_faces"] == 0 for h in health.values()),
    }
    (out_dir / "revert_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    can_report = process(CAN_SOURCE, CAN_OUT, CAN_TARGETS, "heldout_watering_can_production_rounded_parts_reverted.blend", None)
    print(json.dumps(can_report, indent=2))
    telephone_report = process(TELEPHONE_SOURCE, TELEPHONE_OUT, TELEPHONE_TARGETS, "heldout_vintage_telephone_production_handset_reverted.blend", None)
    print(json.dumps(telephone_report, indent=2))
    ok = can_report["all_clean"] and telephone_report["all_clean"]
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
