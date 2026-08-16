"""Blender 5.2 lab for the typed two-endpoint Connect Vertex Path operation."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "blender_ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

import decision_state
import mesh_ops
import modeler_server
import persistent_ids
import state_fingerprint
from decision_transaction import DecisionTransaction

OUT = ROOT / "runs" / "2026-08-16_connect-vertex-path"
BLEND = OUT / "connect_vertex_path_lab.blend"
RENDER = OUT / "connect_vertex_path_solid.png"
REPORT = OUT / "connect_vertex_path_lab_report.json"


def mesh_object(name, vertices, faces, location=(0.0, 0.0, 0.0)):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.show_wire = True
    obj.show_all_edges = True
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


def topology(obj):
    owns_bmesh = obj.mode != "EDIT"
    if owns_bmesh:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
    else:
        bm = bmesh.from_edit_mesh(obj.data)
    components = 0
    remaining = set(bm.verts)
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            current = stack.pop()
            for edge in current.link_edges:
                other = edge.other_vert(current)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    result = {
        "verts": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "face_sizes": sorted(len(face.verts) for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "loose_vertices": sum(not vert.link_edges for vert in bm.verts),
        "loose_edges": sum(not edge.link_faces for edge in bm.edges),
        "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
        "components": components,
    }
    if owns_bmesh:
        bm.free()
    return result


def run_committed(obj):
    revision_before = decision_state.current_revision()
    with DecisionTransaction(revision_before, "connect_vertex_path", obj.name) as tx:
        operation = tx.perform(mesh_ops.connect_vertex_path, obj.name)
        verification = tx.verify()
        revision_after = tx.commit()
    return {
        "operation": operation,
        "verification": verification,
        "revision": [revision_before, revision_after],
        "topology": topology(obj),
    }


def run_rejected(obj, expected_fragment):
    persistent_ids.ensure_persistent_ids(obj.name)
    before = state_fingerprint.compute(obj.name)
    revision = decision_state.current_revision()
    error = None
    tx = None
    try:
        with DecisionTransaction(revision, "connect_vertex_path", obj.name) as tx:
            tx.perform(mesh_ops.connect_vertex_path, obj.name)
    except ValueError as exc:
        error = str(exc)
    after = state_fingerprint.compute(obj.name)
    changed, difference = state_fingerprint.diff(before, after)
    assert error and expected_fragment in error
    assert not changed
    assert decision_state.current_revision() == revision
    assert tx is not None and tx._failure_rolled_back
    return {
        "error": error,
        "automatic_rollback": tx._failure_rolled_back,
        "fingerprint_changed": changed,
        "fingerprint_diff": difference,
        "revision": revision,
        "topology": topology(obj),
    }


def configure_render(objects):
    visible = set(objects)
    for scene_object in bpy.context.scene.objects:
        if scene_object.type == "MESH" and scene_object not in visible:
            scene_object.hide_render = True
    for index, obj in enumerate(objects):
        obj.color = (0.12 + index * 0.1, 0.42, 0.8 - index * 0.18, 1.0)
    evidence_wires = []
    for obj in objects:
        wire = obj.copy()
        wire.data = obj.data.copy()
        wire.name = obj.name + "_TopologyEvidence"
        wire.location = obj.location.copy()
        wire.location.z += 0.015
        wire.color = (0.008, 0.008, 0.008, 1.0)
        bpy.context.scene.collection.objects.link(wire)
        modifier = wire.modifiers.new("Topology evidence", "WIREFRAME")
        modifier.thickness = 0.018
        modifier.use_replace = True
        evidence_wires.append(wire)
    bpy.ops.object.camera_add(location=(0.0, 0.0, 14.0))
    camera = bpy.context.object
    camera.name = "TopologyLabCamera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 11.0
    camera.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_specular_highlight = True
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 650
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER)
    bpy.ops.render.render(write_still=True)
    for wire in evidence_wires:
        wire_mesh = wire.data
        bpy.data.objects.remove(wire, do_unlink=True)
        bpy.data.meshes.remove(wire_mesh)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    records = []

    try:
        hexagon = mesh_object(
            "Connect_Hex_AllQuad",
            [(-2, 0, 0), (-1, -1, 0), (1, -1, 0), (2, 0, 0), (1, 1, 0), (-1, 1, 0)],
            [(0, 1, 2, 3, 4, 5)],
            location=(-3.0, 1.5, 0.0),
        )
        select_vertices(hexagon, [0, 3])
        detail = run_committed(hexagon)
        assert detail["topology"] == {
            "verts": 6, "edges": 7, "faces": 2, "face_sizes": [4, 4],
            "triangles": 0, "quads": 2, "ngons": 0, "degenerate_faces": 0,
            "loose_vertices": 0, "loose_edges": 0, "boundary_edges": 6, "components": 1,
        }
        assert detail["operation"]["new_verts"] == 0
        assert detail["operation"]["new_edges"] == 1
        records.append({"case": "single_face_all_quad_split", "pass": True, "detail": detail})
    except Exception as exc:
        records.append({"case": "single_face_all_quad_split", "pass": False, "error": str(exc), "traceback": traceback.format_exc()})

    try:
        strip = mesh_object(
            "Connect_ThreeFace_Strip",
            [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0),
             (0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0)],
            [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6)],
            location=(0.5, 1.0, 0.0),
        )
        select_vertices(strip, [0, 7])
        detail = run_committed(strip)
        expected = {
            "verts": 10, "edges": 15, "faces": 6, "face_sizes": [3, 3, 4, 4, 4, 4],
            "triangles": 2, "quads": 4, "ngons": 0, "degenerate_faces": 0,
            "loose_vertices": 0, "loose_edges": 0, "boundary_edges": 8, "components": 1,
        }
        assert detail["topology"] == expected
        assert detail["operation"]["new_verts"] == 2
        assert detail["operation"]["new_edges"] == 5
        records.append({"case": "three_face_connected_cut", "pass": True, "detail": detail})
    except Exception as exc:
        records.append({"case": "three_face_connected_cut", "pass": False, "error": str(exc), "traceback": traceback.format_exc()})

    try:
        edit_mode = mesh_object(
            "Connect_Live_EditMode",
            [(-2, 0, 0), (-1, -1, 0), (1, -1, 0), (2, 0, 0), (1, 1, 0), (-1, 1, 0)],
            [(0, 1, 2, 3, 4, 5)],
            location=(4.5, -1.5, 0.0),
        )
        select_vertices(edit_mode, [0, 3])
        bpy.context.view_layer.objects.active = edit_mode
        edit_mode.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        detail = run_committed(edit_mode)
        bpy.ops.object.mode_set(mode="OBJECT")
        assert detail["topology"]["face_sizes"] == [4, 4]
        assert detail["topology"]["ngons"] == 0
        records.append({"case": "live_edit_mode_transaction", "pass": True, "detail": detail})
    except Exception as exc:
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        records.append({"case": "live_edit_mode_transaction", "pass": False, "error": str(exc), "traceback": traceback.format_exc()})

    try:
        adjacent = mesh_object(
            "Reject_AlreadyConnected",
            [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
            [(0, 1, 2, 3)],
            location=(-2.0, -2.0, 0.0),
        )
        select_vertices(adjacent, [0, 1])
        detail = run_rejected(adjacent, "already share an edge")
        records.append({"case": "already_connected_rejection", "pass": True, "detail": detail})
    except Exception as exc:
        records.append({"case": "already_connected_rejection", "pass": False, "error": str(exc), "traceback": traceback.format_exc()})

    try:
        disconnected = mesh_object(
            "Reject_Disconnected",
            [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
             (2, 0, 0), (3, 0, 0), (3, 1, 0), (2, 1, 0)],
            [(0, 1, 2, 3), (4, 5, 6, 7)],
            location=(1.0, -2.0, 0.0),
        )
        select_vertices(disconnected, [0, 6])
        detail = run_rejected(disconnected, "do not define a connectable path")
        records.append({"case": "disconnected_rejection", "pass": True, "detail": detail})
    except Exception as exc:
        records.append({"case": "disconnected_rejection", "pass": False, "error": str(exc), "traceback": traceback.format_exc()})

    try:
        registered = modeler_server._OPS.get("connect_vertex_path") is mesh_ops.connect_vertex_path
        capability = "connect_vertex_path_topology" in modeler_server.CAPABILITIES
        assert registered and capability
        records.append({
            "case": "typed_protocol_registration", "pass": True,
            "detail": {"registered": registered, "capability": capability, "protocol": modeler_server.PROTOCOL_VERSION},
        })
    except Exception as exc:
        records.append({"case": "typed_protocol_registration", "pass": False, "error": str(exc), "traceback": traceback.format_exc()})

    configure_render([hexagon, strip])
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report = {
        "lab": "typed_connect_vertex_path",
        "blender_version": bpy.app.version_string,
        "scope": "exactly two visible selected endpoint vertices",
        "records": records,
        "passed": sum(record["pass"] for record in records),
        "total": len(records),
    }
    report["pass"] = report["passed"] == report["total"]
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CONNECT_VERTEX_PATH_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
