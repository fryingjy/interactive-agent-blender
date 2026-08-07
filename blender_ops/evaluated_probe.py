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


def bounding_box_comparison(name):
    """Compare the base control cage's own bounding box to the modifier-
    evaluated result's bounding box, in local space.

    Exists for a specific, real judgment a plain area/angle check can't
    make: Catmull-Clark subdivision without support loops near a corner
    pulls the evaluated surface inward from that corner (the well-known
    "beach ball" shrinkage), which can quietly erode the intended silhouette
    proportions even when every other validity/pinching signal reads clean
    -- 0 non-manifold, 0 area outliers, a moderate max adjacent-face angle
    can all still coexist with a shape that's noticeably smaller/rounder
    than the control cage that was supposedly built to spec. shrinkage_ratio
    close to 1.0 on an axis means that axis's extent survived subdivision
    intact; a low ratio (e.g. under ~0.9) on an axis that's supposed to read
    as a firm silhouette edge is the concrete, local signal a support loop
    is missing there -- not just a vague "does this look rounded enough"
    impression.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}

    base_coords = [v.co for v in obj.data.vertices]
    if not base_coords:
        return {"error": f"'{name}' has no vertices"}
    base_min = [min(c[i] for c in base_coords) for i in range(3)]
    base_max = [max(c[i] for c in base_coords) for i in range(3)]

    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        eval_coords = [v.co for v in bm.verts]
        if not eval_coords:
            return {"error": "evaluated mesh has no vertices"}
        eval_min = [min(c[i] for c in eval_coords) for i in range(3)]
        eval_max = [max(c[i] for c in eval_coords) for i in range(3)]
    finally:
        cleanup()

    base_dims = [base_max[i] - base_min[i] for i in range(3)]
    eval_dims = [eval_max[i] - eval_min[i] for i in range(3)]
    shrinkage_ratio = [
        round(eval_dims[i] / base_dims[i], 4) if base_dims[i] > 1e-9 else None
        for i in range(3)
    ]

    return {
        "base_dimensions": [round(d, 4) for d in base_dims],
        "evaluated_dimensions": [round(d, 4) for d in eval_dims],
        "shrinkage_ratio_xyz": shrinkage_ratio,
        "base_bounds": {"min": [round(c, 4) for c in base_min], "max": [round(c, 4) for c in base_max]},
        "evaluated_bounds": {"min": [round(c, 4) for c in eval_min], "max": [round(c, 4) for c in eval_max]},
    }
