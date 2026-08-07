import os

import bmesh
import bpy


def pid():
    return os.getpid()


def probe_scene():
    scene = bpy.context.scene
    objects = [{"name": o.name, "type": o.type} for o in scene.objects]
    return {"scene": scene.name, "object_count": len(objects), "objects": objects}


def probe_object(name):
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
        info["mesh"] = {
            "vertices": len(obj.data.vertices),
            "edges": len(obj.data.edges),
            "polygons": len(obj.data.polygons),
        }
    return info


def get_selection(name):
    """Rich selection state: which vertex/edge/face IDs are actually selected right
    now, and what selection mode is active. Reads obj.data's select flags directly
    (kept in sync by Blender regardless of edit/object mode), not a bmesh copy."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    mesh = obj.data
    selected_verts = [v.index for v in mesh.vertices if v.select]
    selected_edges = [e.index for e in mesh.edges if e.select]
    selected_faces = [p.index for p in mesh.polygons if p.select]
    selection_mode = None
    ts = bpy.context.tool_settings
    if ts is not None:
        vert, edge, face = ts.mesh_select_mode
        selection_mode = [m for m, on in (("VERTEX", vert), ("EDGE", edge), ("FACE", face)) if on]
    return {
        "mode": obj.mode,
        "selection_mode": selection_mode,
        "selected_vertex_ids": selected_verts,
        "selected_edge_ids": selected_edges,
        "selected_face_ids": selected_faces,
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
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    if vertex_index < 0 or vertex_index >= len(bm.verts):
        bm.free()
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
    bm.free()
    return result


def valence_distribution(name):
    """Histogram of vertex valence across the whole mesh -- how many 3-poles,
    4-poles (clean quad flow), 5-poles, 6-poles, etc."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    dist = {}
    for v in bm.verts:
        val = len(v.link_edges)
        dist[val] = dist.get(val, 0) + 1
    bm.free()
    return dist


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


def mesh_health(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}

    bm = bmesh.new()
    bm.from_mesh(obj.data)
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
    bm.free()
    return result
