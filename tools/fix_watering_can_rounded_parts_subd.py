"""Correction (found on direct user review, 2026-08-13): Rose_Head,
Connected_Tapered_Spout, and Arched_Handle were reverted earlier
(runs/2026-08-12_watering-can-rounded-parts-bevel-reverted/) to remove an
incorrect WEIGHT Bevel that made them read as faceted -- but the revert only
removed the wrong fix, it never checked whether the underlying cage actually
had enough geometry to read as round in the first place. It doesn't: 56/80/116
verts respectively, zero modifiers. Smooth shading alone cannot make a
low-segment cage look round; it needs a real Subdivision Surface modifier (or
more base geometry). Confirmed live: user circled the spray-head knob in the
field report and pointed out it is still visibly a faceted hex shape, and that
no Subdivision modifier appears to have been used at all.

Fix: add a Subdivision Surface modifier (levels=2) to each of the three parts,
verify the evaluated mesh is still clean, no bevel weight touched (per the
user's explicit note that nothing in that area should be bevel weighted).
Edits the file in place -- same scene, no new version.
"""
import sys
from pathlib import Path

import bmesh
import bpy

BLEND = Path(sys.argv[sys.argv.index("--") + 1])
TARGETS = ["Rose_Head", "Connected_Tapered_Spout", "Arched_Handle"]


def evaluated_health(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(eval_mesh)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    verts, faces = len(bm.verts), len(bm.faces)
    bm.free()
    eval_obj.to_mesh_clear()
    return {"non_manifold_edges": non_manifold, "degenerate_faces": degenerate,
            "ngons": ngons, "evaluated_verts": verts, "evaluated_faces": faces}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    report = {}
    for name in TARGETS:
        obj = bpy.data.objects[name]
        before = {"base_verts": len(obj.data.vertices), "base_faces": len(obj.data.polygons)}
        existing = [m for m in obj.modifiers if m.type == "SUBSURF"]
        subd = existing[0] if existing else obj.modifiers.new("Controlled Catmull-Clark surface", "SUBSURF")
        subd.levels = 2
        subd.render_levels = 2
        subd.show_viewport = True
        subd.show_render = True
        health = evaluated_health(obj)
        report[name] = {**before, "subd_added": existing == [], **health}
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    import json
    print("SUBD_FIX_RESULT:" + json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
