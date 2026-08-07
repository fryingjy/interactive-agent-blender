"""Standalone independent mesh verifier.

Run as:
    blender --background --python tools/verify_mesh.py -- <blend_path> <object_name> [--max-ngons 0]

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
    return parser.parse_args(argv)


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.blend_path)

    obj = bpy.data.objects.get(args.object_name)
    if obj is None or obj.type != "MESH":
        result = {"error": f"object '{args.object_name}' not found or not a mesh"}
        print("VERIFY_RESULT:" + json.dumps(result))
        sys.exit(2)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    loose_verts = sum(1 for v in bm.verts if not v.link_edges)
    loose_edges = sum(1 for e in bm.edges if not e.link_faces)
    degenerate_faces = sum(1 for f in bm.faces if f.calc_area() < 1e-8)

    # Signed volume on a closed manifold mesh is positive only if normals are
    # consistently outward-facing -- a definitive check, not a heuristic.
    bm.transform(obj.matrix_world)
    signed_volume = bm.calc_volume(signed=True)

    stats = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "non_manifold_edges": non_manifold_edges,
        "ngons": ngons,
        "loose_verts": loose_verts,
        "loose_edges": loose_edges,
        "degenerate_faces": degenerate_faces,
        "signed_volume": signed_volume,
    }
    bm.free()

    checks = {
        "non_manifold_edges_ok": non_manifold_edges <= args.max_non_manifold,
        "ngons_ok": ngons <= args.max_ngons,
        "loose_geometry_ok": loose_verts == 0 and loose_edges == 0,
        "degenerate_faces_ok": degenerate_faces == 0,
        "normals_consistent_ok": signed_volume > 0,
    }
    passed = all(checks.values())

    report = {
        "blend_path": str(Path(args.blend_path).resolve()),
        "object_name": args.object_name,
        "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stats": stats,
        "checks": checks,
        "clean": passed,
    }

    if args.report_dir:
        report_dir = Path(args.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        out_path = report_dir / f"{args.object_name}_{ts}.json"
        out_path.write_text(json.dumps(report, indent=2))
        report["report_path"] = str(out_path)

    print("VERIFY_RESULT:" + json.dumps(report))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
