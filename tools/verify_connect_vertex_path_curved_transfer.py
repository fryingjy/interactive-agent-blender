"""Fresh-process verifier for curved/SubD Connect Vertex Path transfer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def topology(obj, evaluated=False):
    if evaluated:
        source = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = source.to_mesh()
    else:
        mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "faces": len(bm.faces),
        "face_sizes": sorted(len(face.verts) for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "non_manifold_nonboundary_edges": sum(not edge.is_manifold and not edge.is_boundary for edge in bm.edges),
    }
    bm.free()
    if evaluated:
        source.to_mesh_clear()
    return result


def ids_ok(obj):
    return all(
        (attribute := obj.data.attributes.get(name)) is not None
        and len(attribute.data) == expected
        and all(int(item.value) > 0 for item in attribute.data)
        and len({int(item.value) for item in attribute.data}) == expected
        for name, expected in (("agent_vertex_id", len(obj.data.vertices)), ("agent_edge_id", len(obj.data.edges)), ("agent_face_id", len(obj.data.polygons)))
    )


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected RUN_DIR after --")
    run_dir = Path(args[0]).resolve()
    generator = json.loads((run_dir / "connect_vertex_path_curved_transfer_report.json").read_text(encoding="utf-8"))
    names = ("Crown_Hex_Repair", "Twisted_Hex_Repair", "Curved_Strip_Diagonal_Control")
    objects = {name: bpy.data.objects.get(name) for name in names}
    base = {name: topology(obj) if obj else None for name, obj in objects.items()}
    evaluated = {name: topology(obj, evaluated=True) if obj else None for name, obj in objects.items()}
    checks = {
        "generator_report_passed": generator.get("pass") is True,
        "all_objects_saved": all(objects.values()),
        "curved_hex_base_repairs_are_all_quad": all(base[name]["face_sizes"] == [4, 4] for name in names[:2]),
        "curved_hex_evaluated_results_are_clean": all(
            evaluated[name]["triangles"] == 0 and evaluated[name]["ngons"] == 0
            and evaluated[name]["degenerate_faces"] == 0 and evaluated[name]["non_manifold_nonboundary_edges"] == 0
            for name in names[:2]
        ),
        "live_subdivision_stacks_persist": all([modifier.type for modifier in obj.modifiers] == ["SUBSURF"] for obj in objects.values()),
        "strict_rejection_control_is_unchanged": base[names[2]]["face_sizes"] == [4, 4, 4],
        "persistent_ids_reconciled_after_repairs": all(ids_ok(obj) for obj in objects.values()),
        "render_evidence_retained": all((run_dir / name).is_file() and (run_dir / name).stat().st_size > 0 for name in generator["renders"]),
        "temporary_wire_objects_not_saved": not any(obj.name.endswith("_EvidenceWire") for obj in bpy.data.objects),
    }
    report = {"lab": "fresh_connect_vertex_path_curved_subd_transfer", "blender_version": bpy.app.version_string, "base": base, "evaluated": evaluated, "checks": checks, "pass": all(checks.values()), "claim_boundary": generator["claim_boundary"]}
    (run_dir / "fresh_verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CONNECT_VERTEX_PATH_CURVED_VERIFY:" + json.dumps({"pass": report["pass"], "checks": checks}))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
