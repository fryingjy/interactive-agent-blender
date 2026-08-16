"""Fresh-process verifier for the real-video loop-cut transfer source."""

from __future__ import annotations

import json
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-16_real-video-loopcut-review"


def component_count(obj) -> int:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    remaining = set(bm.verts)
    result = 0
    while remaining:
        result += 1
        stack = [remaining.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    bm.free()
    return result


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(RUN / "loopcut_chair_transfer.blend"))
    collection = bpy.data.collections.get("TRANSFER_LOW_POLY")
    obj = bpy.data.objects.get("LoopCutChair_ContinuousMesh")
    mesh_objects = [item for item in collection.objects if item.type == "MESH"] if collection else []
    modifier = obj.modifiers.get("Manual Bevel - Unapplied") if obj else None
    bm = bmesh.new()
    if obj:
        bm.from_mesh(obj.data)
    checks = {
        "transfer_collection_exists": collection is not None,
        "exactly_one_transfer_mesh": len(mesh_objects) == 1,
        "expected_mesh_name": obj is not None,
        "one_connected_component": obj is not None and component_count(obj) == 1,
        "all_base_faces_quads": obj is not None and all(len(face.verts) == 4 for face in bm.faces),
        "base_mesh_is_manifold": obj is not None and all(edge.is_manifold for edge in bm.edges),
        "live_unapplied_bevel_exists": modifier is not None and modifier.show_viewport and modifier.show_render,
        "no_modifier_apply_call_in_builder": "bpy.ops.object.modifier_apply" not in (ROOT / "tools" / "run_loopcut_chair_transfer.py").read_text(encoding="utf-8"),
    }
    bm.free()
    result = {"pass": all(checks.values()), "checks": checks}
    (RUN / "fresh_transfer_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
