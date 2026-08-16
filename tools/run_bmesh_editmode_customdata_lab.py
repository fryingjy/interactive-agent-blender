"""Exercise live Edit Mode BMesh and current custom-data layers in Blender 5.2.

This is a technical API fixture, not an asset or evidence of artistic modeling quality.
"""

from __future__ import annotations

import json
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-16_bmesh-editmode-customdata"
BLEND = OUT / "bmesh_editmode_customdata.blend"
REPORT = OUT / "lab_report.json"


def build_cube_mesh() -> bpy.types.Object:
    vertices = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
    ]
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7),
        (0, 1, 5, 4), (1, 2, 6, 5),
        (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new("BMesh_EditMode_CustomData_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("BMesh_EditMode_CustomData", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def main() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = build_cube_mesh()
    mesh = obj.data
    base_counts = {"vertices": len(mesh.vertices), "edges": len(mesh.edges), "faces": len(mesh.polygons)}

    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(mesh)
    same_live_bmesh = bm is bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    subdivide_result = bmesh.ops.subdivide_edges(
        bm,
        edges=list(bm.edges),
        cuts=1,
        use_grid_fill=True,
    )
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()

    bevel_layer = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    crease_layer = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
    region_layer = bm.faces.layers.int.get("semantic_region") or bm.faces.layers.int.new("semantic_region")
    uv_layer = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")

    weighted_edges = []
    creased_edges = []
    semantic_faces = []
    for edge in bm.edges:
        edge[bevel_layer] = 0.0
        edge[crease_layer] = 0.0
        a, b = edge.verts
        same_x = abs(a.co.x - b.co.x) < 1e-7
        same_y = abs(a.co.y - b.co.y) < 1e-7
        same_z = abs(a.co.z - b.co.z) < 1e-7
        if same_x and same_y and abs(a.co.x) > 0.99 and abs(a.co.y) > 0.99 and not same_z:
            edge[bevel_layer] = 1.0
            weighted_edges.append(edge.index)
        if same_z and a.co.z > 0.99 and b.co.z > 0.99:
            edge[crease_layer] = 0.75
            creased_edges.append(edge.index)

    for face in bm.faces:
        face[region_layer] = 0
        if all(vertex.co.z > 0.99 for vertex in face.verts):
            face[region_layer] = 7
            semantic_faces.append(face.index)
        for loop in face.loops:
            loop[uv_layer].uv = ((loop.vert.co.x + 1.0) * 0.5, (loop.vert.co.y + 1.0) * 0.5)

    for vert in bm.verts:
        vert.select = False
    for edge in bm.edges:
        edge.select = False
    for face in bm.faces:
        face.select = False
    bm.faces[0].select = True
    bm.select_flush(True)
    selected_in_edit_mode = {
        "vertices": sum(vertex.select for vertex in bm.verts),
        "edges": sum(edge.select for edge in bm.edges),
        "faces": sum(face.select for face in bm.faces),
    }

    edit_counts = {"vertices": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces)}
    bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.calc_loop_triangles()

    final_counts = {"vertices": len(mesh.vertices), "edges": len(mesh.edges), "faces": len(mesh.polygons)}
    attribute_summary = {
        name: {
            "domain": mesh.attributes[name].domain,
            "data_type": mesh.attributes[name].data_type,
            "nonzero": sum(abs(getattr(item, "value", 0)) > 1e-8 for item in mesh.attributes[name].data),
        }
        for name in ("bevel_weight_edge", "crease_edge", "semantic_region")
        if name in mesh.attributes
    }
    uv_nonzero = sum(loop.uv.length_squared > 1e-8 for loop in mesh.uv_layers["UVMap"].data)

    check_bm = bmesh.new()
    check_bm.from_mesh(mesh)
    non_manifold = sum(not edge.is_manifold for edge in check_bm.edges)
    degenerate_faces = sum(face.calc_area() <= 1e-12 for face in check_bm.faces)
    face_sizes = sorted({len(face.verts) for face in check_bm.faces})
    check_bm.free()

    obj["fixture_purpose"] = "edit_mode_bmesh_customdata_api_validation"
    obj["expected_weighted_edge_count"] = len(weighted_edges)
    obj["expected_creased_edge_count"] = len(creased_edges)
    obj["expected_semantic_face_count"] = len(semantic_faces)
    assertions = {
        "from_edit_mesh_returns_live_bmesh": same_live_bmesh,
        "topology_changed_in_edit_mode": final_counts != base_counts and final_counts == edit_counts,
        "subdivide_returned_geometry": bool(subdivide_result.get("geom_inner")),
        "destructive_update_produced_loop_triangles": len(mesh.loop_triangles) > 0,
        "selection_flush_selected_face_dependencies": selected_in_edit_mode["faces"] == 1 and selected_in_edit_mode["edges"] >= 4 and selected_in_edit_mode["vertices"] >= 4,
        "bevel_weight_edge_persisted": attribute_summary.get("bevel_weight_edge", {}).get("domain") == "EDGE" and attribute_summary["bevel_weight_edge"]["nonzero"] == len(weighted_edges) > 0,
        "crease_edge_persisted": attribute_summary.get("crease_edge", {}).get("domain") == "EDGE" and attribute_summary["crease_edge"]["nonzero"] == len(creased_edges) > 0,
        "face_int_region_persisted": attribute_summary.get("semantic_region", {}).get("domain") == "FACE" and attribute_summary["semantic_region"]["nonzero"] == len(semantic_faces) > 0,
        "uv_loop_layer_persisted": "UVMap" in mesh.uv_layers and uv_nonzero > 0,
        "closed_non_degenerate_result": non_manifold == 0 and degenerate_faces == 0,
        "all_result_faces_are_quads": face_sizes == [4],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report = {
        "blender_version": bpy.app.version_string,
        "official_api": [
            "https://docs.blender.org/api/current/bmesh.html",
            "https://docs.blender.org/api/current/bmesh.types.html",
            "https://docs.blender.org/api/current/bmesh.ops.html",
        ],
        "base_counts": base_counts,
        "edit_counts": edit_counts,
        "final_counts": final_counts,
        "selected_in_edit_mode": selected_in_edit_mode,
        "attribute_summary": attribute_summary,
        "uv_nonzero_loops": uv_nonzero,
        "loop_triangle_count": len(mesh.loop_triangles),
        "weighted_edge_indices": weighted_edges,
        "creased_edge_indices": creased_edges,
        "semantic_face_indices": semantic_faces,
        "non_manifold_edges": non_manifold,
        "degenerate_faces": degenerate_faces,
        "face_sizes": face_sizes,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "claim_boundary": "A controlled API fixture proving current Edit Mode BMesh update, selection flushing, and custom-data persistence. It does not prove arbitrary operator coverage or artistic topology quality.",
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    raise SystemExit(0 if report["pass"] else 2)


main()
