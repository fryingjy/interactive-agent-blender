"""Fresh-process verification for the mixed surface-diagnosis scene.

Run:
    blender --background --factory-startup --python-exit-code 1 \
      --python tools/verify_mixed_surface_diagnosis.py -- FILE.blend REPORT.json

No project modeling or classifier code is imported.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


NAMES = {
    "clean": "Diagnosis_Clean_Control",
    "mixed": "Diagnosis_Mixed_FiveCause",
    "repaired": "Diagnosis_Fully_Repaired",
}


def arguments():
    argv = sys.argv
    if "--" not in argv or len(argv[argv.index("--") + 1 :]) != 2:
        raise SystemExit("expected FILE.blend REPORT.json after --")
    blend, report = argv[argv.index("--") + 1 :]
    return Path(blend).resolve(), Path(report).resolve()


def topology(obj, evaluated=False):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    owner = obj.evaluated_get(depsgraph) if evaluated else obj
    mesh = owner.to_mesh() if evaluated else obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    seen = set()
    components = 0
    for vertex in bm.verts:
        if vertex.index in seen:
            continue
        components += 1
        stack = [vertex]
        seen.add(vertex.index)
        while stack:
            current = stack.pop()
            for edge in current.link_edges:
                other = edge.other_vert(current)
                if other.index not in seen:
                    seen.add(other.index)
                    stack.append(other)
    stats = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "loose_vertices": sum(not vertex.link_edges for vertex in bm.verts),
        "loose_edges": sum(not edge.link_faces for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "connected_components": components,
        "signed_volume": bm.calc_volume(signed=True),
    }
    bm.free()
    if evaluated:
        owner.to_mesh_clear()
    return stats


def exact_state(obj):
    return {
        "coordinates": tuple(tuple(round(value, 7) for value in vertex.co) for vertex in obj.data.vertices),
        "winding": tuple(tuple(polygon.vertices) for polygon in obj.data.polygons),
        "material_indices": tuple(polygon.material_index for polygon in obj.data.polygons),
        "bevels": tuple(
            (modifier.name, round(modifier.width, 7), modifier.segments, modifier.limit_method)
            for modifier in obj.modifiers if modifier.type == "BEVEL"
        ),
    }


def main():
    blend_path, report_path = arguments()
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    missing = [name for name in NAMES.values() if bpy.data.objects.get(name) is None]
    if missing:
        raise SystemExit("missing expected objects: " + ", ".join(missing))
    objects = {key: bpy.data.objects[name] for key, name in NAMES.items()}
    base = {key: topology(obj) for key, obj in objects.items()}
    evaluated = {key: topology(obj, evaluated=True) for key, obj in objects.items()}
    states = {key: exact_state(obj) for key, obj in objects.items()}
    neutral_lights = [obj for obj in bpy.data.objects if obj.type == "LIGHT" and obj.name.startswith("Neutral_")]
    faulty_lights = [obj for obj in bpy.data.objects if obj.type == "LIGHT" and obj.name.startswith("Faulty_")]

    clean_health = all(
        base[name][field] == expected
        for name in ("clean", "repaired")
        for field, expected in (
            ("faces", 5376),
            ("quads", 5376),
            ("non_manifold_edges", 0),
            ("loose_vertices", 0),
            ("loose_edges", 0),
            ("degenerate_faces", 0),
            ("connected_components", 1),
        )
    )
    evaluated_clean = all(
        evaluated[name]["non_manifold_edges"] == 0
        and evaluated[name]["loose_vertices"] == 0
        and evaluated[name]["loose_edges"] == 0
        and evaluated[name]["degenerate_faces"] == 0
        and evaluated[name]["signed_volume"] > 0
        for name in ("clean", "repaired")
    )
    assertions = {
        "expected_objects_present": not missing,
        "clean_and_repaired_connected_all_quad": clean_health,
        "clean_and_repaired_evaluated_healthy": evaluated_clean,
        "repaired_exactly_matches_clean_state": states["repaired"] == states["clean"],
        "mixed_geometry_differs": states["mixed"]["coordinates"] != states["clean"]["coordinates"],
        "mixed_winding_differs": states["mixed"]["winding"] != states["clean"]["winding"],
        "mixed_material_assignment_differs": states["mixed"]["material_indices"] != states["clean"]["material_indices"],
        "mixed_has_unnecessary_bevel": bool(states["mixed"]["bevels"]),
        "mixed_evaluated_contains_degenerates": evaluated["mixed"]["degenerate_faces"] > 0,
        "saved_final_uses_neutral_not_faulty_lights": (
            len(neutral_lights) == 3
            and len(faulty_lights) == 2
            and all(not light.hide_render and light.data.energy > 0 for light in neutral_lights)
            and all(light.hide_render and light.data.energy == 0 for light in faulty_lights)
        ),
        "fixed_seed_cycles_saved": (
            bpy.context.scene.render.engine == "CYCLES"
            and bpy.context.scene.cycles.seed == 37
            and not bpy.context.scene.cycles.use_animated_seed
        ),
    }
    report = {
        "blend_path": str(blend_path),
        "blender_version": bpy.app.version_string,
        "verification_source": "fresh-process Blender datablocks and evaluated dependency graph",
        "base": base,
        "evaluated": evaluated,
        "mixed_bevels": [list(value) for value in states["mixed"]["bevels"]],
        "light_state": {
            "neutral": [{"name": light.name, "energy": light.data.energy, "hidden": light.hide_render} for light in neutral_lights],
            "faulty": [{"name": light.name, "energy": light.data.energy, "hidden": light.hide_render} for light in faulty_lights],
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("MIXED_SURFACE_VERIFY_RESULT:" + json.dumps(report))
    raise SystemExit(0 if report["pass"] else 1)


main()
