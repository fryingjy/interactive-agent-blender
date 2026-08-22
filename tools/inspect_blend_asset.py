"""Read-only structural audit for a Blender asset example.

Run with Blender after opening a file:
    blender --background example.blend --python tools/inspect_blend_asset.py -- output.json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def output_path():
    argv = sys.argv
    if "--" not in argv or len(argv[argv.index("--") + 1 :]) != 1:
        raise SystemExit("expected one output JSON path after --")
    return Path(argv[argv.index("--") + 1]).resolve()


def mesh_record(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    non_manifold = sum(not edge.is_manifold for edge in bm.edges)
    boundaries = sum(edge.is_boundary for edge in bm.edges)
    ngons = sum(len(face.verts) > 4 for face in bm.faces)
    triangles = sum(len(face.verts) == 3 for face in bm.faces)
    quads = sum(len(face.verts) == 4 for face in bm.faces)
    degenerate = sum(face.calc_area() < 1e-8 for face in bm.faces)
    bm.free()
    world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    world_dimensions = [
        max(corner[axis] for corner in world_corners) - min(corner[axis] for corner in world_corners)
        for axis in range(3)
    ]
    return {
        "name": obj.name,
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "triangles": triangles,
        "quads": quads,
        "ngons": ngons,
        "boundary_edges": boundaries,
        "non_manifold_edges": non_manifold,
        "degenerate_faces": degenerate,
        "uv_layers": len(mesh.uv_layers),
        "materials": len(obj.material_slots),
        "modifiers": [
            {"name": modifier.name, "type": modifier.type, "show_viewport": modifier.show_viewport}
            for modifier in obj.modifiers
        ],
        "dimensions": [float(value) for value in world_dimensions],
        "dimensions_space": "WORLD_AXIS_ALIGNED_BASE_CAGE",
        "scale": [float(value) for value in obj.scale],
        "hidden_viewport": obj.hide_get(),
        "hidden_render": obj.hide_render,
    }


def main():
    destination = output_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    # A freshly loaded background file can expose stale Object.dimensions until
    # the view layer evaluates object transforms. This matters for authored
    # radial parts rotated into an assembly axis: without the update, the audit
    # can report the pre-rotation local bounds even though renders use the
    # correct world transform.
    bpy.context.view_layer.update()
    objects = list(bpy.data.objects)
    meshes = [mesh_record(obj) for obj in objects if obj.type == "MESH"]
    meshes.sort(key=lambda item: item["faces"], reverse=True)
    modifier_counts = Counter(
        modifier["type"] for item in meshes for modifier in item["modifiers"]
    )
    report = {
        "source_blend": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "scene": bpy.context.scene.name if bpy.context.scene else None,
        "collections": len(bpy.data.collections),
        "objects_by_type": dict(Counter(obj.type for obj in objects)),
        "mesh_totals": {
            "objects": len(meshes),
            "vertices": sum(item["vertices"] for item in meshes),
            "faces": sum(item["faces"] for item in meshes),
            "triangles": sum(item["triangles"] for item in meshes),
            "quads": sum(item["quads"] for item in meshes),
            "ngons": sum(item["ngons"] for item in meshes),
            "boundary_edges": sum(item["boundary_edges"] for item in meshes),
            "non_manifold_edges": sum(item["non_manifold_edges"] for item in meshes),
            "degenerate_faces": sum(item["degenerate_faces"] for item in meshes),
        },
        "modifier_counts": dict(modifier_counts),
        "materials": len(bpy.data.materials),
        "images": len(bpy.data.images),
        "armatures": len(bpy.data.armatures),
        "actions": len(bpy.data.actions),
        "mesh_names": [item["name"] for item in meshes],
        "largest_meshes": meshes[:20],
        "assessment_limits": [
            "Structural inventory does not establish artistic quality.",
            "Open boundaries may be intentional and require object-level interpretation.",
            "Base mesh counts do not include evaluated modifier geometry.",
        ],
    }
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("ASSET_INSPECTION_RESULT:" + json.dumps(report))


main()
