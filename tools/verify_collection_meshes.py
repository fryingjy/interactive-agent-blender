"""Fresh-process verification of every mesh in one saved Blender collection.

Run:
    blender --background --factory-startup --python-exit-code 1 \
      --python tools/verify_collection_meshes.py -- FILE.blend COLLECTION REPORT.json

This script intentionally imports no project modeling code.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def args():
    argv = sys.argv
    if "--" not in argv or len(argv[argv.index("--") + 1 :]) != 3:
        raise SystemExit("expected FILE.blend COLLECTION REPORT.json after --")
    blend, collection, report = argv[argv.index("--") + 1 :]
    return Path(blend).resolve(), collection, Path(report).resolve()


def inspect(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.transform(evaluated.matrix_world)
    stats = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "loose_vertices": sum(not vert.link_edges for vert in bm.verts),
        "loose_edges": sum(not edge.link_faces for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
        "signed_volume": bm.calc_volume(signed=True),
        "uv_layers": len(mesh.uv_layers),
    }
    bm.free()
    evaluated.to_mesh_clear()
    checks = {
        "closed_manifold": stats["non_manifold_edges"] == 0,
        "no_ngons": stats["ngons"] == 0,
        "no_loose_geometry": stats["loose_vertices"] == 0 and stats["loose_edges"] == 0,
        "no_degenerate_faces": stats["degenerate_faces"] == 0,
        "outward_positive_volume": stats["signed_volume"] > 0,
        "has_uv": stats["uv_layers"] > 0,
    }
    return {"name": obj.name, "stats": stats, "checks": checks, "clean": all(checks.values())}


def main():
    blend_path, collection_name, report_path = args()
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        raise SystemExit(f"missing collection: {collection_name}")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = [inspect(obj, depsgraph) for obj in collection.all_objects if obj.type == "MESH"]
    report = {
        "blend_path": str(blend_path),
        "collection": collection_name,
        "geometry_source": "fresh-process evaluated dependency graph",
        "objects": objects,
        "summary": {
            "mesh_objects": len(objects),
            "clean_objects": sum(item["clean"] for item in objects),
            "all_clean": bool(objects) and all(item["clean"] for item in objects),
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("COLLECTION_VERIFY_RESULT:" + json.dumps(report))
    raise SystemExit(0 if report["summary"]["all_clean"] else 1)


main()
