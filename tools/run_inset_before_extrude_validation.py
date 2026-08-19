"""Controlled validation of the inset-before-extrude family, headless.

Tests two independent variables against the captured claim (McGlasham insetting/softbodies
episode: direct extrude plants a pole at the extrusion base, "the area of maximum distortion"):
surface curvature (flat panel vs. curved cylinder body) and feature scale (small local
detail vs. a larger attached form). Completes the missing control for the live spout-growing
transfer test done earlier this session (curved+larger+inset already has real evidence;
curved+larger+direct is the new control that makes it a genuine A/B).

Execute headlessly:
    blender --background --factory-startup --python tools/run_inset_before_extrude_validation.py -- OUTPUT_DIR
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


def flat_panel(name, *, size=3.0, subdivisions=6):
    """A subdivided flat quad grid -- a hard-surface panel, not a bare single face,
    matching the source's own demo ('even on an already-subdivided flat plane')."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=subdivisions, y_segments=subdivisions, size=size / 2.0)
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh); bm.free(); mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def open_capped_cylinder(name, *, radius, far, near, segments=24, bands=1):
    """One tube, ngon cap at far, open collar at near, with ``bands`` height rows --
    matching the actual live-validated spout-growth construction (2 loop cuts / 3 bands),
    not a single full-height panel, so the target face for inset/extrude is a properly
    proportioned mid-band cell rather than an elongated whole-height strip."""
    bm = bmesh.new()
    rings = []
    for row in range(bands + 1):
        t = row / bands
        z = far + (near - far) * t
        ring = [bm.verts.new((radius * math.cos(2.0 * math.pi * s / segments),
                               radius * math.sin(2.0 * math.pi * s / segments), z))
                for s in range(segments)]
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for row in range(bands):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            bm.faces.new((rings[row][segment], rings[row][nxt], rings[row + 1][nxt], rings[row + 1][segment]))
    bm.faces.new(reversed(rings[0]))
    bm.normal_update()
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh); bm.free(); mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def select_face_by_center(obj, predicate):
    bpy.context.view_layer.objects.active = obj
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = predicate(f.calc_center_median())
    bm.to_mesh(obj.data); bm.free(); obj.data.update()


def mesh_metrics(obj) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new(); bm.from_mesh(mesh)
        try:
            valence = {}
            for v in bm.verts:
                valence[len(v.link_edges)] = valence.get(len(v.link_edges), 0) + 1
            face_sizes = [len(f.verts) for f in bm.faces]
            angles = sorted(
                (
                    math.degrees(e.link_faces[0].normal.angle(e.link_faces[1].normal))
                    for e in bm.edges if len(e.link_faces) == 2
                ),
                reverse=True,
            )
            return {
                "vertices": len(bm.verts),
                "faces": len(bm.faces),
                "quads": sum(1 for s in face_sizes if s == 4),
                "triangles": sum(1 for s in face_sizes if s == 3),
                "ngons": sum(1 for s in face_sizes if s > 4),
                "non_manifold_edges": sum(not e.is_manifold for e in bm.edges),
                "valence_distribution": valence,
                "five_plus_poles": sum(c for v, c in valence.items() if v >= 5),
                "max_dihedral_degrees": angles[0] if angles else None,
                "median_dihedral_degrees": angles[len(angles) // 2] if angles else None,
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def apply_modifier(obj, modifier_name):
    with bpy.context.temp_override(object=obj, active_object=obj, selected_editable_objects=[obj]):
        bpy.ops.object.modifier_apply(modifier=modifier_name)


def add_subsurf(obj, levels=2):
    m = obj.modifiers.new("Subdivision", "SUBSURF")
    m.levels = levels; m.render_levels = levels
    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    obj.data.update()


# ---------------------------------------------------------------------------
# Case A/B: flat panel, small local feature, direct extrude vs inset+extrude
# ---------------------------------------------------------------------------

def build_flat_small(report, output_dir, *, use_inset, label):
    clear_scene()
    panel = flat_panel("FlatPanel", size=3.0, subdivisions=6)
    # target one interior face near the center for a small local feature
    select_face_by_center(panel, lambda c: abs(c.x) < 0.3 and abs(c.y) < 0.3)
    bm = bmesh.new(); bm.from_mesh(panel.data)
    bm.faces.ensure_lookup_table()
    selected = [f for f in bm.faces if f.select]
    if use_inset:
        ret = bmesh.ops.inset_region(bm, faces=selected, thickness=0.08, depth=0.0, use_boundary=True, use_even_offset=True)
        extrude_target = selected  # inset keeps originals as the extrude target, matching this project's own inset_selection
    else:
        extrude_target = selected
    # compute average normal before extrude (this project's own extrude_selection correction)
    from mathutils import Vector
    avg_normal = Vector((0.0, 0.0, 0.0))
    for f in extrude_target:
        avg_normal += f.normal
    ext = bmesh.ops.extrude_face_region(bm, geom=extrude_target)
    new_verts = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    if avg_normal.length > 1e-9:
        avg_normal.normalize()
        bmesh.ops.translate(bm, verts=new_verts, vec=avg_normal * 0.4)
    bmesh.ops.delete(bm, geom=[f for f in extrude_target if f.is_valid], context="FACES")
    bm.normal_update()
    bm.to_mesh(panel.data); bm.free(); panel.data.update()

    add_subsurf(panel, levels=2)
    report[label] = mesh_metrics(panel)
    blend_path = output_dir / f"{label}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report[label]["blend_path"] = str(blend_path)


# ---------------------------------------------------------------------------
# Case C/D: curved cylinder body, larger attached form, direct vs inset+extrude
# ---------------------------------------------------------------------------

def build_curved_large(report, output_dir, *, use_inset, label):
    clear_scene()
    # 3 height bands (2 implicit loop cuts), matching the live-validated spout-growth
    # construction exactly -- so the target is a properly proportioned mid-band cell,
    # not an elongated whole-height strip.
    body = open_capped_cylinder("CurvedBody", radius=1.0, far=-2.5, near=1.3, segments=16, bands=3)
    bm = bmesh.new(); bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    # the mid band's faces all span z in [-0.833, 0.433]; pick the one nearest +X (front)
    mid_faces = [f for f in bm.faces if len(f.verts) == 4 and -1.0 < f.calc_center_median().z < 0.6]
    target = max(mid_faces, key=lambda f: f.calc_center_median().x)
    target.select = True
    bm.to_mesh(body.data); bm.free(); body.data.update()

    bm = bmesh.new(); bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    selected = [f for f in bm.faces if f.select]
    from mathutils import Vector
    if use_inset:
        # thickness scaled to the actual selected face's own size (live-validated approach:
        # checked face dimensions before choosing thickness, not a fixed guess)
        face_dims = selected[0].calc_area() ** 0.5
        ret = bmesh.ops.inset_region(bm, faces=selected, thickness=face_dims * 0.15, depth=0.0, use_boundary=True, use_even_offset=True)
        extrude_target = selected
    else:
        extrude_target = selected
    avg_normal = Vector((0.0, 0.0, 0.0))
    for f in extrude_target:
        avg_normal += f.normal
    ext = bmesh.ops.extrude_face_region(bm, geom=extrude_target)
    new_verts = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    if avg_normal.length > 1e-9:
        avg_normal.normalize()
        bmesh.ops.translate(bm, verts=new_verts, vec=avg_normal * 0.8)
    bmesh.ops.delete(bm, geom=[f for f in extrude_target if f.is_valid], context="FACES")
    bm.normal_update()
    bm.to_mesh(body.data); bm.free(); body.data.update()

    add_subsurf(body, levels=2)
    report[label] = mesh_metrics(body)
    blend_path = output_dir / f"{label}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report[label]["blend_path"] = str(blend_path)


def main() -> None:
    output_dir = output_directory()
    report = {
        "question": (
            "Does inset-before-extrude measurably reduce pole burden and surface distortion, "
            "and does that benefit hold across both flat/curved surfaces and small/large features, "
            "or is it conditional?"
        ),
    }

    build_flat_small(report, output_dir, use_inset=False, label="flat_small_direct")
    build_flat_small(report, output_dir, use_inset=True, label="flat_small_inset")
    build_curved_large(report, output_dir, use_inset=False, label="curved_large_direct")
    build_curved_large(report, output_dir, use_inset=True, label="curved_large_inset")

    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote report: {report_path}")


if __name__ == "__main__":
    main()
