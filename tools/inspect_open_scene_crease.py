"""Write a read-only crease/topology snapshot of the currently open Blender scene."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


DEFAULT_OUTPUT = Path(
    r"C:\Users\odane\Downloads\3d\runs\2026-08-16_scotch-c38-model\user_scene_crease_inspection.json"
)


def output_path() -> Path:
    tail = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(tail) > 1:
        raise SystemExit("Expected at most one OUTPUT.json argument after --")
    return Path(tail[0]).resolve() if tail else DEFAULT_OUTPUT


def attribute_record(attribute):
    values = [float(item.value) for item in attribute.data]
    return {
        "name": attribute.name,
        "domain": attribute.domain,
        "data_type": attribute.data_type,
        "nonzero": sum(value > 1e-6 for value in values),
        "at_or_above_0_5": sum(value >= 0.5 for value in values),
        "at_or_above_0_8": sum(value >= 0.8 for value in values),
        "maximum": max(values, default=0.0),
        "distinct_rounded_values": sorted({round(value, 4) for value in values}),
    }


def object_record(obj):
    mesh = obj.data
    crease_attributes = [
        attribute_record(attribute)
        for attribute in mesh.attributes
        if attribute.domain == "EDGE" and "crease" in attribute.name.lower()
    ]
    bevel_attributes = [
        attribute_record(attribute)
        for attribute in mesh.attributes
        if attribute.domain == "EDGE" and "bevel" in attribute.name.lower()
    ]
    return {
        "name": obj.name,
        "selected": obj.select_get(),
        "active": bpy.context.view_layer.objects.active == obj,
        "mode": obj.mode,
        "dimensions": list(obj.dimensions),
        "topology": {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "triangles": sum(len(face.vertices) == 3 for face in mesh.polygons),
            "quads": sum(len(face.vertices) == 4 for face in mesh.polygons),
            "ngons": sum(len(face.vertices) > 4 for face in mesh.polygons),
        },
        "crease_attributes": crease_attributes,
        "bevel_weight_attributes": bevel_attributes,
        "modifiers": [
            {
                "name": modifier.name,
                "type": modifier.type,
                "show_viewport": modifier.show_viewport,
                "show_render": modifier.show_render,
                "levels": getattr(modifier, "levels", None),
                "render_levels": getattr(modifier, "render_levels", None),
                "width": getattr(modifier, "width", None),
                "segments": getattr(modifier, "segments", None),
                "limit_method": getattr(modifier, "limit_method", None),
            }
            for modifier in obj.modifiers
        ],
        "smooth_faces": sum(face.use_smooth for face in mesh.polygons),
    }


OUTPUT = output_path()
report = {
    "schema_version": 1,
    "record_type": "OPEN_SCENE_CREASE_INSPECTION",
    "read_only": True,
    "blend_file": bpy.data.filepath,
    "is_dirty": bpy.data.is_dirty,
    "active_object": bpy.context.view_layer.objects.active.name
    if bpy.context.view_layer.objects.active
    else None,
    "objects": [object_record(obj) for obj in bpy.context.scene.objects if obj.type == "MESH"],
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"OPEN_SCENE_CREASE_INSPECTION:{OUTPUT}")
