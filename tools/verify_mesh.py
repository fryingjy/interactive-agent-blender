"""Standalone independent mesh verifier.

Run as:
    blender --background --python tools/verify_mesh.py -- <blend_path> <object_name> [--max-ngons 0]

Add --evaluated to verify the dependency-graph result after modifiers instead
of the editable base mesh. The default remains base-mesh verification for
backward compatibility with existing evidence.

Deliberately does NOT import anything from blender_ops/ — this must stay a fresh, independent
check of a saved .blend file, sharing no code with whatever produced the mesh.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import bmesh
import bpy


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("blend_path")
    parser.add_argument("object_name")
    parser.add_argument("--max-ngons", type=int, default=0)
    parser.add_argument("--max-non-manifold", type=int, default=0)
    parser.add_argument("--report-dir", default=None)
    parser.add_argument("--evaluated", action="store_true")
    parser.add_argument("--allow-open", action="store_true", help="allow intentional boundary edges and skip closed-volume orientation")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.blend_path)

    obj = bpy.data.objects.get(args.object_name)
    if obj is None or obj.type != "MESH":
        result = {"error": f"object '{args.object_name}' not found or not a mesh"}
        print("VERIFY_RESULT:" + json.dumps(result))
        sys.exit(2)

    evaluated_obj = None
    if args.evaluated:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated_obj = obj.evaluated_get(depsgraph)
        source_mesh = evaluated_obj.to_mesh()
        source_matrix = evaluated_obj.matrix_world
    else:
        source_mesh = obj.data
        source_matrix = obj.matrix_world

    bm = bmesh.new()
    bm.from_mesh(source_mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    boundary_edges = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    invalid_non_manifold_edges = sum(1 for e in bm.edges if len(e.link_faces) not in {1, 2})
    non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    loose_verts = sum(1 for v in bm.verts if not v.link_edges)
    loose_edges = sum(1 for e in bm.edges if not e.link_faces)
    degenerate_faces = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    winding_conflicts = 0
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        directions = []
        for face in edge.link_faces:
            loop = next(loop for loop in face.loops if loop.edge == edge)
            directions.append((loop.vert.index, loop.link_loop_next.vert.index))
        if directions[0] == directions[1]:
            winding_conflicts += 1

    # Signed volume on a closed manifold mesh is positive only if normals are
    # consistently outward-facing -- a definitive check, not a heuristic.
    bm.transform(source_matrix)
    signed_volume = bm.calc_volume(signed=True)

    stats = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "non_manifold_edges": non_manifold_edges,
        "boundary_edges": boundary_edges,
        "invalid_non_manifold_edges": invalid_non_manifold_edges,
        "ngons": ngons,
        "loose_verts": loose_verts,
        "loose_edges": loose_edges,
        "degenerate_faces": degenerate_faces,
        "face_winding_conflicts": winding_conflicts,
        "signed_volume": signed_volume,
    }
    bm.free()
    if evaluated_obj is not None:
        evaluated_obj.to_mesh_clear()

    checks = {
        "non_manifold_edges_ok": invalid_non_manifold_edges == 0 if args.allow_open else non_manifold_edges <= args.max_non_manifold,
        "ngons_ok": ngons <= args.max_ngons,
        "loose_geometry_ok": loose_verts == 0 and loose_edges == 0,
        "degenerate_faces_ok": degenerate_faces == 0,
        "normals_consistent_ok": winding_conflicts == 0 and (args.allow_open or signed_volume > 0),
    }
    passed = all(checks.values())

    report = {
        "blend_path": str(Path(args.blend_path).resolve()),
        "object_name": args.object_name,
        "geometry_source": "evaluated" if args.evaluated else "base",
        "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stats": stats,
        "checks": checks,
        "clean": passed,
    }

    if args.report_dir:
        report_dir = Path(args.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        out_path = report_dir / f"{args.object_name}_{report['geometry_source']}_{ts}_{time.time_ns()}.json"
        out_path.write_text(json.dumps(report, indent=2))
        report["report_path"] = str(out_path)

    print("VERIFY_RESULT:" + json.dumps(report))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
