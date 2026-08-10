"""Modeler-relevant BMesh API state and operator lab."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy


def output_directory():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected one OUTPUT_DIR after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_object(name, bm, location):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def counts(bm):
    return {"vertices": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces)}


def main():
    output = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    records = []

    bm = bmesh.new()
    verts = [bm.verts.new(co) for co in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 0))]
    bm.faces.new((verts[0], verts[1], verts[2]))
    before = counts(bm)
    result = bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    after = counts(bm)
    records.append({"case": "remove_doubles", "before": before, "after": after, "return_type": type(result).__name__, "targetmap_size": len(result.get("targetmap", {})) if isinstance(result, dict) else None})
    store_object("BMesh_RemoveDoubles", bm, (-6, 3, 0))
    bm.free()

    bm = bmesh.new()
    a, b, c = [bm.verts.new(co) for co in ((0, 0, 0), (1e-7, 0, 0), (0, 1, 0))]
    bm.faces.new((a, b, c))
    before = counts(bm)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    after = counts(bm)
    records.append({"case": "dissolve_degenerate", "before": before, "after": after})
    store_object("BMesh_DissolveDegenerate", bm, (-3, 3, 0))
    bm.free()

    bm = bmesh.new()
    ring = [bm.verts.new((math.cos(i * math.pi / 3), math.sin(i * math.pi / 3), 0)) for i in range(6)]
    face = bm.faces.new(ring)
    result = bmesh.ops.triangulate(bm, faces=[face], quad_method="BEAUTY", ngon_method="BEAUTY")
    records.append({"case": "triangulate_ngon", "after": counts(bm), "returned_faces": len(result.get("faces", [])), "face_map_size": len(result.get("face_map", {}))})
    store_object("BMesh_Triangulate", bm, (0, 3, 0))
    bm.free()

    bm = bmesh.new()
    v0, v1, v2, v3 = [bm.verts.new(co) for co in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0))]
    bm.faces.new((v0, v1, v2))
    bm.faces.new((v0, v2, v3))
    before = counts(bm)
    shared_diagonal = bm.edges.get((v0, v2))
    result = bmesh.ops.dissolve_limit(bm, angle_limit=1e-5, use_dissolve_boundaries=True, verts=bm.verts[:], edges=bm.edges[:], delimit=set())
    after = counts(bm)
    records.append({"case": "dissolve_limit_broad_boundary_failure", "before": before, "after": after, "region_size": len(result.get("region", []))})
    store_object("BMesh_DissolveLimit", bm, (3, 3, 0))
    bm.free()

    bm = bmesh.new()
    v0, v1, v2, v3 = [bm.verts.new(co) for co in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0))]
    bm.faces.new((v0, v1, v2))
    bm.faces.new((v0, v2, v3))
    shared_diagonal = bm.edges.get((v0, v2))
    before = counts(bm)
    result = bmesh.ops.dissolve_edges(bm, edges=[shared_diagonal], use_verts=False)
    after = counts(bm)
    records.append({"case": "dissolve_shared_edge", "before": before, "after": after, "region_size": len(result.get("region", [])) if isinstance(result, dict) else None})
    store_object("BMesh_DissolveSharedEdge", bm, (4.5, 3, 0))
    bm.free()

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    for face in bm.faces:
        face.normal_flip()
    volume_before = bm.calc_volume(signed=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    volume_after = bm.calc_volume(signed=True)
    records.append({"case": "recalc_face_normals", "signed_volume_before": volume_before, "signed_volume_after": volume_after})
    store_object("BMesh_RecalculateNormals", bm, (6, 3, 0))
    bm.free()

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    uv_layer = bm.loops.layers.uv.new("LabUV")
    written = 0
    for face in bm.faces:
        for loop in face.loops:
            loop[uv_layer].uv = (loop.vert.co.x * 0.25 + 0.5, loop.vert.co.y * 0.25 + 0.5)
            written += 1
    obj = store_object("BMesh_UVCustomData", bm, (-3, -2, 0))
    layer = obj.data.uv_layers.get("LabUV")
    nonzero = sum(abs(item.uv.x) > 1e-8 or abs(item.uv.y) > 1e-8 for item in layer.data)
    records.append({"case": "uv_custom_data_roundtrip", "loops_written": written, "loops_nonzero_after_to_mesh": nonzero})
    bm.free()

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.faces.ensure_lookup_table()
    face = bm.faces[0]
    face.select = True
    selected_before = {"verts": sum(v.select for v in bm.verts), "edges": sum(e.select for e in bm.edges), "faces": sum(f.select for f in bm.faces)}
    bm.select_flush(True)
    selected_after = {"verts": sum(v.select for v in bm.verts), "edges": sum(e.select for e in bm.edges), "faces": sum(f.select for f in bm.faces)}
    records.append({"case": "selection_flush", "before": selected_before, "after": selected_after})
    store_object("BMesh_SelectionFlush", bm, (0, -2, 0))
    bm.free()

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    original = counts(bm)
    copied = bm.copy()
    bmesh.ops.translate(copied, verts=copied.verts[:], vec=(0.5, 0, 0))
    copy_counts = counts(copied)
    copied.free()
    records.append({"case": "owned_copy_and_free", "original": original, "copy": copy_counts, "original_still_valid": counts(bm) == original})
    store_object("BMesh_Ownership", bm, (3, -2, 0))
    bm.free()

    by_case = {record["case"]: record for record in records}
    assertions = {
        "remove_doubles_reduces_duplicate_vertex": by_case["remove_doubles"]["after"]["vertices"] == 3,
        "degenerate_cleanup_removes_zero_area_face": by_case["dissolve_degenerate"]["after"]["faces"] == 0,
        "triangulation_returns_four_faces": by_case["triangulate_ngon"]["after"]["faces"] == 4,
        "broad_limited_dissolve_failure_is_preserved": by_case["dissolve_limit_broad_boundary_failure"]["after"]["faces"] == 0,
        "direct_shared_edge_dissolve_merges_triangles": by_case["dissolve_shared_edge"]["after"]["faces"] == 1 and by_case["dissolve_shared_edge"]["after"]["vertices"] == 4,
        "normal_recalculation_restores_positive_volume": by_case["recalc_face_normals"]["signed_volume_before"] < 0 < by_case["recalc_face_normals"]["signed_volume_after"],
        "uv_custom_data_roundtrips": by_case["uv_custom_data_roundtrip"]["loops_nonzero_after_to_mesh"] == by_case["uv_custom_data_roundtrip"]["loops_written"],
        "selection_flush_selects_dependencies": by_case["selection_flush"]["after"]["verts"] > 0 and by_case["selection_flush"]["after"]["edges"] > 0,
        "copy_is_independent_and_original_survives": by_case["owned_copy_and_free"]["original_still_valid"],
    }
    report = {
        "lab": "modeler_relevant_bmesh_api",
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode("utf-8"),
        "records": records,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (output / "bmesh_api_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "bmesh_api_lab.blend"))
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("one or more BMesh assertions failed")


if __name__ == "__main__":
    main()
