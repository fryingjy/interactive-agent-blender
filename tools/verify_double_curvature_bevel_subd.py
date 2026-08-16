"""Fresh-process verification for the double-curvature Bevel/SubD evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def health(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def base_health(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    remaining = set(bm.verts)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    result = {
        "components": components,
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
    }
    bm.free()
    return result


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected RUN_DIR after --")
    run_dir = Path(args[0]).resolve()
    generator = json.loads((run_dir / "double_curvature_bevel_subd_report.json").read_text(encoding="utf-8"))
    names = [f"{family}_{case}" for family in ("CROWN", "SADDLE") for case in ("COMPLETE", "INCOMPLETE")]
    objects = {name: bpy.data.objects.get(name) for name in names}
    records = {}
    for name, obj in objects.items():
        attr = obj.data.attributes.get("bevel_weight_edge") if obj else None
        weighted = sum(item.value > 0.999 for item in attr.data) if attr else 0
        intended = list(obj.get("hard_surface_intended_bevel_edge_ids", [])) if obj else []
        records[name] = {
            "base_vertices": len(obj.data.vertices) if obj else None,
            "base_faces": len(obj.data.polygons) if obj else None,
            "base_non_quads": sum(len(face.vertices) != 4 for face in obj.data.polygons) if obj else None,
            "base_health": base_health(obj) if obj else None,
            "modifier_types": [modifier.type for modifier in obj.modifiers] if obj else None,
            "intent_source": obj.get("hard_surface_bevel_intent_source") if obj else None,
            "intended_count": len(intended),
            "weighted_count": weighted,
            "health": health(obj) if obj else None,
        }
    render_names = generator.get("renders", [])
    checks = {
        "generator_report_passed": generator.get("pass") is True,
        "all_four_objects_exist": all(objects.values()),
        "all_base_cages_are_98_vertex_96_quad": all(
            item["base_vertices"] == 98 and item["base_faces"] == 96 and item["base_non_quads"] == 0
            and item["base_health"]["components"] == 1
            and item["base_health"]["non_manifold_edges"] == 0
            and item["base_health"]["degenerate_faces"] == 0
            for item in records.values()
        ),
        "all_intent_sources_remain_explicit": all(item["intent_source"] == "EXPLICIT_DECLARATION" for item in records.values()),
        "complete_maps_cover_all_declared_edges": all(
            records[f"{family}_COMPLETE"]["weighted_count"] == records[f"{family}_COMPLETE"]["intended_count"] == 48
            for family in ("CROWN", "SADDLE")
        ),
        "incomplete_maps_retain_eight_detectable_omissions": all(
            records[f"{family}_INCOMPLETE"]["intended_count"] == 48
            and records[f"{family}_INCOMPLETE"]["weighted_count"] == 40
            for family in ("CROWN", "SADDLE")
        ),
        "bevel_precedes_subd_in_saved_stacks": all(item["modifier_types"][:2] == ["BEVEL", "SUBSURF"] for item in records.values()),
        "all_saved_evaluated_meshes_are_clean_quads": all(
            item["health"]["non_manifold_edges"] == 0
            and item["health"]["degenerate_faces"] == 0
            and item["health"]["ngons"] == 0
            for item in records.values()
        ),
        "all_render_evidence_is_retained": len(render_names) == 6 and all((run_dir / name).is_file() and (run_dir / name).stat().st_size > 0 for name in render_names),
        "temporary_wire_objects_not_saved": not any(obj.name.endswith("_EvidenceWire") for obj in bpy.data.objects),
        "no_applied_duplicate_meshes_saved": len([obj for obj in bpy.data.objects if obj.type == "MESH"]) == 4,
    }
    report = {
        "lab": "independent_double_curvature_bevel_subd_verification",
        "blender_version": bpy.app.version_string,
        "records": records,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": generator.get("claim_boundary"),
    }
    (run_dir / "fresh_verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("DOUBLE_CURVATURE_BEVEL_SUBD_VERIFY:" + json.dumps({"pass": report["pass"], "checks": checks}))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
