"""Mechanical mesh helpers callable directly by the agent -- NOT a library of
asset-specific shape generators.

ALLOWED to call directly, any number of times: inspection, verification,
saving, object naming, modifier configuration, selection helpers, repair
primitives, mechanical cleanup (merge-by-distance, recalc normals,
triangulate stray n-gons, bevel a selection the agent already chose).

NOT ALLOWED: calling any of these in an unsupervised loop whose parameters
are derived from a formula (e.g. `[f(i) for i in range(N)]`) to stamp
detailing across a whole prop in one shot -- that is procedural asset
generation wearing this module's clothes, the exact failure mode this
project restarted to get away from. A helper like add_ring_detail() may
still be called many times, but each call's location/parameters must come
from the agent inspecting the current mesh and deciding that specific
instance, not from an algorithm generating the whole set in advance. The
artistic form has to come from the agent's own iterative decisions, not
from this module.
"""

import bmesh
import bpy


def _bm_from_object(name):
    obj = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    return obj, bm


def _write_back(obj, bm):
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def merge_by_distance(name, dist=0.0001):
    obj, bm = _bm_from_object(name)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    _write_back(obj, bm)


def recalc_normals(name):
    obj, bm = _bm_from_object(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _write_back(obj, bm)


def triangulate_ngons(name):
    obj, bm = _bm_from_object(name)
    bm.faces.ensure_lookup_table()
    ngon_faces = [f for f in bm.faces if len(f.verts) > 4]
    if ngon_faces:
        bmesh.ops.triangulate(bm, faces=ngon_faces)
    _write_back(obj, bm)


def bevel_edges(name, edge_indices, offset=0.02, segments=2):
    obj, bm = _bm_from_object(name)
    bm.edges.ensure_lookup_table()
    edges = [bm.edges[i] for i in edge_indices if i < len(bm.edges)]
    bmesh.ops.bevel(bm, geom=edges, offset=offset, segments=segments, affect="EDGES")
    _write_back(obj, bm)


def add_ring_detail(name, z, radial_offset=0.03):
    """Bisect the mesh at a horizontal plane and push the resulting new ring
    of vertices radially in/out by radial_offset, forming a grip-ridge or
    decorative groove ring. Returns the number of new vertices added.

    Each call's z/radial_offset must be a specific decision the agent made
    by looking at this object's current state -- never call this in a loop
    whose z-values come from a formula (`start + i * step`); that turns one
    mechanical helper into a procedural ring-stamping generator, which is
    exactly the shape-authoring this module is not supposed to do. See the
    module docstring.
    """
    obj, bm = _bm_from_object(name)
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    result = bmesh.ops.bisect_plane(
        bm, geom=geom, dist=1e-4,
        plane_co=(0, 0, z), plane_no=(0, 0, 1),
        clear_inner=False, clear_outer=False,
    )
    new_verts = [g for g in result["geom_cut"] if isinstance(g, bmesh.types.BMVert)]
    for v in new_verts:
        x, y = v.co.x, v.co.y
        d = (x ** 2 + y ** 2) ** 0.5
        if d > 1e-6:
            v.co.x += (x / d) * radial_offset
            v.co.y += (y / d) * radial_offset
    _write_back(obj, bm)
    return len(new_verts)
