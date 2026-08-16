"""Fresh-process verification for the Bevel normal-policy comparison."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy


def evaluated_metrics(obj: bpy.types.Object) -> dict[str, float | int | bool]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        panel_faces = sorted(mesh.polygons, key=lambda polygon: polygon.area, reverse=True)[:6]
        errors = []
        for polygon in panel_faces:
            face_normal = polygon.normal.normalized()
            for loop_index in polygon.loop_indices:
                corner_normal = mesh.corner_normals[loop_index].vector.normalized()
                dot = max(-1.0, min(1.0, face_normal.dot(corner_normal)))
                errors.append(math.degrees(math.acos(dot)))
        bm = bmesh.new()
        bm.from_mesh(mesh)
        non_manifold = sum(not edge.is_manifold for edge in bm.edges)
        degenerate = sum(face.calc_area() <= 1e-12 for face in bm.faces)
        bm.free()
        return {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "max_error_deg": max(errors),
            "custom_normal": "custom_normal" in mesh.attributes,
            "non_manifold": non_manifold,
            "degenerate": degenerate,
        }
    finally:
        evaluated.to_mesh_clear()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("blend", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    expected_names = {
        "PLAIN_SMOOTH": "Plain_Smooth_Bevel",
        "HARDEN_NORMALS": "Harden_Normals_Bevel",
        "FACE_STRENGTH_WEIGHTED": "Face_Strength_Weighted_Normal",
    }
    objects = {policy: bpy.data.objects.get(name) for policy, name in expected_names.items()}
    metrics = {policy: evaluated_metrics(obj) for policy, obj in objects.items() if obj}
    modifier_types = {policy: [modifier.type for modifier in obj.modifiers] for policy, obj in objects.items() if obj}
    plain = metrics.get("PLAIN_SMOOTH", {})
    hardened = metrics.get("HARDEN_NORMALS", {})
    weighted = metrics.get("FACE_STRENGTH_WEIGHTED", {})
    assertions = {
        "all_expected_objects_exist": all(objects.values()),
        "plain_stack_is_bevel": modifier_types.get("PLAIN_SMOOTH") == ["BEVEL"],
        "hardened_stack_is_bevel": modifier_types.get("HARDEN_NORMALS") == ["BEVEL"],
        "weighted_stack_orders_bevel_then_weighted_normal": modifier_types.get("FACE_STRENGTH_WEIGHTED") == ["BEVEL", "WEIGHTED_NORMAL"],
        "harden_flag_is_saved": bool(objects["HARDEN_NORMALS"] and objects["HARDEN_NORMALS"].modifiers[0].harden_normals),
        "face_influence_is_saved": bool(objects["FACE_STRENGTH_WEIGHTED"] and objects["FACE_STRENGTH_WEIGHTED"].modifiers[-1].use_face_influence),
        "normal_policies_improve_large_panels": bool(plain and hardened and weighted and hardened["max_error_deg"] < plain["max_error_deg"] and weighted["max_error_deg"] < plain["max_error_deg"]),
        "corrected_panels_are_sub_degree": bool(hardened and weighted and hardened["max_error_deg"] < 1.0 and weighted["max_error_deg"] < 1.0),
        "all_evaluated_meshes_are_clean": all(item["non_manifold"] == 0 and item["degenerate"] == 0 for item in metrics.values()) and len(metrics) == 3,
    }
    result = {
        "blender_version": bpy.app.version_string,
        "blend": str(args.blend),
        "modifier_types": modifier_types,
        "metrics": metrics,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "claim_boundary": "Independent saved-file and evaluated-normal verification. It does not import the builder or certify visual quality on an unfamiliar asset.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    raise SystemExit(0 if result["pass"] else 2)


main()
