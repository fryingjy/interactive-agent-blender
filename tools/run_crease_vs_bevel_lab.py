"""REPRODUCE + partial VALIDATE step for docs/BLEND_FILE_STUDY_PROTOCOL.md,
testing a principle extracted from studying battle axe.blend: full edge
crease (value 1.0) on a SubD cage protects that edge from the modifier's
smoothing without adding any new geometry, which is a genuinely different
mechanism from Bevel (which adds a physical radius/chamfer as new geometry).
The axe file uses crease-only for every sharp edge in all 5 of its objects
and zero Bevel modifiers anywhere.

Three variants of the same base cage (a box with one raised nub, chosen to
have both a flat-panel body and a feature that should round smoothly, like
the axe pommel's body-plus-taper pattern) test this directly:

  A. No crease, no Bevel, SubD only -> negative control: the whole shape
     should round into a blob, including the edges we want to stay sharp.
  B. Crease the box's outer edges (protect them), leave the nub's edges
     uncreased, SubD -> the technique under test: box should stay sharp/
     flat, nub should still round.
  C. Bevel-weight the SAME outer edges instead of creasing, Bevel modifier
     + SubD -> comparison: does this look different, and does it cost
     anything (extra modifier, extra evaluated geometry) that crease
     doesn't?

Verifies each variant's evaluated mesh is clean, and reports the evaluated
vertex count so the "crease adds no geometry" claim is checked, not assumed.
"""
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
import object_ops  # noqa: E402
import persistent_ids  # noqa: E402
from render_passes import render_silhouette  # noqa: E402


def args():
    vals = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(vals) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    out = Path(vals[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    return out


def build_box_with_nub(name):
    """SIMPLIFIED after independent verification caught real non-manifold
    geometry from an inset_individual + extrude_face_region combination
    (a duplicate-face bug in that construction, not a property of crease
    vs. bevel -- confirmed because both A and B shared the identical base
    topology and both showed the same defect). A plain rectangular box,
    taller in Z than X/Y, tests the same principle with no bmesh operator
    edge cases: crease/bevel only the 4 vertical edges (protect them),
    leave the 8 horizontal top/bottom edges uncreased so they round under
    SubD -- if the vertical edges stay sharp while top/bottom corners round
    into a pillar-like profile, the technique works, with a topologically
    trivial, independently-verifiable base mesh."""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (0.6, 0.6, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    return obj


def vertical_edge_ids(obj_name):
    """The 4 edges connecting the bottom face (z=-0.5) to the top face
    (z=0.5) -- both endpoints share the same x,y but differ in z."""
    obj = bpy.data.objects[obj_name]
    persistent_ids.ensure_persistent_ids(obj_name)
    index_to_id = persistent_ids.get_id_maps(obj_name)["edges"]["index_to_id"]
    ids = []
    for edge in obj.data.edges:
        v0, v1 = obj.data.vertices[edge.vertices[0]], obj.data.vertices[edge.vertices[1]]
        same_xy = abs(v0.co.x - v1.co.x) < 1e-6 and abs(v0.co.y - v1.co.y) < 1e-6
        diff_z = abs(v0.co.z - v1.co.z) > 1e-6
        if same_xy and diff_z:
            ids.append(index_to_id[edge.index])
    return ids



def evaluated_stats(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    verts, faces = len(bm.verts), len(bm.faces)
    bm.free()
    ev.to_mesh_clear()
    return {"evaluated_vertices": verts, "evaluated_faces": faces,
            "non_manifold_edges": non_manifold, "degenerate_faces": degenerate}


def main():
    out = args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bpy.context.scene.world = world
    col = bpy.context.scene.collection

    mat = bpy.data.materials.new("Lab Steel")
    mat.use_nodes = True
    mat.diffuse_color = (0.5, 0.5, 0.55, 1)

    report = {}

    # A: no crease, no bevel, SubD only
    a = build_box_with_nub("A_NoProtection")
    a.data.materials.append(mat)
    a.location.x = -2.5
    subd_a = a.modifiers.new("Subdivision", "SUBSURF")
    subd_a.levels = 2
    subd_a.render_levels = 2
    report["A_NoProtection"] = evaluated_stats(a)
    base_a = {"base_vertices": len(a.data.vertices), "base_faces": len(a.data.polygons)}
    report["A_NoProtection"].update(base_a)

    # B: crease outer box edges (technique under test), SubD
    b = build_box_with_nub("B_CreaseProtected")
    b.data.materials.append(mat)
    b.location.x = 0
    outer_ids = vertical_edge_ids("B_CreaseProtected")
    # object_ops.set_bevel_weight_by_ids only writes the "bevel_weight_edge"
    # attribute; crease uses its own "crease_edge" attribute, which
    # object_ops does not yet expose -- a real gap this experiment
    # demonstrates (see STORE step: this needs its own typed function before
    # this technique can be sanctioned for real construction scripts).
    persistent_ids.ensure_persistent_ids("B_CreaseProtected")
    id_map = persistent_ids.get_id_maps("B_CreaseProtected")["edges"]["id_to_index"]
    crease_attr = b.data.attributes.get("crease_edge")
    if crease_attr is None:
        crease_attr = b.data.attributes.new("crease_edge", "FLOAT", "EDGE")
    for edge_id in outer_ids:
        crease_attr.data[id_map[edge_id]].value = 1.0
    subd_b = b.modifiers.new("Subdivision", "SUBSURF")
    subd_b.levels = 2
    subd_b.render_levels = 2
    report["B_CreaseProtected"] = evaluated_stats(b)
    report["B_CreaseProtected"].update({"base_vertices": len(b.data.vertices), "base_faces": len(b.data.polygons),
                                         "creased_edge_count": len(outer_ids)})

    # C: bevel-weight the same outer edges instead, Bevel + SubD
    c = build_box_with_nub("C_BevelProtected")
    c.data.materials.append(mat)
    c.location.x = 2.5
    outer_ids_c = vertical_edge_ids("C_BevelProtected")
    object_ops.set_bevel_weight_by_ids("C_BevelProtected", outer_ids_c, weight=1.0)
    bevel_c = c.modifiers.new("Bevel", "BEVEL")
    bevel_c.limit_method = "WEIGHT"
    bevel_c.width = 0.03
    bevel_c.segments = 2
    subd_c = c.modifiers.new("Subdivision", "SUBSURF")
    subd_c.levels = 2
    subd_c.render_levels = 2
    report["C_BevelProtected"] = evaluated_stats(c)
    report["C_BevelProtected"].update({"base_vertices": len(c.data.vertices), "base_faces": len(c.data.polygons),
                                        "weighted_edge_count": len(outer_ids_c)})

    # D: FOLLOW-UP after seeing B's result -- B's flat side faces visibly
    # "pillowed" (bulged outward) despite the boundary edge itself staying
    # sharp. Hypothesis: crease only protects the EDGE, not the FACE: a
    # single quad face with no internal support has nothing to stop SubD
    # inflating its center. Same crease technique, but each side face is
    # pre-subdivided (plain, non-modifier subdivide) into a 3x3 grid before
    # the SubD modifier + crease are applied, giving the face internal
    # support the way the axe file's much denser cages (100-1000+ verts,
    # not 8) implicitly do.
    d = build_box_with_nub("D_CreaseWithSupport")
    d.data.materials.append(mat)
    d.location.x = 5.0
    bpy.context.view_layer.objects.active = d
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=2)
    bpy.ops.object.mode_set(mode="OBJECT")
    outer_ids_d = vertical_edge_ids("D_CreaseWithSupport")
    crease_set_result = object_ops.set_edge_crease_by_ids("D_CreaseWithSupport", outer_ids_d, value=1.0)
    subd_d = d.modifiers.new("Subdivision", "SUBSURF")
    subd_d.levels = 1
    subd_d.render_levels = 1
    smooth_result_d = object_ops.set_smooth_by_angle("D_CreaseWithSupport")
    audit_d = object_ops.hard_surface_shading_audit("D_CreaseWithSupport")
    report["D_CreaseWithSupport"] = evaluated_stats(d)
    report["D_CreaseWithSupport"].update({
        "base_vertices": len(d.data.vertices), "base_faces": len(d.data.polygons),
        "creased_edge_count": len(outer_ids_d),
        "crease_set_result": crease_set_result,
        "hard_surface_shading_audit": audit_d,
    })

    for obj in (a, b, c, d):
        for p in obj.data.polygons:
            p.use_smooth = True

    all_names = [a.name, b.name, c.name, d.name]
    masks = {}
    for view in ("front", "iso"):
        mask_path = out / f"compare_{view}.png"
        result = render_silhouette(all_names, str(mask_path), view=("isometric" if view == "iso" else view), resolution=900)
        masks[view] = str(mask_path)

    bpy.ops.wm.save_as_mainfile(filepath=str(out / "crease_vs_bevel_lab.blend"))

    report["masks"] = masks
    (out / "report.json").write_text(__import__("json").dumps(report, indent=2))
    print(__import__("json").dumps(report, indent=2))


if __name__ == "__main__":
    main()
