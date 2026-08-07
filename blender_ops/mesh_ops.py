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
import mathutils

import bmesh_io
import persistent_ids


def _bm_from_object(name):
    """CORRECTION (found live during the mug-handle fix, and again auditing
    against the master directive's Edit Mode truth requirement): reading via
    bmesh.new()+from_mesh() unconditionally broke outright when the object
    turned out to be in Edit Mode (bm.to_mesh() raised "Mesh is in
    editmode"). Routes through bmesh_io, which picks the correct mode-aware
    API instead of assuming Object Mode."""
    obj = bpy.data.objects[name]
    bm = bmesh_io.read_bmesh(obj)
    persistent_ids.ensure_layers(bm)
    return obj, bm


def _write_back(obj, bm):
    bmesh_io.write_bmesh(obj, bm)


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


def select_by_ids(name, vertex_ids=None, edge_ids=None, face_ids=None, extend=False):
    """Select mesh elements by their persistent agent_id, resolved to
    current indices at call time -- so the caller can remember 'the tip
    vertex, agent_id 3012' across unrelated topology changes elsewhere in
    the mesh, instead of a raw index that may have renumbered. Set
    extend=True to add to the current selection instead of replacing it.
    Returns how many of each kind were actually found and selected."""
    obj, bm = _bm_from_object(name)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    if not extend:
        for seq in (bm.verts, bm.edges, bm.faces):
            for elem in seq:
                elem.select = False

    id_maps = persistent_ids.get_id_maps(name)
    counts = {"verts": 0, "edges": 0, "faces": 0}
    for kind, ids, seq in (
        ("verts", vertex_ids, bm.verts),
        ("edges", edge_ids, bm.edges),
        ("faces", face_ids, bm.faces),
    ):
        if not ids:
            continue
        id_to_index = id_maps[kind]["id_to_index"]
        for agent_id in ids:
            idx = id_to_index.get(agent_id)
            if idx is not None:
                seq[idx].select = True
                counts[kind] += 1
    bm.select_flush(True)
    _write_back(obj, bm)
    return counts


def subdivide_selection(name, cuts=2):
    """Subdivide the currently selected faces (or edges) into a denser
    grid -- the general loop-cut/subdivide member of the typed vocabulary,
    adding resolution for later sculpting without deciding any shape
    itself. Leaves the new interior faces selected, matching the
    extrude/inset convention.

    Verified bmesh.ops.subdivide_edges' actual return shape directly rather
    than assumed: geom_inner is the strictly-new interior geometry,
    geom_split is verts/edges created by splitting the original boundary
    edges (the cut points) -- both are genuinely new and need their
    persistent IDs cleared; the ORIGINAL boundary verts/edges (not in
    either set) correctly keep their existing IDs, same reuse pattern as
    inset."""
    obj, bm = _bm_from_object(name)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]
    if selected_faces:
        edges = list({e for f in selected_faces for e in f.edges})
    else:
        edges = [e for e in bm.edges if e.select]
        if not edges:
            _write_back(obj, bm)
            raise ValueError(f"no faces or edges selected on '{name}' to subdivide")

    ret = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True)
    new_geom = list({*ret["geom_inner"], *ret["geom_split"]})
    new_verts = [g for g in new_geom if isinstance(g, bmesh.types.BMVert)]
    new_edges = [g for g in new_geom if isinstance(g, bmesh.types.BMEdge)]
    new_faces = [g for g in ret["geom_inner"] if isinstance(g, bmesh.types.BMFace)]
    persistent_ids.clear_ids_in_open_bmesh(bm, verts=new_verts, edges=new_edges, faces=new_faces)

    for seq in (bm.verts, bm.edges, bm.faces):
        for elem in seq:
            elem.select = False
    for f in new_faces:
        f.select = True
    bm.select_flush(True)

    _write_back(obj, bm)
    return {"new_verts": len(new_verts), "new_faces": len(new_faces)}


def inset_selection(name, thickness=0.05, depth=0.0):
    """Inset the currently selected faces by `thickness`, optionally pushed
    in/out along their normal by `depth`. Leaves the shrunk original faces
    selected (matching Blender's own Inset Faces tool -- the new inner
    faces stay selected so a follow-up extrude/move can chain off them),
    not the new ring faces.

    Unlike extrude_face_region (see extrude_selection's docstring),
    inset_region does NOT abandon the original face -- confirmed directly
    against a bare cube: the original face object stays valid and keeps
    its own persistent ID (correct, it genuinely is "the same face,
    resized"), and its own boundary verts are moved inward and reused
    (also correctly keeping their IDs), not duplicated. The elements that
    ARE genuinely new are the ring faces returned by the operator plus a
    duplicate outer-boundary vert/edge for each original one -- those
    need clear_ids_in_open_bmesh, computed as "everything touched by the
    ring MINUS whatever the original selected faces still legitimately
    own" so this doesn't wipe out correct pre-existing IDs on the reused
    inner boundary."""
    obj, bm = _bm_from_object(name)
    bm.faces.ensure_lookup_table()
    selected_faces = [f for f in bm.faces if f.select]
    if not selected_faces:
        _write_back(obj, bm)
        raise ValueError(f"no faces selected on '{name}' to inset")

    reused_verts = {v for f in selected_faces for v in f.verts}
    reused_edges = {e for f in selected_faces for e in f.edges}

    ret = bmesh.ops.inset_region(
        bm, faces=selected_faces, thickness=thickness, depth=depth,
        use_boundary=True, use_even_offset=True,
    )
    ring_faces = ret["faces"]
    ring_verts = {v for f in ring_faces for v in f.verts} - reused_verts
    ring_edges = {e for f in ring_faces for e in f.edges} - reused_edges
    persistent_ids.clear_ids_in_open_bmesh(bm, verts=ring_verts, edges=ring_edges, faces=ring_faces)

    for seq in (bm.verts, bm.edges, bm.faces):
        for elem in seq:
            elem.select = False
    for f in selected_faces:
        if f.is_valid:
            f.select = True
    for v in reused_verts:
        if v.is_valid:
            v.select = True
    bm.select_flush(True)

    _write_back(obj, bm)
    return len(selected_faces)


def extrude_selection(name, offset=0.1):
    """Extrude whatever is currently selected (faces preferred, falling back
    to a pure edge selection) along its average normal by `offset`. Pair with
    a selection command first -- this acts on selection state, it doesn't
    choose what to extrude. Returns the number of new vertices.

    CORRECTION (found live, testing this against a fresh cube, two separate
    real bugs -- not one): (1) the extrude direction must be captured BEFORE
    calling bmesh.ops.extrude_face_region, not after. That operation reuses
    the ORIGINAL face objects as the interior "back wall" of the extrusion
    and flips their winding in the process -- reading .normal on them
    afterward silently returns the flipped (inward) direction, which pushed
    the new cap into the solid instead of out of it. (2) Even with the
    direction fixed, bmesh.ops.extrude_face_region does NOT delete/consume
    the original selected face -- confirmed directly: it stays valid and is
    absent from the operator's own returned "new geometry" list. Left in
    place, it becomes a stale duplicate sharing the original boundary edges
    with the new side walls, producing non-manifold edges (3 faces per
    edge instead of 2). Fix: explicitly delete the original faces (not
    anything from the operator's return value) after extruding+translating.
    Verified against a fresh cube both ways: non-manifold-edges went 4 (bad
    direction) -> still 4 (right direction, stale face left) -> 0 (stale
    face explicitly deleted), with the expected face count (10, not 11) and
    zero degenerate faces."""
    obj, bm = _bm_from_object(name)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]
    if selected_faces:
        normal = mathutils.Vector((0.0, 0.0, 0.0))
        for f in selected_faces:
            normal += f.normal
        ret = bmesh.ops.extrude_face_region(bm, geom=selected_faces)
        new_verts = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
        new_edges = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMEdge)]
        new_faces = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMFace)]
        persistent_ids.clear_ids_in_open_bmesh(bm, verts=new_verts, edges=new_edges, faces=new_faces)
        bmesh.ops.delete(bm, geom=[f for f in selected_faces if f.is_valid], context='FACES')
    else:
        selected_edges = [e for e in bm.edges if e.select]
        if not selected_edges:
            _write_back(obj, bm)
            raise ValueError(f"no faces or edges selected on '{name}' to extrude")
        normal = mathutils.Vector((0.0, 0.0, 0.0))
        seen_verts = set()
        for e in selected_edges:
            for v in e.verts:
                if v.index not in seen_verts:
                    seen_verts.add(v.index)
                    normal += v.normal
        ret = bmesh.ops.extrude_edge_only(bm, edges=selected_edges)
        new_verts = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
        new_edges = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMEdge)]
        new_faces = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMFace)]
        persistent_ids.clear_ids_in_open_bmesh(bm, verts=new_verts, edges=new_edges, faces=new_faces)

    if normal.length > 1e-9:
        normal.normalize()
        bmesh.ops.translate(bm, verts=new_verts, vec=normal * offset)

    # Leave the NEW geometry selected and deselect everything else, matching
    # ordinary Extrude behavior everywhere else in Blender -- found live that
    # without this, the original (untouched) boundary loop stayed selected
    # after extrude, so a follow-up move/scale silently acted on old
    # geometry instead of the thing that was just created.
    for seq in (bm.verts, bm.edges, bm.faces):
        for elem in seq:
            elem.select = False
    for v in new_verts:
        v.select = True
    for f in new_faces:
        f.select = True
    bm.select_flush(True)

    _write_back(obj, bm)
    return len(new_verts)


def move_selection(name, delta):
    """Translate the currently selected vertices by delta=(dx, dy, dz)."""
    obj, bm = _bm_from_object(name)
    bm.verts.ensure_lookup_table()
    selected_verts = [v for v in bm.verts if v.select]
    if not selected_verts:
        _write_back(obj, bm)
        raise ValueError(f"no vertices selected on '{name}' to move")
    bmesh.ops.translate(bm, verts=selected_verts, vec=delta)
    _write_back(obj, bm)
    return len(selected_verts)


def scale_selection(name, factor, center=None):
    """Scale the currently selected vertices by factor=(sx, sy, sz) about
    center (defaults to the median point of the selection, not the object
    origin, so scaling a local detail doesn't drag it toward the origin)."""
    obj, bm = _bm_from_object(name)
    bm.verts.ensure_lookup_table()
    selected_verts = [v for v in bm.verts if v.select]
    if not selected_verts:
        _write_back(obj, bm)
        raise ValueError(f"no vertices selected on '{name}' to scale")
    if center is None:
        c = mathutils.Vector((0.0, 0.0, 0.0))
        for v in selected_verts:
            c += v.co
        c /= len(selected_verts)
    else:
        c = mathutils.Vector(center)
    bmesh.ops.scale(bm, verts=selected_verts, vec=factor, space=mathutils.Matrix.Translation(-c))
    _write_back(obj, bm)
    return len(selected_verts)
