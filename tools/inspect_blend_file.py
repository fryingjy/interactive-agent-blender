"""Read-only inspection tool for studying a professional .blend file, per
docs/BLEND_FILE_STUDY_PROTOCOL.md. Opens the file, records raw scene/mesh/
modifier/material/UV/collection facts, and exits WITHOUT saving -- the
source file is never modified. This is step 1 (INSPECT) of the protocol's
loop; it deliberately does not interpret or infer anything, only records
what is directly readable from the file, so INSPECT and UNDERSTAND stay
separated as the protocol requires.

Usage:
    blender --background --factory-startup --python tools/inspect_blend_file.py -- <BLEND_PATH> <OUTPUT_JSON>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def mesh_stats(obj):
    me = obj.data
    return {
        "vertices": len(me.vertices),
        "edges": len(me.edges),
        "polygons": len(me.polygons),
        "ngons": sum(1 for p in me.polygons if len(p.vertices) > 4),
        "triangles": sum(1 for p in me.polygons if len(p.vertices) == 3),
        "quads": sum(1 for p in me.polygons if len(p.vertices) == 4),
        "uv_layers": [uv.name for uv in me.uv_layers],
        "vertex_groups": [vg.name for vg in obj.vertex_groups],
        "shape_keys": [sk.name for sk in me.shape_keys.key_blocks] if me.shape_keys else [],
        "has_custom_split_normals": bool(me.has_custom_normals) if hasattr(me, "has_custom_normals") else None,
        "material_slots": [m.name if m else None for m in me.materials],
        "bevel_weight_attribute_present": "bevel_weight_edge" in me.attributes,
        "crease_attribute_present": any(a.name in ("crease_edge", "crease_vert") for a in me.attributes),
        "auto_smooth_angle_deg": None,
    }


def modifier_info(obj):
    out = []
    for m in obj.modifiers:
        entry = {"name": m.name, "type": m.type, "show_viewport": m.show_viewport, "show_render": m.show_render}
        if m.type == "BEVEL":
            entry.update({"width": m.width, "segments": m.segments, "limit_method": m.limit_method,
                          "angle_limit_deg": round(__import__("math").degrees(m.angle_limit), 2) if hasattr(m, "angle_limit") else None,
                          "harden_normals": getattr(m, "harden_normals", None)})
        elif m.type == "SUBSURF":
            entry.update({"levels": m.levels, "render_levels": m.render_levels,
                          "subdivision_type": m.subdivision_type,
                          "use_limit_surface": getattr(m, "use_limit_surface", None)})
        elif m.type == "MIRROR":
            entry.update({"use_axis": list(m.use_axis), "use_bisect_axis": list(m.use_bisect_axis),
                          "merge_threshold": m.merge_threshold})
        elif m.type == "SOLIDIFY":
            entry.update({"thickness": m.thickness, "offset": m.offset})
        elif m.type == "ARRAY":
            entry.update({"count": m.count, "use_relative_offset": m.use_relative_offset})
        elif m.type == "WEIGHTED_NORMAL":
            entry.update({"weight": m.weight, "keep_sharp": m.keep_sharp})
        elif m.type == "NODES":
            entry.update({"node_group": m.node_group.name if m.node_group else None})
        out.append(entry)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    blend_path, out_path = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    scene = bpy.context.scene
    report = {
        "blend_path": str(blend_path),
        "inspected_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "blender_version_used": bpy.app.version_string,
        "file_saved_with_version": ".".join(str(v) for v in bpy.data.version) if hasattr(bpy.data, "version") else None,
        "scene_name": scene.name,
        "collections": [],
        "objects": [],
        "materials_total": len(bpy.data.materials),
        "material_names": [m.name for m in bpy.data.materials],
        "images_total": len(bpy.data.images),
        "image_names": [img.name for img in bpy.data.images],
    }

    def walk_collection(col, depth=0):
        report["collections"].append({
            "name": col.name, "depth": depth,
            "object_count": len(col.objects),
            "child_collections": [c.name for c in col.children],
        })
        for c in col.children:
            walk_collection(c, depth + 1)

    walk_collection(scene.collection)

    for obj in bpy.data.objects:
        entry = {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation_euler_deg": [round(__import__("math").degrees(a), 2) for a in obj.rotation_euler],
            "scale": list(obj.scale),
            "parent": obj.parent.name if obj.parent else None,
            "collections": [c.name for c in obj.users_collection],
            "hide_viewport": obj.hide_viewport,
            "hide_render": obj.hide_render,
            "custom_properties": {k: (obj[k] if isinstance(obj[k], (int, float, str, bool)) else str(obj[k])) for k in obj.keys()},
        }
        if obj.type == "MESH":
            entry["mesh"] = mesh_stats(obj)
            entry["modifiers"] = modifier_info(obj)
        elif obj.type in ("CURVE", "SURFACE", "FONT"):
            entry["modifiers"] = modifier_info(obj)
        elif obj.type == "EMPTY":
            entry["empty_display_type"] = obj.empty_display_type
        report["objects"].append(entry)

    out_path.write_text(json.dumps(report, indent=2))
    print("INSPECT_RESULT_PATH:" + str(out_path))
    print(json.dumps({"object_count": len(report["objects"]), "collection_count": len(report["collections"])}, indent=2))


if __name__ == "__main__":
    main()
