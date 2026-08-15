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

try:
    from . import bmesh_io, persistent_ids
except ImportError:
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


def _element_snapshot(bm):
    return set(bm.verts), set(bm.edges), set(bm.faces)


def _clear_new_element_ids(bm, before):
    before_verts, before_edges, before_faces = before
    new_verts = [item for item in bm.verts if item not in before_verts]
    new_edges = [item for item in bm.edges if item not in before_edges]
    new_faces = [item for item in bm.faces if item not in before_faces]
    persistent_ids.clear_ids_in_open_bmesh(bm, verts=new_verts, edges=new_edges, faces=new_faces)
    return {"new_verts": len(new_verts), "new_edges": len(new_edges), "new_faces": len(new_faces)}


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
    # CORRECTION (found live building the watering-can body ring cage):
    # bm.select_flush(True) flushes UPWARD -- it selects any edge/face whose
    # every vertex happens to already be selected. Direct assignment above
    # already cascades DOWNWARD automatically (selecting an edge selects its
    # verts; a face its edges+verts), which is the only cascade needed for
    # bmesh validity. Flushing up silently over-selects: selecting all 16
    # vertical edges of a 16-gon cylinder touches all 32 verts (100% of the
    # mesh's verts, since each vert is exactly one vertical edge's endpoint),
    # and flush(True) then re-selected every OTHER edge/face too (48 edges,
    # 18 faces on a mesh that only has 48 edges / 18 faces total) because
    # each was fully bounded by already-selected verts -- even though none
    # of those other edges/faces were ever chosen by the caller. Confirmed
    # directly: without the flush call, selection stayed exactly 16 edges /
    # 0 faces, matching intent. No flush = no downward loss either, since
    # verts still cascade automatically per-element above.
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


def rotate_selection(name, angle, axis=(0.0, 0.0, 1.0), center=None):
    """Rotate selected vertices by radians around a local-space axis and selection median."""
    obj, bm = _bm_from_object(name)
    selected = [vert for vert in bm.verts if vert.select]
    if not selected:
        _write_back(obj, bm)
        raise ValueError(f"no vertices selected on '{name}' to rotate")
    pivot = mathutils.Vector(center) if center is not None else sum((v.co for v in selected), mathutils.Vector()) / len(selected)
    axis_vector = mathutils.Vector(axis)
    if axis_vector.length < 1e-9:
        _write_back(obj, bm)
        raise ValueError("rotation axis must be nonzero")
    matrix = mathutils.Matrix.Rotation(angle, 4, axis_vector.normalized())
    bmesh.ops.rotate(bm, verts=selected, cent=pivot, matrix=matrix)
    _write_back(obj, bm)
    return len(selected)


def bevel_selection(name, offset=0.02, segments=2, offset_type="OFFSET", profile=0.5, clamp_overlap=False):
    """Bevel selected edges with explicit width semantics and overlap policy."""
    obj, bm = _bm_from_object(name)
    selected = [edge for edge in bm.edges if edge.select]
    if not selected:
        _write_back(obj, bm)
        raise ValueError(f"no edges selected on '{name}' to bevel")
    before = _element_snapshot(bm)
    bmesh.ops.bevel(
        bm,
        geom=selected,
        offset=offset,
        offset_type=offset_type,
        segments=segments,
        profile=profile,
        affect="EDGES",
        clamp_overlap=clamp_overlap,
    )
    created = _clear_new_element_ids(bm, before)
    _write_back(obj, bm)
    return {
        "selected_edges": len(selected),
        "offset": offset,
        "offset_type": offset_type,
        "segments": segments,
        "profile": profile,
        "clamp_overlap": clamp_overlap,
        **created,
    }


def delete_selection(name):
    """Delete selected faces first, otherwise selected edges, otherwise vertices."""
    obj, bm = _bm_from_object(name)
    faces = [face for face in bm.faces if face.select]
    edges = [edge for edge in bm.edges if edge.select]
    verts = [vert for vert in bm.verts if vert.select]
    if faces:
        bmesh.ops.delete(bm, geom=faces, context="FACES")
        domain, count = "faces", len(faces)
    elif edges:
        bmesh.ops.delete(bm, geom=edges, context="EDGES")
        domain, count = "edges", len(edges)
    elif verts:
        bmesh.ops.delete(bm, geom=verts, context="VERTS")
        domain, count = "verts", len(verts)
    else:
        _write_back(obj, bm)
        raise ValueError(f"nothing selected on '{name}' to delete")
    _write_back(obj, bm)
    return {"domain": domain, "deleted": count}


def dissolve_selection(name, use_verts=True):
    """Dissolve the most specific selected domain while preserving surrounding surface."""
    obj, bm = _bm_from_object(name)
    faces = [face for face in bm.faces if face.select]
    edges = [edge for edge in bm.edges if edge.select]
    verts = [vert for vert in bm.verts if vert.select]
    if faces:
        bmesh.ops.dissolve_faces(bm, faces=faces, use_verts=use_verts)
        domain, count = "faces", len(faces)
    elif edges:
        bmesh.ops.dissolve_edges(bm, edges=edges, use_verts=use_verts, use_face_split=False)
        domain, count = "edges", len(edges)
    elif verts:
        bmesh.ops.dissolve_verts(bm, verts=verts, use_face_split=False, use_boundary_tear=False)
        domain, count = "verts", len(verts)
    else:
        _write_back(obj, bm)
        raise ValueError(f"nothing selected on '{name}' to dissolve")
    _write_back(obj, bm)
    return {"domain": domain, "dissolved": count}


def merge_selection(name, center=None):
    """Merge selected vertices to an explicit point or their median."""
    obj, bm = _bm_from_object(name)
    verts = [vert for vert in bm.verts if vert.select]
    if len(verts) < 2:
        _write_back(obj, bm)
        raise ValueError(f"at least two vertices must be selected on '{name}' to merge")
    point = mathutils.Vector(center) if center is not None else sum((v.co for v in verts), mathutils.Vector()) / len(verts)
    bmesh.ops.pointmerge(bm, verts=verts, merge_co=point)
    _write_back(obj, bm)
    return {"merged_vertices": len(verts), "merge_point": list(point)}


def fill_selection(name):
    """Create faces from selected boundary edges/vertices using BMesh contextual creation."""
    obj, bm = _bm_from_object(name)
    edges = [edge for edge in bm.edges if edge.select]
    verts = [vert for vert in bm.verts if vert.select]
    if len(edges) < 3:
        _write_back(obj, bm)
        raise ValueError(f"at least three boundary edges must be selected on '{name}' to fill")
    result = bmesh.ops.contextual_create(bm, geom=list({*edges, *verts}))
    faces = [item for item in result.get("faces", []) if isinstance(item, bmesh.types.BMFace)]
    persistent_ids.clear_ids_in_open_bmesh(bm, faces=faces)
    _write_back(obj, bm)
    return {"created_faces": len(faces)}


def bridge_selection(name, use_merge=False, merge_factor=0.5, twist=0):
    """Bridge selected boundary edge loops with an intentional integer twist offset.

    ``twist`` maps to Blender's ``bmesh.ops.bridge_loops(..., twist_offset=...)``.
    It changes which target-loop vertex each source-loop vertex joins; it does not
    make incompatible loop counts or a poor attachment location production-safe.
    """
    if isinstance(twist, bool) or not isinstance(twist, int):
        raise ValueError("bridge twist must be an integer offset")
    obj, bm = _bm_from_object(name)
    edges = [edge for edge in bm.edges if edge.select and not edge.is_manifold]
    if len(edges) < 4:
        _write_back(obj, bm)
        raise ValueError(f"selected boundary edges on '{name}' do not form bridgeable loops")
    before = _element_snapshot(bm)
    bmesh.ops.bridge_loops(
        bm,
        edges=edges,
        use_pairs=False,
        use_cyclic=False,
        use_merge=use_merge,
        merge_factor=merge_factor,
        twist_offset=twist,
    )
    created = _clear_new_element_ids(bm, before)
    _write_back(obj, bm)
    return {"input_edges": len(edges), "twist": twist, "created_faces": created["new_faces"], **created}


def spin_selection(name, angle, steps, center=(0.0, 0.0, 0.0), axis=(0.0, 0.0, 1.0), use_duplicate=False):
    """Spin selected geometry around a local-space axis."""
    obj, bm = _bm_from_object(name)
    geom = [item for seq in (bm.verts, bm.edges, bm.faces) for item in seq if item.select]
    if not geom:
        _write_back(obj, bm)
        raise ValueError(f"nothing selected on '{name}' to spin")
    before = _element_snapshot(bm)
    result = bmesh.ops.spin(bm, geom=geom, cent=center, axis=axis, angle=angle, steps=steps, use_duplicate=use_duplicate)
    final_geometry = len(result.get("geom_last", []))
    created = _clear_new_element_ids(bm, before)
    _write_back(obj, bm)
    return {"steps": steps, "final_geometry": final_geometry, **created}


def loop_cut_selection(name, cuts=1):
    """Subdivide a selected edge ring as the typed loop-cut equivalent."""
    obj, bm = _bm_from_object(name)
    edges = [edge for edge in bm.edges if edge.select]
    if not edges:
        _write_back(obj, bm)
        raise ValueError(f"no edge ring selected on '{name}' to cut")
    selected = set(edges)
    invalid_faces = []
    for edge in edges:
        for face in edge.link_faces:
            selected_in_face = [candidate for candidate in face.edges if candidate in selected]
            opposite = (
                len(selected_in_face) == 2
                and not (set(selected_in_face[0].verts) & set(selected_in_face[1].verts))
            )
            if len(face.verts) != 4 or not opposite:
                invalid_faces.append(face)
    if invalid_faces:
        detail = {
            "selected_edges": len(edges),
            "invalid_adjacent_faces": len(set(invalid_faces)),
            "requirement": "every traversed face must be a quad containing exactly two opposite selected ring edges",
        }
        _write_back(obj, bm)
        raise ValueError(f"selection on '{name}' is not a continuous quad edge ring: {detail}")
    before = _element_snapshot(bm)
    bmesh.ops.subdivide_edgering(bm, edges=edges, cuts=cuts, profile_shape="SMOOTH", profile_shape_factor=0.0)
    created = _clear_new_element_ids(bm, before)
    _write_back(obj, bm)
    return {"cuts": cuts, "created_geometry": sum(created.values()), **created}


def bisect_selection(name, plane_co, plane_no, clear_inner=False, clear_outer=False, fill=False):
    """Knife/bisect selected geometry by a plane; optionally clear and cap one side."""
    obj, bm = _bm_from_object(name)
    geom = [item for seq in (bm.verts, bm.edges, bm.faces) for item in seq if item.select]
    if not geom:
        _write_back(obj, bm)
        raise ValueError(f"nothing selected on '{name}' to bisect")
    before = _element_snapshot(bm)
    result = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=plane_co, plane_no=plane_no, clear_inner=clear_inner, clear_outer=clear_outer)
    cut = result.get("geom_cut", [])
    filled_faces = []
    if fill:
        if not (clear_inner or clear_outer):
            _write_back(obj, bm)
            raise ValueError("bisect fill requires clear_inner or clear_outer so the cut is a boundary")
        cut_edges = [item for item in cut if isinstance(item, bmesh.types.BMEdge) and item.is_boundary]
        if not cut_edges:
            _write_back(obj, bm)
            raise ValueError(f"bisect on '{name}' produced no boundary loop to fill")
        fill_result = bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)
        filled_faces = list(fill_result.get("faces", []))
        if not filled_faces:
            _write_back(obj, bm)
            raise RuntimeError(f"bisect on '{name}' did not create a cap")
    created = _clear_new_element_ids(bm, before)
    _write_back(obj, bm)
    return {
        "cut_geometry": len(cut),
        "clear_inner": clear_inner,
        "clear_outer": clear_outer,
        "fill": fill,
        "filled_faces": len(filled_faces),
        **created,
    }


def symmetrize_selection(name, direction="-X_TO_+X", threshold=0.0001):
    """Mirror selected geometry across a principal local axis with weld tolerance."""
    obj, bm = _bm_from_object(name)
    geom = [item for seq in (bm.verts, bm.edges, bm.faces) for item in seq if item.select]
    if not geom:
        _write_back(obj, bm)
        raise ValueError(f"nothing selected on '{name}' to symmetrize")
    direction_map = {
        "-X_TO_+X": "-X", "+X_TO_-X": "X",
        "-Y_TO_+Y": "-Y", "+Y_TO_-Y": "Y",
        "-Z_TO_+Z": "-Z", "+Z_TO_-Z": "Z",
    }
    bmesh_direction = direction_map.get(direction, direction)
    before = _element_snapshot(bm)
    bmesh.ops.symmetrize(bm, input=geom, direction=bmesh_direction, dist=threshold)
    created = _clear_new_element_ids(bm, before)
    _write_back(obj, bm)
    return {"direction": direction, "bmesh_direction": bmesh_direction, "result_geometry": sum(created.values()), **created}


def split_selection(name):
    """Disconnect selected geometry in-place while keeping it in the same object."""
    obj, bm = _bm_from_object(name)
    geom = [item for seq in (bm.verts, bm.edges, bm.faces) for item in seq if item.select]
    if not geom:
        _write_back(obj, bm)
        raise ValueError(f"nothing selected on '{name}' to split")
    before = _element_snapshot(bm)
    result = bmesh.ops.split(bm, geom=geom, use_only_faces=False)
    result_geometry = len(result.get("geom", []))
    created = _clear_new_element_ids(bm, before)
    _write_back(obj, bm)
    return {"split_geometry": result_geometry, **created}


def assign_vertex_group(name, group_name, weight=1.0):
    """Create (if needed) a vertex group and assign the currently-selected vertices to it at
    the given weight. The missing piece for vertex-group-restricted modifiers (Shrinkwrap,
    Mirror, Bevel) -- those all take a vertex_group name, but nothing in the typed surface could
    previously create or populate one."""
    obj, bm = _bm_from_object(name)
    if group_name not in obj.vertex_groups:
        obj.vertex_groups.new(name=group_name)
    group_index = obj.vertex_groups[group_name].index
    deform_layer = bm.verts.layers.deform.verify()
    assigned = 0
    for vert in bm.verts:
        if vert.select:
            vert[deform_layer][group_index] = weight
            assigned += 1
    _write_back(obj, bm)
    if assigned == 0:
        raise ValueError(f"nothing selected on '{name}' to assign to vertex group '{group_name}'")
    return {"group_name": group_name, "group_index": group_index, "assigned_count": assigned, "weight": weight}


def separate_selection(name, new_name=None):
    """Move selected faces to a new object and report the identity boundary explicitly."""
    obj, bm = _bm_from_object(name)
    faces = [face for face in bm.faces if face.select]
    if not faces:
        _write_back(obj, bm)
        raise ValueError(f"no faces selected on '{name}' to separate")
    source_verts = sorted({vert for face in faces for vert in face.verts}, key=lambda vert: vert.index)
    index = {vert: i for i, vert in enumerate(source_verts)}
    vertices = [tuple(vert.co) for vert in source_verts]
    polygons = [[index[vert] for vert in face.verts] for face in faces]
    material_indices = [face.material_index for face in faces]
    bmesh.ops.delete(bm, geom=faces, context="FACES")
    _write_back(obj, bm)

    mesh = bpy.data.meshes.new((new_name or name + "_Separated") + "_Mesh")
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()
    separated = bpy.data.objects.new(new_name or name + "_Separated", mesh)
    for collection in obj.users_collection:
        collection.objects.link(separated)
    separated.matrix_world = obj.matrix_world.copy()
    for material in obj.data.materials:
        separated.data.materials.append(material)
    for polygon, material_index in zip(separated.data.polygons, material_indices):
        polygon.material_index = material_index
    persistent_ids.ensure_persistent_ids(separated.name)
    return {
        "new_object": separated.name,
        "separated_faces": len(polygons),
        "identity_discontinuity": True,
        "identity_note": "new object receives new persistent IDs; cross-object element identity is not silently reused",
    }
