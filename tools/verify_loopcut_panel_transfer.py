"""Fresh-process verifier for the different-geometry loop-cut transfer."""

from __future__ import annotations

import json
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-16_real-video-loopcut-review"


def components(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data); unseen = set(bm.verts); count = 0
    while unseen:
        count += 1; stack = [unseen.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen: unseen.remove(other); stack.append(other)
    bm.free(); return count


def main():
    bpy.ops.wm.open_mainfile(filepath=str(RUN / "loopcut_control_panel_transfer.blend"))
    collection = bpy.data.collections.get("TRANSFER_DIFFERENT_GEOMETRY")
    obj = bpy.data.objects.get("LoopCutControlPanel_ContinuousMesh")
    bm = bmesh.new()
    if obj: bm.from_mesh(obj.data)
    bevel = obj.modifiers.get("Manual Bevel - Unapplied") if obj else None
    builder = (ROOT / "tools" / "run_loopcut_panel_transfer.py").read_text(encoding="utf-8")
    checks = {
        "named_collection_exists": collection is not None,
        "one_mesh_in_collection": collection is not None and len([item for item in collection.objects if item.type == "MESH"]) == 1,
        "one_continuous_mesh": obj is not None and components(obj) == 1,
        "all_base_faces_quads": obj is not None and all(len(face.verts) == 4 for face in bm.faces),
        "base_mesh_is_manifold": obj is not None and all(edge.is_manifold for edge in bm.edges),
        "live_unapplied_bevel": bevel is not None and bevel.show_viewport and bevel.show_render,
        "builder_never_applies_modifier": "bpy.ops.object.modifier_apply" not in builder,
    }
    bm.free(); result = {"pass": all(checks.values()), "checks": checks}
    (RUN / "fresh_panel_transfer_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2)); raise SystemExit(0 if result["pass"] else 1)

if __name__ == "__main__": main()
