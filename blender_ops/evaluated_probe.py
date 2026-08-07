"""Inspect the modifier-EVALUATED mesh, not the base control cage.

Every existing state_probe.py function reads obj.data directly -- the base
mesh, before any modifier stack runs. That was fine for every prop built so
far (Bottle/Flashlight/Mug/SpeakerEnclosure), none of which used a modifier
that changes the visible surface. It stops being fine the moment a
Subdivision Surface modifier enters the picture: the control cage and the
actual smoothed result are different meshes with different vertex/face
counts, and the topology problems that actually matter for subdivision
work (pinching, curvature discontinuity) only exist in the EVALUATED
result, invisible to every tool built before this one.

Uses bpy's own dependency graph (the same evaluation Blender's viewport
uses), not a reimplementation of Catmull-Clark or any other subdivision
algorithm -- so this reports exactly what the modifier stack actually
produces, not an approximation of it.
"""

import bpy
import bmesh


def _read_evaluated_bmesh(obj):
    """Returns (bm, cleanup_fn). Caller must call cleanup_fn() when done --
    the evaluated mesh is a temporary datablock that must be explicitly
    freed (to_mesh_clear()), unlike obj.data which Blender owns."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh_eval)

    def cleanup():
        bm.free()
        obj_eval.to_mesh_clear()

    return bm, cleanup


def evaluated_mesh_health(name):
    """Same shape as state_probe.mesh_health(), but on the evaluated
    (post-modifier) mesh -- what the surface actually looks like, not the
    control cage that produces it."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        return {
            "vertices": len(bm.verts),
            "edges": len(bm.edges),
            "faces": len(bm.faces),
            "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
            "ngons": sum(1 for f in bm.faces if len(f.verts) > 4),
            "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
            "degenerate_faces": sum(1 for f in bm.faces if f.calc_area() < 1e-8),
        }
    finally:
        cleanup()


def evaluated_valence_distribution(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        bm.verts.ensure_lookup_table()
        dist = {}
        for v in bm.verts:
            val = len(v.link_edges)
            dist[val] = dist.get(val, 0) + 1
        return dist
    finally:
        cleanup()


def evaluated_surface_quality(name):
    """Signals aimed specifically at spotting subdivision pinching, which
    doesn't show up as a validity failure (still 0 non-manifold, 0
    degenerate) -- it shows up as an unusually tight CLUSTER of very small,
    similarly-angled faces where the surface should be flowing smoothly.

    face_area_ratio alone (already used for hard-surface work) is a weak
    signal here since subdivided surfaces naturally have many small faces
    everywhere, not just at defects -- what's diagnostic for pinching is
    the presence of a face-area OUTLIER cluster (a few faces far smaller
    than the local median, not just smaller than the global max), and
    sharp normal-angle changes between adjacent faces in a region that's
    supposed to be a smooth continuous surface. Reports both rather than
    just the same min/max ratio already available elsewhere.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        bm.faces.ensure_lookup_table()
        areas = [f.calc_area() for f in bm.faces]
        areas_nonzero = sorted(a for a in areas if a > 1e-9)
        if not areas_nonzero:
            return {"error": "no non-degenerate faces on evaluated mesh"}
        median = areas_nonzero[len(areas_nonzero) // 2]
        outliers = [a for a in areas_nonzero if median > 1e-9 and a < median * 0.05]

        max_angle = 0.0
        angle_samples = 0
        for e in bm.edges:
            if len(e.link_faces) == 2:
                angle = e.calc_face_angle(0.0)
                max_angle = max(max_angle, angle)
                angle_samples += 1

        return {
            "face_count": len(areas),
            "min_area": round(min(areas_nonzero), 8),
            "max_area": round(max(areas_nonzero), 6),
            "median_area": round(median, 6),
            "area_outlier_count": len(outliers),
            "area_outlier_ratio": round(len(outliers) / len(areas_nonzero), 4) if areas_nonzero else 0,
            "max_adjacent_face_angle_radians": round(max_angle, 4),
            "angle_samples": angle_samples,
        }
    finally:
        cleanup()
