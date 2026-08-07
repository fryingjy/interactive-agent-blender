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
