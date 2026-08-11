"""Probe weighted-bevel widths on the saved connected camera without mutating it."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def health(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(values) != 2:
    raise SystemExit("expected BLEND_FILE OUTPUT_REPORT after --")
blend_file, output = (Path(value).resolve() for value in values)
bpy.ops.wm.open_mainfile(filepath=str(blend_file))
obj = next(obj for obj in bpy.data.objects if obj.type == "MESH")
bevel = next(modifier for modifier in obj.modifiers if modifier.type == "BEVEL")
subdivision = next(modifier for modifier in obj.modifiers if modifier.type == "SUBSURF")
attribute = obj.data.attributes["bevel_weight_edge"]
lens_center = (0.32, -0.28)
scenarios = ("lens_only", "front_only", "back_only", "lens_and_front")
records = []
for scenario in scenarios:
    count = 0
    for edge in obj.data.edges:
        first = obj.data.vertices[edge.vertices[0]].co
        second = obj.data.vertices[edge.vertices[1]].co
        same_y = abs(first.y - second.y) < 1e-5
        first_radius = ((first.x - lens_center[0]) ** 2 + (first.z - lens_center[1]) ** 2) ** 0.5
        second_radius = ((second.x - lens_center[0]) ** 2 + (second.z - lens_center[1]) ** 2) ** 0.5
        lens = same_y and abs(first_radius - second_radius) < 0.035 and first.y <= -0.819 and min(first_radius, second_radius) > 0.5 and max(first_radius, second_radius) < 1.3
        front = same_y and abs(first.y + 0.82) < 1e-5 and min(first_radius, second_radius) > 1.45
        back = same_y and abs(first.y - 0.82) < 1e-5
        weighted = {"lens_only": lens, "front_only": front, "back_only": back, "lens_and_front": lens or front}[scenario]
        attribute.data[edge.index].value = 1.0 if weighted else 0.0
        count += int(weighted)
    bevel.width = 0.028
    subdivision.show_viewport = False
    bevel_only = health(obj)
    subdivision.show_viewport = True
    full_stack = health(obj)
    records.append({"scenario": scenario, "weighted_edges": count, "bevel_only": bevel_only, "bevel_then_subdivision": full_stack})
report = {"lab": "connected_camera_weighted_bevel_scope_probe", "records": records}
output.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("BEVEL_PROBE:" + json.dumps(report))
