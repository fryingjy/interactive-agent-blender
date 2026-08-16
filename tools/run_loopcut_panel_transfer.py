"""Transfer the reviewed loop-cut planning principle to a recessed control panel.

One box mesh is partitioned with orthogonal loop cuts, then its intended center
region is inset and extruded downward. No mesh primitives are assembled.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from blender_ops import decision_state, mesh_ops, object_ops, state_probe
from blender_ops.decision_transaction import DecisionTransaction

RUN = ROOT / "runs" / "2026-08-16_real-video-loopcut-review"


def bmesh_for(name):
    obj = bpy.data.objects[name]
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    return obj, bm


def write(obj, bm):
    bm.to_mesh(obj.data); bm.free(); obj.data.update()


def select_ring(name, axis):
    obj, bm = bmesh_for(name)
    for seq in (bm.verts, bm.edges, bm.faces):
        for item in seq: item.select = False
    count = 0
    for edge in bm.edges:
        direction = (edge.verts[1].co - edge.verts[0].co).normalized()
        if abs(abs(direction.dot(axis)) - 1.0) < 1e-6:
            edge.select = True; count += 1
    write(obj, bm)
    return count


def select_center_top(name):
    obj, bm = bmesh_for(name)
    for seq in (bm.verts, bm.edges, bm.faces):
        for item in seq: item.select = False
    selected = []
    for face in bm.faces:
        center = face.calc_center_median()
        if face.normal.z > 0.9 and abs(center.x) < 0.1 and abs(center.y) < 0.1:
            face.select = True; selected.append(face)
    write(obj, bm)
    if len(selected) != 1:
        raise RuntimeError(f"expected one center panel face, selected {len(selected)}")
    return 1


def component_count(name):
    _, bm = bmesh_for(name)
    unseen = set(bm.verts); count = 0
    while unseen:
        count += 1; stack = [unseen.pop()]
        while stack:
            vert = stack.pop()
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other in unseen: unseen.remove(other); stack.append(other)
    bm.free(); return count


def act(revision, action, name, fn, *args):
    with DecisionTransaction(revision, action, target_object=name) as tx:
        result = tx.perform(fn, *args); verification = tx.verify(); next_revision = tx.commit()
    return next_revision, {"action": action, "result": result, "verification": verification}


def main():
    RUN.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection = bpy.data.collections.new("TRANSFER_DIFFERENT_GEOMETRY")
    bpy.context.scene.collection.children.link(collection)
    bpy.ops.mesh.primitive_cube_add(size=2)
    obj = bpy.context.object; obj.name = "LoopCutControlPanel_ContinuousMesh"
    for owner in list(obj.users_collection): owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.scale = (3.0, 2.0, 0.35); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    revision = decision_state.current_revision(); decisions = []

    edge_count = select_ring(obj.name, Vector((0, 1, 0)))
    revision, entry = act(revision, "loop_cut_x_panel_boundaries", obj.name, mesh_ops.loop_cut_selection, obj.name, 2)
    entry["mechanical_selection_edges"] = edge_count; decisions.append(entry)
    edge_count = select_ring(obj.name, Vector((1, 0, 0)))
    revision, entry = act(revision, "loop_cut_y_panel_boundaries", obj.name, mesh_ops.loop_cut_selection, obj.name, 2)
    entry["mechanical_selection_edges"] = edge_count; decisions.append(entry)

    face_count = select_center_top(obj.name)
    revision, entry = act(revision, "inset_intended_panel_region", obj.name, mesh_ops.inset_selection, obj.name, 0.22, 0.0)
    entry["mechanical_selected_faces"] = face_count; decisions.append(entry)
    revision, entry = act(revision, "recess_intended_panel_region", obj.name, mesh_ops.extrude_selection, obj.name, -0.28)
    decisions.append(entry)
    revision, entry = act(revision, "add_live_bevel", obj.name, object_ops.add_modifier, obj.name, "BEVEL", "Manual Bevel - Unapplied")
    obj.modifiers["Manual Bevel - Unapplied"].width = 0.035
    obj.modifiers["Manual Bevel - Unapplied"].segments = 2
    obj.modifiers["Manual Bevel - Unapplied"].limit_method = "ANGLE"
    decisions.append(entry)

    scene = bpy.context.scene; scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"
    scene.display.shading.show_shadows = True; scene.display.shading.show_cavity = True
    bpy.ops.object.camera_add(location=(7.5, -8.5, 6.5))
    camera = bpy.context.object; camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler(); scene.camera = camera
    scene.render.resolution_x = 800; scene.render.resolution_y = 800; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"; scene.render.filepath = str(RUN / "control_panel_transfer_solid.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN / "loopcut_control_panel_transfer.blend"))
    report = {"principle": "Use loop cuts to reserve a later functional region in one mesh, then operate on that selected region.", "source_episode_review": "episode_review.json", "target": "recessed control panel, unlike the source chair", "object": obj.name, "collection": collection.name, "connected_components": component_count(obj.name), "mesh_health": state_probe.mesh_health(obj.name), "modifiers": [{"name": m.name, "type": m.type, "live": m.show_viewport} for m in obj.modifiers], "modifier_apply_called": False, "decisions": decisions, "claim_boundary": "A controlled different-geometry transfer of one topology-planning principle; not a complete real-product asset."}
    (RUN / "loopcut_control_panel_transfer_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
