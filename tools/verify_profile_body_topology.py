"""Fresh-process topology check for a continuous all-quad profile body."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("expected BLEND OBJECT REPORT after --")
    blend_path, object_name, report_path = Path(args[0]).resolve(), args[1], Path(args[2]).resolve()
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    obj = bpy.data.objects.get(object_name)
    if obj is None or obj.type != "MESH":
        raise SystemExit(f"missing mesh object: {object_name}")
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    islands = 0
    remaining = set(bm.verts)
    while remaining:
        islands += 1
        stack = [remaining.pop()]
        while stack:
            vert = stack.pop()
            for edge in vert.link_edges:
                neighbor = edge.other_vert(vert)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    report = {
        "blend": str(blend_path),
        "object": object_name,
        "geometry_source": "fresh-process base cage",
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "quad_faces": sum(len(face.verts) == 4 for face in bm.faces),
        "non_quad_faces": sum(len(face.verts) != 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "connected_components": islands,
    }
    report["pass"] = report["non_quad_faces"] == 0 and report["non_manifold_edges"] == 0 and islands == 1
    bm.free()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PROFILE_TOPOLOGY_RESULT:" + json.dumps(report))
    raise SystemExit(0 if report["pass"] else 1)


main()
