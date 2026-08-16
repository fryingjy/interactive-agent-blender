"""Reproduce the reviewed loop-cut principle in a Blender scene.

The result is one continuous low-poly mesh: a chair-shaped study grown from a
single flattened cube.  Loop cuts create the selectable regions before the
leg and back extrusions.  The Bevel modifier stays live and unapplied.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "blender_ops") not in sys.path:
    sys.path.insert(0, str(ROOT / "blender_ops"))

from blender_ops import decision_state, mesh_ops, object_ops, state_probe
from blender_ops.decision_transaction import DecisionTransaction


RUN = ROOT / "runs" / "2026-08-16_real-video-loopcut-review"
BLEND_PATH = RUN / "loopcut_chair_transfer.blend"


def mesh_bm(name: str):
    obj = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return obj, bm


def write_bm(obj, bm) -> None:
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def select_axis_edge_ring(name: str, axis: Vector) -> int:
    """Mechanical selection of the complete axis-aligned quad ring."""
    obj, bm = mesh_bm(name)
    count = 0
    for vert in bm.verts:
        vert.select = False
    for face in bm.faces:
        face.select = False
    for edge in bm.edges:
        edge.select = False
        direction = (edge.verts[1].co - edge.verts[0].co).normalized()
        if abs(abs(direction.dot(axis)) - 1.0) < 1e-6:
            edge.select = True
            count += 1
    write_bm(obj, bm)
    return count


def select_chair_leg_faces(name: str) -> int:
    obj, bm = mesh_bm(name)
    count = 0
    for face in bm.faces:
        face.select = False
        center = face.calc_center_median()
        if face.normal.z < -0.9 and abs(center.x) > 1.0 and abs(center.y) > 1.0:
            face.select = True
            count += 1
    write_bm(obj, bm)
    return count


def select_chair_back_faces(name: str) -> int:
    obj, bm = mesh_bm(name)
    count = 0
    for face in bm.faces:
        face.select = False
        center = face.calc_center_median()
        if face.normal.z > 0.9 and center.y > 1.0:
            face.select = True
            count += 1
    write_bm(obj, bm)
    return count


def connected_components(name: str) -> int:
    obj, bm = mesh_bm(name)
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
    bm.free()
    return components


def transaction(revision: int, action: str, object_name: str, fn, *args, **kwargs):
    with DecisionTransaction(revision, action, target_object=object_name) as tx:
        result = tx.perform(fn, *args, **kwargs)
        verification = tx.verify()
        next_revision = tx.commit()
    return next_revision, {"action": action, "result": result, "verification": verification}


def setup() -> bpy.types.Object:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection = bpy.data.collections.new("TRANSFER_LOW_POLY")
    bpy.context.scene.collection.children.link(collection)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = "LoopCutChair_ContinuousMesh"
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)
    obj.scale = (2.0, 2.0, 0.3)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    chair = setup()
    name = chair.name
    revision = decision_state.current_revision()
    decisions = []

    selected = select_axis_edge_ring(name, Vector((0, 1, 0)))
    revision, record = transaction(revision, "loop_cut_x_regions", name, mesh_ops.loop_cut_selection, name, 3)
    record["mechanical_selection_edges"] = selected
    decisions.append(record)

    selected = select_axis_edge_ring(name, Vector((1, 0, 0)))
    revision, record = transaction(revision, "loop_cut_y_regions", name, mesh_ops.loop_cut_selection, name, 3)
    record["mechanical_selection_edges"] = selected
    decisions.append(record)

    selected = select_chair_leg_faces(name)
    revision, record = transaction(revision, "extrude_four_leg_regions", name, mesh_ops.extrude_selection, name, -1.6)
    record["mechanical_selected_faces"] = selected
    decisions.append(record)

    selected = select_chair_back_faces(name)
    revision, record = transaction(revision, "extrude_back_row", name, mesh_ops.extrude_selection, name, 2.2)
    record["mechanical_selected_faces"] = selected
    decisions.append(record)

    # A live, user-adjustable modifier is added after the mesh decisions. It is not applied.
    revision, record = transaction(revision, "add_live_bevel", name, object_ops.add_modifier, name, "BEVEL", "Manual Bevel - Unapplied")
    bevel = chair.modifiers["Manual Bevel - Unapplied"]
    bevel.width = 0.04
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    record["modifier_is_live"] = chair.modifiers["Manual Bevel - Unapplied"].show_viewport
    decisions.append(record)

    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.studio_light = "paint.sl"
    bpy.context.scene.display.shading.show_shadows = True
    bpy.context.scene.display.shading.show_cavity = True
    bpy.ops.object.camera_add(location=(7.5, -8.5, 6.5))
    camera = bpy.context.object
    camera.name = "ReviewCamera"
    camera.rotation_euler = (Vector((0.0, 0.0, 0.5)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = camera
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 800
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = str(RUN / "chair_transfer_solid.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))

    report = {
        "principle": "Add loop cuts only where later component regions are needed; then extrude those regions from the same continuous mesh.",
        "source_episode_review": "episode_review.json",
        "target": "chair blockout built from one cube rather than assembled primitive components",
        "object": name,
        "collections": [collection.name for collection in chair.users_collection],
        "base_object_count": 1,
        "connected_components": connected_components(name),
        "mesh_health": state_probe.mesh_health(name),
        "modifiers": [{"name": mod.name, "type": mod.type, "show_viewport": mod.show_viewport} for mod in chair.modifiers],
        "modifier_apply_called": False,
        "decisions": decisions,
        "claim_boundary": "This is a narrow reproduction of the episode's topology-planning principle, not evidence of complete chair design, reference fidelity, or generalized autonomous modeling."
    }
    (RUN / "loopcut_chair_transfer_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
