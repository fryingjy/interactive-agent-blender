"""Controlled reproduction of the Shrinkwrap+Bridge boolean-free cylinder-join technique.

Phase C of the 2026-08-17 continuation directive: the Priority-1 captured skill (from
runs/2026-08-17_video-study-mcglasham-subd-primitives-and-connections/knowledge_items.json,
item 1, source IS2LPVNp6SE, cross-checked in runs/2026-08-17_real-video-connecting-cylinders-review/)
is reproduced on neutral geometry -- a body cylinder with a spout/handle-stub cylinder joined
to its side -- using this project's own typed-mesh-construction house style (explicit bmesh
ring topology, not interactive slide operators, which do not reliably work in --background mode).

QUESTION: does the captured Shrinkwrap-Project + delete + join + Bridge Edge Loops recipe, applied
literally, produce a manifold, all-quad(-ish), visually clean joint in current Blender (5.2)?
HYPOTHESIS: yes, matching the source's and both independent extractions' claims.
CONTROL: the same two raw cylinders joined with a Boolean Union modifier instead (the naive
alternative the source explicitly warns against), subdivided the same way.
TREATMENT: the captured recipe.
MEASUREMENTS: base/evaluated vertex-face counts, non-manifold edge count, quad/tri/ngon
breakdown, and a beauty render for visual review (wireframe defects hide from mesh-health checks,
per this project's own flashlight-crater finding).

Execute with Blender in background mode:
    blender --background --factory-startup --python tools/run_cylinder_join_lab.py -- OUTPUT_DIR
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy


def output_directory() -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected exactly one OUTPUT_DIR argument after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def open_capped_cylinder(name, *, axis, radius, far, near, segments=16):
    """A single tube: an ngon cap at ``far`` and an open boundary ring at ``near``.

    ``axis`` is 'Z' or 'X'. ``far``/``near`` are signed positions along that axis
    (far is capped and away from the joint; near is the open collar to be joined).
    """
    bm = bmesh.new()
    ring_far = []
    ring_near = []
    for segment in range(segments):
        angle = 2.0 * math.pi * segment / segments
        a, b = radius * math.cos(angle), radius * math.sin(angle)
        if axis == "Z":
            ring_far.append(bm.verts.new((a, b, far)))
            ring_near.append(bm.verts.new((a, b, near)))
        elif axis == "X":
            ring_far.append(bm.verts.new((far, a, b)))
            ring_near.append(bm.verts.new((near, a, b)))
        else:
            raise ValueError("axis must be 'Z' or 'X'")
    bm.verts.ensure_lookup_table()
    for segment in range(segments):
        nxt = (segment + 1) % segments
        bm.faces.new((ring_far[segment], ring_far[nxt], ring_near[nxt], ring_near[segment]))
    bm.faces.new(reversed(ring_far))  # far-end ngon cap
    bm.normal_update()

    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    group = obj.vertex_groups.new(name="collar")
    # verts were interleaved far/near per segment above (far0, near0, far1, near1, ...)
    near_indices = [segment * 2 + 1 for segment in range(segments)]
    group.add(near_indices, 1.0, "REPLACE")
    return obj


def add_shrinkwrap(obj, *, target, vertex_group, axis, offset, wrap_method="PROJECT"):
    modifier = obj.modifiers.new("Shrinkwrap", "SHRINKWRAP")
    modifier.wrap_method = wrap_method
    if wrap_method == "PROJECT":
        modifier.use_project_x = axis == "X"
        modifier.use_project_y = axis == "Y"
        modifier.use_project_z = axis == "Z"
        modifier.use_negative_direction = True
        modifier.use_positive_direction = True
    modifier.target = target
    modifier.vertex_group = vertex_group
    modifier.offset = offset
    return modifier


def apply_modifier(obj, modifier_name):
    with bpy.context.temp_override(
        object=obj, active_object=obj, selected_editable_objects=[obj]
    ):
        bpy.ops.object.modifier_apply(modifier=modifier_name)


def mesh_metrics(obj) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            face_sizes = [len(face.verts) for face in bm.faces]
            valence = {}
            for vert in bm.verts:
                valence[len(vert.link_edges)] = valence.get(len(vert.link_edges), 0) + 1
            return {
                "base": {
                    "vertices": len(obj.data.vertices),
                    "edges": len(obj.data.edges),
                    "faces": len(obj.data.polygons),
                },
                "evaluated": {
                    "vertices": len(bm.verts),
                    "edges": len(bm.edges),
                    "faces": len(bm.faces),
                    "quads": sum(1 for size in face_sizes if size == 4),
                    "triangles": sum(1 for size in face_sizes if size == 3),
                    "ngons": sum(1 for size in face_sizes if size > 4),
                    "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                    "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
                    "valence_distribution": valence,
                },
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def max_dihedral_angle_degrees(obj) -> dict:
    """Sharpest and median angle between adjacent face normals on the base control cage.

    Distinguishes a genuine geometric fold (a hard local crease) from healthy SubD
    curvature, which this project's own flashlight-crater finding showed a plain
    non-manifold/ngon mesh-health check cannot tell apart.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        angles = [
            math.degrees(edge.link_faces[0].normal.angle(edge.link_faces[1].normal))
            for edge in bm.edges
            if len(edge.link_faces) == 2
        ]
        angles.sort(reverse=True)
        return {
            "max_degrees": angles[0] if angles else None,
            "top5_degrees": angles[:5],
            "median_degrees": angles[len(angles) // 2] if angles else None,
        }
    finally:
        bm.free()


def build_treatment(report: dict, output_dir: Path, *, wrap_method: str, label: str) -> None:
    """Shrinkwrap + delete-interior + join + Bridge Edge Loops, per the captured recipe.

    ``wrap_method`` isolates one variable against the literal captured recipe (PROJECT):
    NEAREST_SURFACEPOINT always finds some point on the target regardless of ray
    direction, directly testing whether the diagnosed partial-coverage fold (PROJECT
    leaves an unhit vertex exactly where it started) is actually caused by wrap method.
    """
    clear_scene()

    body = open_capped_cylinder(
        "Body", axis="Z", radius=0.5, far=-2.5, near=0.15, segments=16
    )
    spout = open_capped_cylinder(
        "Spout", axis="X", radius=0.5, far=3.0, near=-0.15, segments=16
    )

    # Body's tube runs along its own local Z (unrotated) -> project along Z.
    # Spout's tube geometry runs along X but the object itself was never rotated,
    # so its "own axis" in local-frame terms is still X, not Z -- project along X.
    add_shrinkwrap(body, target=spout, vertex_group="collar", axis="Z", offset=-0.1, wrap_method=wrap_method)
    add_shrinkwrap(spout, target=body, vertex_group="collar", axis="X", offset=-0.1, wrap_method=wrap_method)

    report[label]["wrap_method"] = wrap_method
    report[label]["pre_shrinkwrap"] = {
        "body": mesh_metrics(body),
        "spout": mesh_metrics(spout),
    }

    apply_modifier(body, "Shrinkwrap")
    apply_modifier(spout, "Shrinkwrap")

    report[label]["post_shrinkwrap"] = {
        "body": mesh_metrics(body),
        "spout": mesh_metrics(spout),
    }

    body.select_set(True)
    spout.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    joined = body
    joined.name = f"BodySpoutJoined_{label}"

    bm = bmesh.new()
    bm.from_mesh(joined.data)
    bm.verts.ensure_lookup_table()
    boundary_edges = [edge for edge in bm.edges if edge.is_boundary]
    report[label]["boundary_edges_before_bridge"] = len(boundary_edges)
    bridge_result = bmesh.ops.bridge_loops(bm, edges=boundary_edges)
    report[label]["bridge_faces_created"] = len(bridge_result.get("faces", []))
    bm.normal_update()
    bm.to_mesh(joined.data)
    joined.data.update()
    bm.free()

    report[label]["dihedral_angles_pre_subsurf"] = max_dihedral_angle_degrees(joined)

    subsurf = joined.modifiers.new("Subdivision", "SUBSURF")
    subsurf.levels = 2
    subsurf.render_levels = 2
    joined.data.polygons.foreach_set("use_smooth", [True] * len(joined.data.polygons))
    joined.data.update()

    report[label]["final"] = mesh_metrics(joined)

    blend_path = output_dir / f"cylinder_join_{label}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report[label]["blend_path"] = str(blend_path)


def build_control(report: dict, output_dir: Path) -> None:
    """Naive Boolean Union of the same two overlapping cylinders, then Subdivision Surface."""
    clear_scene()

    body = open_capped_cylinder(
        "BodyControl", axis="Z", radius=0.5, far=-2.5, near=1.0, segments=16
    )
    spout = open_capped_cylinder(
        "SpoutControl", axis="X", radius=0.5, far=3.0, near=-0.5, segments=16
    )
    # Give the control pair genuine 3D overlap (unlike the treatment's open-collar tubes)
    # by capping their near ends too, so Boolean Union has two real closed solids to combine.
    for obj, axis in ((body, "Z"), (spout, "X")):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        boundary = [edge for edge in bm.edges if edge.is_boundary]
        bmesh.ops.holes_fill(bm, edges=boundary)
        bm.normal_update()
        bm.to_mesh(obj.data)
        obj.data.update()
        bm.free()

    boolean = body.modifiers.new("Boolean", "BOOLEAN")
    boolean.operation = "UNION"
    boolean.object = spout
    boolean.solver = "EXACT"

    report["control"]["pre_boolean"] = {
        "body": mesh_metrics(body),
        "spout": mesh_metrics(spout),
    }

    apply_modifier(body, "Boolean")
    spout.hide_render = True
    spout.hide_viewport = True

    report["control"]["post_boolean"] = mesh_metrics(body)

    subsurf = body.modifiers.new("Subdivision", "SUBSURF")
    subsurf.levels = 2
    subsurf.render_levels = 2
    body.data.polygons.foreach_set("use_smooth", [True] * len(body.data.polygons))
    body.data.update()
    body.name = "BodySpoutBoolean"

    report["control"]["final"] = mesh_metrics(body)

    blend_path = output_dir / "cylinder_join_control.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report["control"]["blend_path"] = str(blend_path)


def main() -> None:
    output_dir = output_directory()
    report = {
        "question": (
            "Does the captured Shrinkwrap-Project + delete + join + Bridge Edge Loops recipe "
            "produce a manifold, clean-topology joint, compared to a naive Boolean Union?"
        ),
        "treatment": {},
        "treatment_nearest_surface_variant": {},
        "control": {},
    }

    build_treatment(report, output_dir, wrap_method="PROJECT", label="treatment")
    build_treatment(
        report, output_dir, wrap_method="NEAREST_SURFACEPOINT", label="treatment_nearest_surface_variant"
    )
    build_control(report, output_dir)

    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote report: {report_path}")


if __name__ == "__main__":
    main()
