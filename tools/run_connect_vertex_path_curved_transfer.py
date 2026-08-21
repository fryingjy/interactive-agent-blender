"""Transfer typed Connect Vertex Path to curved, SubD-sensitive topology."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

from lab_common import add_repo_paths

ROOT, OPS = add_repo_paths(__file__)

import persistent_ids
import state_fingerprint
from modeler_server import ModelerServer

OUT = ROOT / "runs" / "2026-08-16_connect-vertex-path-curved-transfer"
BLEND = OUT / "connect_vertex_path_curved_transfer.blend"
REPORT = OUT / "connect_vertex_path_curved_transfer_report.json"
SOLID = OUT / "connect_vertex_path_curved_transfer_matcap.png"
WIRE = OUT / "connect_vertex_path_curved_transfer_wire.png"


def make_object(name, vertices, faces, location):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    if sum(face.normal.z for face in bm.faces) < 0.0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    persistent_ids.ensure_persistent_ids(name)
    return obj


def select_vertices(obj, indices):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    for sequence in (bm.verts, bm.edges, bm.faces):
        for element in sequence:
            element.select = False
    for index in indices:
        bm.verts[index].select = True
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def base_topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "face_sizes": sorted(len(face.verts) for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
    }
    bm.free()
    return result


def evaluated_topology(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold and not edge.is_boundary for edge in bm.edges),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def add_subd(obj):
    modifier = obj.modifiers.new("Live curved-surface subdivision", "SUBSURF")
    modifier.subdivision_type = "CATMULL_CLARK"
    modifier.levels = modifier.render_levels = 2


def commit_path(server, obj):
    begin = server.cmd_begin_decision(obj.name, "connect_vertex_path_subd_safe")
    performed = server.cmd_perform_decision(
        begin["decision_id"], "connect_vertex_path",
        {"check_degenerate": True, "require_all_quads": True},
        command_id=f"{obj.name}_subd_safe_connect",
    )
    verified = server.cmd_verify_decision(begin["decision_id"])
    committed = server.cmd_commit_decision(begin["decision_id"])
    return {
        "operation": performed["result"],
        "begin_revision": begin["observed_revision"],
        "result_revision": committed["result_revision"],
        "verified_after_present": verified["after"] is not None,
    }


def reject_diagonal(server, obj):
    before = state_fingerprint.compute(obj.name)
    begin = server.cmd_begin_decision(obj.name, "connect_vertex_path_subd_safe_rejection")
    error = None
    try:
        server.cmd_perform_decision(
            begin["decision_id"], "connect_vertex_path",
            {"check_degenerate": True, "require_all_quads": True},
            command_id=f"{obj.name}_subd_safe_reject",
        )
    except ValueError as exc:
        error = str(exc)
    abandoned = server.cmd_abandon_decision(begin["decision_id"], "strict quad preflight rejection")
    after = state_fingerprint.compute(obj.name)
    changed, difference = state_fingerprint.diff(before, after)
    return {
        "begin_revision": begin["observed_revision"],
        "error": error,
        "abandoned": abandoned,
        "fingerprint_changed": changed,
        "fingerprint_diff": difference,
    }


def setup_scene(path, wire=False):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 620
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    scene.display.shading.type = "SOLID"
    scene.display.shading.light = "STUDIO" if not wire else "FLAT"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_shadows = True
    scene.display.shading.background_type = "WORLD"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Connect Curved Review World")
    scene.world.color = (0.018, 0.024, 0.035)
    camera_data = bpy.data.cameras.get("ConnectCurvedCamera") or bpy.data.cameras.new("ConnectCurvedCamera")
    camera = bpy.data.objects.get("ConnectCurvedCamera") or bpy.data.objects.new("ConnectCurvedCamera", camera_data)
    if not camera.users_collection:
        scene.collection.objects.link(camera)
    camera.location = (0.0, -9.5, 9.8)
    camera.rotation_euler = (Vector((0.0, 0.0, 0.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 8.2
    scene.camera = camera


def render(objects, path, wire=False):
    temporary = []
    for index, obj in enumerate(objects):
        obj.hide_render = False
        obj.color = ((0.18, 0.52, 0.82, 1.0), (0.24, 0.72, 0.48, 1.0), (0.76, 0.32, 0.20, 1.0))[index]
        if wire:
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=bpy.context.evaluated_depsgraph_get())
            item = bpy.data.objects.new(obj.name + "_EvidenceWire", mesh)
            bpy.context.scene.collection.objects.link(item)
            item.matrix_world = obj.matrix_world.copy()
            item.color = (0.008, 0.012, 0.02, 1.0)
            modifier = item.modifiers.new("Topology wire", "WIREFRAME")
            modifier.thickness = 0.010
            modifier.use_replace = True
            obj.hide_render = True
            temporary.append(item)
    setup_scene(path, wire=wire)
    bpy.ops.render.render(write_still=True)
    for item in temporary:
        mesh = item.data
        bpy.data.objects.remove(item, do_unlink=True)
        bpy.data.meshes.remove(mesh)
    for obj in objects:
        obj.hide_render = False


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()

    crown = make_object(
        "Crown_Hex_Repair",
        [(-1.6, 0.0, 0.02), (-0.8, -1.1, 0.20), (0.9, -1.0, 0.34), (1.6, 0.0, 0.12), (0.8, 1.1, -0.10), (-0.9, 1.0, -0.18)],
        [(0, 1, 2, 3, 4, 5)], (-2.3, 1.55, 0.0),
    )
    twisted = make_object(
        "Twisted_Hex_Repair",
        [(-1.45, 0.0, -0.15), (-0.75, -1.0, 0.30), (0.85, -1.05, -0.28), (1.5, 0.0, 0.22), (0.75, 1.0, 0.36), (-0.8, 1.05, -0.24)],
        [(0, 1, 2, 3, 4, 5)], (2.3, 1.55, 0.0),
    )
    strip = make_object(
        "Curved_Strip_Diagonal_Control",
        [(1.2, -0.8, 0.0), (1.35, -0.3, 0.0), (1.35, 0.3, 0.0), (1.2, 0.8, 0.0),
         (1.2, -0.8, 1.0), (1.35, -0.3, 1.0), (1.35, 0.3, 1.0), (1.2, 0.8, 1.0)],
        [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6)], (0.0, -1.7, -0.3),
    )
    for obj in (crown, twisted, strip):
        add_subd(obj)
    select_vertices(crown, [0, 3])
    select_vertices(twisted, [0, 3])
    select_vertices(strip, [0, 7])

    crown_tx = commit_path(server, crown)
    twisted_tx = commit_path(server, twisted)
    rejected = reject_diagonal(server, strip)
    records = {
        crown.name: {"base": base_topology(crown), "evaluated": evaluated_topology(crown), "transaction": crown_tx},
        twisted.name: {"base": base_topology(twisted), "evaluated": evaluated_topology(twisted), "transaction": twisted_tx},
        strip.name: {"base": base_topology(strip), "evaluated": evaluated_topology(strip), "rejection": rejected},
    }
    render([crown, twisted, strip], SOLID, wire=False)
    render([crown, twisted, strip], WIRE, wire=True)
    assertions = {
        "two_curved_hex_repairs_become_all_quad": all(
            records[name]["base"]["face_sizes"] == [4, 4]
            and records[name]["base"]["triangles"] == 0
            and records[name]["base"]["ngons"] == 0
            for name in (crown.name, twisted.name)
        ),
        "two_curved_subd_results_are_clean": all(
            records[name]["evaluated"]["triangles"] == 0
            and records[name]["evaluated"]["ngons"] == 0
            and records[name]["evaluated"]["degenerate_faces"] == 0
            and records[name]["evaluated"]["non_manifold_edges"] == 0
            for name in (crown.name, twisted.name)
        ),
        "live_subdivision_remains_unapplied": all(
            [modifier.type for modifier in obj.modifiers] == ["SUBSURF"] for obj in (crown, twisted, strip)
        ),
        "typed_transactions_commit_and_verify": all(
            record["transaction"]["result_revision"] == record["transaction"]["begin_revision"] + 1
            and record["transaction"]["verified_after_present"]
            and record["transaction"]["operation"]["require_all_quads"]
            for record in (records[crown.name], records[twisted.name])
        ),
        "strict_quad_preflight_rejects_curved_diagonal_without_mutation": (
            rejected["error"] is not None
            and "require_all_quads" in rejected["error"]
            and not rejected["fingerprint_changed"]
            and rejected["abandoned"]["failed_operation_rolled_back"]
            and records[strip.name]["base"]["face_sizes"] == [4, 4, 4]
        ),
        "render_evidence_exists": all(path.is_file() and path.stat().st_size > 0 for path in (SOLID, WIRE)),
    }
    report = {
        "lab": "typed_connect_vertex_path_curved_subd_transfer",
        "blender_version": bpy.app.version_string,
        "scope": "two endpoint Connect Vertex Path; strict all-quad preflight for SubD-sensitive calls",
        "records": records,
        "assertions": assertions,
        "renders": [SOLID.name, WIRE.name],
        "pass": all(assertions.values()),
        "claim_boundary": "Two controlled curved nonplanar six-sided repair patches and one curved strip rejection. This demonstrates a strict typed preflight and live SubD topology outcome, not ordered multi-point support, arbitrary real-prop path selection, or professional reference fidelity.",
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print("CONNECT_VERTEX_PATH_CURVED_RESULT:" + json.dumps({"pass": report["pass"], "assertions": assertions}))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
