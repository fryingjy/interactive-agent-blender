"""Isolate weighted-bevel failures by semantic sharp-edge category."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def evaluated_health(obj):
    owner = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = owner.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
    }
    bm.free()
    owner.to_mesh_clear()
    return result


values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(values) != 2:
    raise SystemExit("expected BLEND_FILE OUTPUT_REPORT after --")
blend_file, output = (Path(value).resolve() for value in values)
bpy.ops.wm.open_mainfile(filepath=str(blend_file))
obj = next(item for item in bpy.data.objects if item.type == "MESH")
bevel = next(modifier for modifier in obj.modifiers if modifier.type == "BEVEL")
subdivision = next(modifier for modifier in obj.modifiers if modifier.type == "SUBSURF")
attribute = obj.data.attributes["bevel_weight_edge"]
categories = {key: set(value) for key, value in json.loads(obj["sharp_edge_indices_json"]).items()}
scenarios = {name: indices for name, indices in categories.items()}
body_indices = categories["body_perimeters"]
for y_value in (-0.82, -0.78, 0.78, 0.82):
    scenarios[f"body_y_{y_value:+.2f}"] = {
        edge.index
        for edge in obj.data.edges
        if edge.index in body_indices
        and all(abs(obj.data.vertices[vertex].co.y - y_value) < 1e-5 for vertex in edge.vertices)
    }
scenarios["all_controls"] = categories["top_control_1"] | categories["top_control_2"]
scenarios["all_except_body"] = set().union(*(indices for name, indices in categories.items() if not name.startswith("body_")))
scenarios["all"] = set().union(*categories.values())
records = []
for name, indices in scenarios.items():
    for edge in obj.data.edges:
        attribute.data[edge.index].value = 1.0 if edge.index in indices else 0.0
    subdivision.show_viewport = False
    bpy.context.view_layer.update()
    bevel_only = evaluated_health(obj)
    subdivision.show_viewport = True
    bpy.context.view_layer.update()
    full_stack = evaluated_health(obj)
    records.append({"scenario": name, "weighted_edges": len(indices), "bevel_only": bevel_only, "full_stack": full_stack})
front_indices = scenarios["body_y_-0.82"]
for width in (0.014, 0.010, 0.006, 0.003):
    bevel.width = width
    for edge in obj.data.edges:
        attribute.data[edge.index].value = 1.0 if edge.index in front_indices else 0.0
    subdivision.show_viewport = False
    bpy.context.view_layer.update()
    bevel_only = evaluated_health(obj)
    subdivision.show_viewport = True
    bpy.context.view_layer.update()
    full_stack = evaluated_health(obj)
    records.append({"scenario": f"body_front_width_{width:.3f}", "weighted_edges": len(front_indices), "bevel_only": bevel_only, "full_stack": full_stack})
report = {"lab": "connected_camera_semantic_sharp_edge_probe", "records": records}
output.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("SEMANTIC_BEVEL_PROBE:" + json.dumps(report))
