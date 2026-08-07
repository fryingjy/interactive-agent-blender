import os

import bpy

import bmesh_io
import decision_state
import persistent_ids


def _free_if_object_mode(obj, bm):
    """bmesh.from_edit_mesh() returns Blender's own live edit-bmesh, owned by
    the edit-mesh system -- freeing it would corrupt the live edit session.
    Only bmesh.new()-created copies (Object Mode reads) should be freed."""
    if obj.mode != "EDIT":
        bm.free()


def pid():
    return os.getpid()


def probe_scene():
    scene = bpy.context.scene
    objects = [{"name": o.name, "type": o.type} for o in scene.objects]
    return {"scene": scene.name, "object_count": len(objects), "objects": objects}


def probe_object(name):
    """CORRECTION (found live during the mug-handle fix, confirmed again while
    auditing this module against the master directive's Edit Mode truth
    requirement): obj.data.vertices/edges/polygons counts are NOT reliably
    live while the object is in Edit Mode -- they reflect the mesh datablock
    as of mode entry, not the true current edit-bmesh, until Blender flushes
    on mode exit. Uses bmesh_io.read_bmesh (mode-aware) instead."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        return {"error": f"object '{name}' not found"}
    info = {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation_euler": list(obj.rotation_euler),
        "scale": list(obj.scale),
        "mode": obj.mode,
    }
    if obj.type == "MESH":
        bm = bmesh_io.read_bmesh(obj)
        info["mesh"] = {
            "vertices": len(bm.verts),
            "edges": len(bm.edges),
            "polygons": len(bm.faces),
        }
        _free_if_object_mode(obj, bm)
    return info


def get_selection(name):
    """Rich selection state: which vertex/edge/face indices are actually
    selected right now, each paired with its persistent agent_id where one
    has been assigned, plus the active selection mode.

    CORRECTION (found auditing against the master directive's Edit Mode
    truth requirement): previously read obj.data's select flags directly on
    the claim they're "kept in sync ... regardless of edit/object mode" --
    untested, and the same class of assumption already disproved once this
    session for mesh counts (see probe_object). Now reads through
    bmesh_io.read_bmesh, which is mode-aware by construction rather than by
    assumption. Per the master directive: reason about persistent agent_id,
    not the raw index, since the index can renumber after unrelated
    topology changes elsewhere in the mesh; resolve back to an index only
    immediately before issuing a Blender operation."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}

    bm = bmesh_io.read_bmesh(obj)
    id_maps = persistent_ids.get_id_maps(name)

    def _pairs(seq, kind):
        index_to_id = id_maps[kind]["index_to_id"]
        return [{"index": e.index, "agent_id": index_to_id.get(e.index)} for e in seq if e.select]

    selected_verts = _pairs(bm.verts, "verts")
    selected_edges = _pairs(bm.edges, "edges")
    selected_faces = _pairs(bm.faces, "faces")
    _free_if_object_mode(obj, bm)

    selection_mode = None
    ts = bpy.context.tool_settings
    if ts is not None:
        vert, edge, face = ts.mesh_select_mode
        selection_mode = [m for m, on in (("VERTEX", vert), ("EDGE", edge), ("FACE", face)) if on]
    return {
        "mode": obj.mode,
        "selection_mode": selection_mode,
        "selected_vertices": selected_verts,
        "selected_edges": selected_edges,
        "selected_faces": selected_faces,
        "selected_vertex_count": len(selected_verts),
        "selected_edge_count": len(selected_edges),
        "selected_face_count": len(selected_faces),
    }


def vertex_neighborhood(name, vertex_index):
    """Local topology around one vertex: valence, whether it sits on a boundary
    (non-manifold edge), its immediate neighbors, and the edge lengths / face areas
    touching it. This is what lets a decision be "the loop is too close to the
    corner" instead of "vertex 41 has some coordinates"."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm = bmesh_io.read_bmesh(obj)
    bm.verts.ensure_lookup_table()
    if vertex_index < 0 or vertex_index >= len(bm.verts):
        _free_if_object_mode(obj, bm)
        return {"error": f"vertex index {vertex_index} out of range (0..{len(bm.verts) - 1})"}
    v = bm.verts[vertex_index]
    result = {
        "vertex_index": vertex_index,
        "valence": len(v.link_edges),
        "is_boundary": any(not e.is_manifold for e in v.link_edges),
        "neighbor_vertex_ids": [e.other_vert(v).index for e in v.link_edges],
        "connected_edge_lengths": [round(e.calc_length(), 5) for e in v.link_edges],
        "connected_face_areas": [round(f.calc_area(), 5) for f in v.link_faces],
        "connected_face_ids": [f.index for f in v.link_faces],
    }
    _free_if_object_mode(obj, bm)
    return result


def valence_distribution(name):
    """Histogram of vertex valence across the whole mesh -- how many 3-poles,
    4-poles (clean quad flow), 5-poles, 6-poles, etc."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm = bmesh_io.read_bmesh(obj)
    bm.verts.ensure_lookup_table()
    dist = {}
    for v in bm.verts:
        val = len(v.link_edges)
        dist[val] = dist.get(val, 0) + 1
    _free_if_object_mode(obj, bm)
    return dist


_STANDARD_VIEW_ROTATIONS = {
    # Read directly from bpy.ops.view3d.view_axis() output for this Blender
    # version rather than typed from memory -- a first attempt using
    # remembered values was live-tested against an actual FRONT view and
    # failed to match, both because the exact values were wrong and because
    # quaternion sign was not accounted for (q and -q are the same rotation;
    # see the caller, which checks both).
    "FRONT": (0.707107, 0.707107, -0.0, -0.0),
    "BACK": (0.0, -0.0, 0.707107, 0.707107),
    "TOP": (1.0, -0.0, -0.0, -0.0),
    "BOTTOM": (0.0, 1.0, -0.0, -0.0),
    "LEFT": (0.5, 0.5, -0.5, -0.5),
    "RIGHT": (0.5, 0.5, 0.5, 0.5),
}


def viewport_state():
    """Direct state for the first 3D viewport found -- projection type,
    view distance/location, shading mode, x-ray, local view, active camera
    -- so the agent knows whether it's evaluating a front-orthographic
    silhouette vs. a perspective view vs. wireframe without inferring that
    from rendered pixels (this project deliberately doesn't use
    screenshots for facts Blender can expose directly)."""
    area = space = region_3d = None
    for a in bpy.context.screen.areas:
        if a.type == "VIEW_3D":
            area = a
            space = a.spaces.active
            region_3d = space.region_3d
            break
    if area is None:
        return {"error": "no 3D viewport found in the current screen"}

    rotation = tuple(round(c, 6) for c in region_3d.view_rotation)
    orientation_label = None
    for label, ref in _STANDARD_VIEW_ROTATIONS.items():
        matches_positive = all(abs(a - b) < 1e-3 for a, b in zip(rotation, ref))
        matches_negated = all(abs(a + b) < 1e-3 for a, b in zip(rotation, ref))
        if matches_positive or matches_negated:
            orientation_label = label
            break

    result = {
        "view_perspective": region_3d.view_perspective,  # 'PERSP' | 'ORTHO' | 'CAMERA'
        "orientation_label": orientation_label,  # None if not a standard axis-aligned view
        "view_rotation": rotation,
        "view_distance": round(region_3d.view_distance, 5),
        "view_location": [round(c, 5) for c in region_3d.view_location],
        "shading_type": space.shading.type,  # 'WIREFRAME' | 'SOLID' | 'MATERIAL' | 'RENDERED'
        "show_xray": bool(space.shading.show_xray),
        "local_view": space.local_view is not None,
        "lens_mm": round(space.lens, 2),
    }

    cam = bpy.context.scene.camera
    if cam is not None:
        result["active_camera"] = {
            "name": cam.name,
            "location": [round(c, 5) for c in cam.location],
            "rotation_euler": [round(c, 5) for c in cam.rotation_euler],
            "lens_mm": round(cam.data.lens, 2) if cam.data else None,
        }
    else:
        result["active_camera"] = None
    return result


def inspect_region(name, center_ids, rings=2):
    """A local topology graph around one or more persistent vertex IDs,
    grown outward by `rings` edge-hops -- richer than vertex_neighborhood()
    (which only covers one vertex's immediate neighbors). Returns vertices,
    edges, and faces touching the region, each keyed by persistent agent_id
    (not raw index, which can renumber elsewhere in the mesh), plus
    region-level aggregates useful for judging local mesh quality: pole
    locations (valence != 4), edge-length ratio, face-area ratio, local
    tri/quad/ngon counts, and connected-component count within the region
    (computed directly from the collected edges, not assumed to be 1)."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}

    bm = bmesh_io.read_bmesh(obj)
    bm.verts.ensure_lookup_table()

    id_maps = persistent_ids.get_id_maps(name)
    vert_id_to_index = id_maps["verts"]["id_to_index"]
    vert_index_to_id = id_maps["verts"]["index_to_id"]

    start_indices = set()
    missing = []
    for agent_id in center_ids:
        idx = vert_id_to_index.get(agent_id)
        if idx is None:
            missing.append(agent_id)
        else:
            start_indices.add(idx)
    if not start_indices:
        _free_if_object_mode(obj, bm)
        return {"error": f"none of center_ids {center_ids} resolved to a vertex on '{name}'", "missing_ids": missing}

    frontier = set(start_indices)
    visited = set(start_indices)
    for _ in range(max(0, rings)):
        next_frontier = set()
        for idx in frontier:
            for e in bm.verts[idx].link_edges:
                other = e.other_vert(bm.verts[idx]).index
                if other not in visited:
                    next_frontier.add(other)
        visited |= next_frontier
        frontier = next_frontier
        if not frontier:
            break

    region_verts = [bm.verts[i] for i in sorted(visited)]
    region_edges = {e for v in region_verts for e in v.link_edges}
    region_faces = {f for v in region_verts for f in v.link_faces}

    verts_out = {}
    poles = []
    for v in region_verts:
        vid = vert_index_to_id.get(v.index)
        valence = len(v.link_edges)
        is_boundary = any(not e.is_manifold for e in v.link_edges)
        verts_out[vid if vid is not None else f"idx_{v.index}"] = {
            "index": v.index,
            "agent_id": vid,
            "position": [round(c, 5) for c in v.co],
            "valence": valence,
            "is_boundary": is_boundary,
            "neighbor_agent_ids": [vert_index_to_id.get(e.other_vert(v).index) for e in v.link_edges],
        }
        if valence != 4:
            poles.append({"agent_id": vid, "index": v.index, "valence": valence, "position": [round(c, 5) for c in v.co]})

    edge_lengths = []
    edges_out = []
    for e in region_edges:
        length = e.calc_length()
        edge_lengths.append(length)
        angle = None
        if len(e.link_faces) == 2:
            angle = round(e.calc_face_angle(), 5)
        edges_out.append({
            "vertex_indices": [v.index for v in e.verts],
            "vertex_agent_ids": [vert_index_to_id.get(v.index) for v in e.verts],
            "length": round(length, 5),
            "is_boundary": not e.is_manifold,
            "face_angle_radians": angle,
        })

    face_areas = []
    faces_out = []
    tri = quad = ngon = 0
    for f in region_faces:
        area = f.calc_area()
        face_areas.append(area)
        n = len(f.verts)
        if n == 3:
            tri += 1
        elif n == 4:
            quad += 1
        else:
            ngon += 1
        faces_out.append({
            "index": f.index,
            "vertex_count": n,
            "area": round(area, 6),
            "normal": [round(c, 5) for c in f.normal],
        })

    # connected components within the region, computed from the actual
    # collected edges -- not assumed to be 1 just because this started as a
    # BFS (center_ids could themselves be in disconnected parts of the mesh
    # if rings=0 or the mesh has separate shells).
    region_vert_indices = {v.index for v in region_verts}
    adjacency = {i: [] for i in region_vert_indices}
    for e in region_edges:
        a, b = (v.index for v in e.verts)
        if a in adjacency and b in adjacency:
            adjacency[a].append(b)
            adjacency[b].append(a)
    remaining = set(region_vert_indices)
    components = 0
    while remaining:
        components += 1
        stack = [next(iter(remaining))]
        while stack:
            cur = stack.pop()
            if cur in remaining:
                remaining.discard(cur)
                stack.extend(adjacency.get(cur, []))

    _free_if_object_mode(obj, bm)

    return {
        "center_ids": center_ids,
        "missing_center_ids": missing,
        "rings": rings,
        "vertex_count": len(region_verts),
        "edge_count": len(region_edges),
        "face_count": len(region_faces),
        "vertices": verts_out,
        "edges": edges_out,
        "faces": faces_out,
        "poles": poles,
        "local_face_composition": {"tri": tri, "quad": quad, "ngon": ngon},
        "edge_length_ratio": round(max(edge_lengths) / min(edge_lengths), 3) if edge_lengths and min(edge_lengths) > 1e-9 else None,
        "face_area_ratio": round(max(face_areas) / min(face_areas), 3) if face_areas and min(face_areas) > 1e-9 else None,
        "connected_components": components,
    }


def modifier_state(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        return {"error": f"object '{name}' not found"}
    return {
        "modifier_count": len(obj.modifiers),
        "modifiers": [
            {"name": m.name, "type": m.type, "show_viewport": m.show_viewport}
            for m in obj.modifiers
        ],
    }


def active_state():
    """Which object/mode is actually active right now -- not per-object, this is
    global editor state."""
    vl = bpy.context.view_layer
    active_obj = vl.objects.active
    return {
        "active_object": active_obj.name if active_obj else None,
        "mode": active_obj.mode if active_obj else None,
    }


def get_full_state(name):
    """One consolidated read -- revision, mesh health, valence
    distribution, selection, and persistent-ID coverage -- covering what a
    decision typically needs before choosing its next action, instead of
    several separate round trips."""
    id_maps = persistent_ids.get_id_maps(name)
    id_coverage = {kind: len(m["index_to_id"]) for kind, m in id_maps.items()}
    return {
        "revision": decision_state.current_revision(),
        "mesh_health": mesh_health(name),
        "valence_distribution": valence_distribution(name),
        "selection": get_selection(name),
        "persistent_id_coverage": id_coverage,
    }


def mesh_health(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}

    bm = bmesh_io.read_bmesh(obj)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
        "ngons": sum(1 for f in bm.faces if len(f.verts) > 4),
        "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
        "degenerate_faces": sum(1 for f in bm.faces if f.calc_area() < 1e-8),
    }
    _free_if_object_mode(obj, bm)
    return result
