"""Fresh-process verification for the facial corrective-transfer lab.

Run:
    blender --background --factory-startup --python-exit-code 1 \
      --python tools/verify_facial_expression_transfer.py -- FILE.blend REPORT.json

The verifier deliberately imports no project modeling code and reconstructs its
claims from the saved Blender datablocks and dependency graph.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy


EXPECTED = {
    "Dense_Corrected_Reference": "Dense_Face_Rig",
    "Purposeful_Uncorrected_Face": "Uncorrected_Face_Rig",
    "Purposeful_DrivenCorrective_Face": "Corrected_Face_Rig",
}


def arguments():
    argv = sys.argv
    if "--" not in argv or len(argv[argv.index("--") + 1 :]) != 2:
        raise SystemExit("expected FILE.blend REPORT.json after --")
    blend, report = argv[argv.index("--") + 1 :]
    return Path(blend).resolve(), Path(report).resolve()


def base_topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    jaw_group = obj.vertex_groups.get("Jaw")
    jaw_indices = set()
    if jaw_group is not None:
        for vertex in obj.data.vertices:
            if any(group.group == jaw_group.index and group.weight > 1e-6 for group in vertex.groups):
                jaw_indices.add(vertex.index)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "loose_vertices": sum(not vertex.link_edges for vertex in bm.verts),
        "loose_edges": sum(not edge.link_faces for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "jaw_weighted_vertices": len(jaw_indices),
        "non_quad_faces_touching_weighted_jaw": sum(
            len(face.verts) != 4 and any(vertex.index in jaw_indices for vertex in face.verts)
            for face in bm.faces
        ),
    }
    bm.free()
    return result


def evaluated_topology(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    stats = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "loose_vertices": sum(not vertex.link_edges for vertex in bm.verts),
        "loose_edges": sum(not edge.link_faces for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "signed_volume": bm.calc_volume(signed=True),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return stats


def modifier_record(obj, rig):
    modifiers = list(obj.modifiers)
    armatures = [modifier for modifier in modifiers if modifier.type == "ARMATURE"]
    subds = [modifier for modifier in modifiers if modifier.type == "SUBSURF"]
    return {
        "stack": [modifier.type for modifier in modifiers],
        "one_armature": len(armatures) == 1,
        "one_subdivision": len(subds) == 1,
        "armature_targets_expected_rig": len(armatures) == 1 and armatures[0].object == rig,
        "armature_precedes_subdivision": bool(
            armatures and subds and modifiers.index(armatures[0]) < modifiers.index(subds[0])
        ),
        "preserve_volume": bool(armatures and armatures[0].use_deform_preserve_volume),
    }


def driver_record(obj):
    shape_keys = obj.data.shape_keys
    animation = shape_keys.animation_data if shape_keys else None
    drivers = list(animation.drivers) if animation else []
    corrective_path = 'key_blocks["JawSmileCorrective"].value'
    corrective = next((curve for curve in drivers if curve.data_path == corrective_path), None)
    variables = []
    if corrective is not None:
        for variable in corrective.driver.variables:
            target = variable.targets[0]
            variables.append(
                {
                    "name": variable.name,
                    "bone": target.bone_target,
                    "transform_type": target.transform_type,
                    "transform_space": target.transform_space,
                }
            )
    return {
        "driver_count": len(drivers),
        "corrective_driver_present": corrective is not None,
        "corrective_expression": corrective.driver.expression if corrective else None,
        "corrective_variables": variables,
        "expected_corrective_variables": {
            (item["name"], item["bone"], item["transform_type"])
            for item in variables
        }
        == {
            ("jaw", "Jaw", "ROT_X"),
            ("left", "Smile.L", "LOC_X"),
            ("right", "Smile.R", "LOC_X"),
        },
    }


def set_pose(rig, jaw_degrees, left_x, right_x):
    rig.pose.bones["Jaw"].rotation_mode = "XYZ"
    rig.pose.bones["Jaw"].rotation_euler.x = math.radians(jaw_degrees)
    rig.pose.bones["Smile.L"].location.x = left_x
    rig.pose.bones["Smile.R"].location.x = right_x
    bpy.context.view_layer.update()


def driver_gating(obj, rig):
    key = obj.data.shape_keys.key_blocks["JawSmileCorrective"]
    left_pose = rig.pose.bones["Smile.L"].location.x
    right_pose = rig.pose.bones["Smile.R"].location.x
    if abs(left_pose) < 1e-9 or abs(right_pose) < 1e-9:
        raise RuntimeError("saved combined pose lacks bilateral smile-control displacement")
    values = {}
    for label, jaw, left, right in (
        ("rest", 0.0, 0.0, 0.0),
        ("jaw_only", 10.0, 0.0, 0.0),
        ("smile_only", 0.0, left_pose, right_pose),
        ("combined", 10.0, left_pose, right_pose),
    ):
        set_pose(rig, jaw, left, right)
        values[label] = float(key.value)
    return values


def main():
    blend_path, report_path = arguments()
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    missing = [name for name in (*EXPECTED.keys(), *EXPECTED.values()) if bpy.data.objects.get(name) is None]
    if missing:
        raise SystemExit("missing expected objects: " + ", ".join(missing))

    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = {}
    for object_name, rig_name in EXPECTED.items():
        obj = bpy.data.objects[object_name]
        rig = bpy.data.objects[rig_name]
        base = base_topology(obj)
        modifiers = modifier_record(obj, rig)
        checks = {
            "mesh_and_armature_types": obj.type == "MESH" and rig.type == "ARMATURE",
            "required_bones": {"Jaw", "Smile.L", "Smile.R"}.issubset(rig.data.bones.keys()),
            "closed_base": base["non_manifold_edges"] == 0,
            "no_loose_base_geometry": base["loose_vertices"] == 0 and base["loose_edges"] == 0,
            "no_degenerate_base_faces": base["degenerate_faces"] == 0,
            "targeted_jaw_density": base["jaw_weighted_vertices"] >= 100,
            "weighted_jaw_region_all_quad": base["non_quad_faces_touching_weighted_jaw"] == 0,
            "modifier_stack_valid": all(value for key, value in modifiers.items() if key != "stack"),
        }
        objects[object_name] = {
            "rig": rig_name,
            "base": base,
            "modifiers": modifiers,
            "checks": checks,
        }

    corrected = bpy.data.objects["Purposeful_DrivenCorrective_Face"]
    corrected_rig = bpy.data.objects["Corrected_Face_Rig"]
    key_names = set(corrected.data.shape_keys.key_blocks.keys()) if corrected.data.shape_keys else set()
    driver = driver_record(corrected)
    gating = driver_gating(corrected, corrected_rig)

    evaluated = {}
    for object_name, rig_name in EXPECTED.items():
        rig = bpy.data.objects[rig_name]
        saved_left = rig.pose.bones["Smile.L"].location.x
        saved_right = rig.pose.bones["Smile.R"].location.x
        # The corrected rig was left in the combined state by driver_gating;
        # the other rigs retain their saved combined control positions.
        set_pose(rig, 10.0, saved_left, saved_right)
        stats = evaluated_topology(bpy.data.objects[object_name], depsgraph)
        evaluated[object_name] = {
            "stats": stats,
            "clean": stats["non_manifold_edges"] == 0
            and stats["loose_vertices"] == 0
            and stats["loose_edges"] == 0
            and stats["degenerate_faces"] == 0
            and stats["signed_volume"] > 0,
        }

    assertions = {
        "expected_objects_present": not missing,
        "all_base_checks_pass": all(all(item["checks"].values()) for item in objects.values()),
        "corrected_shape_keys_present": {"Basis", "SmileWide", "JawSmileCorrective"}.issubset(key_names),
        "corrective_driver_wired": driver["corrective_driver_present"] and driver["expected_corrective_variables"],
        "corrective_zero_at_rest": gating["rest"] < 0.01,
        "corrective_rejects_jaw_only": gating["jaw_only"] < 0.01,
        "corrective_rejects_smile_only": gating["smile_only"] < 0.01,
        "corrective_activates_combined": gating["combined"] > 0.9,
        "all_combined_evaluated_meshes_clean": all(item["clean"] for item in evaluated.values()),
    }
    report = {
        "blend_path": str(blend_path),
        "blender_version": bpy.app.version_string,
        "verification_source": "fresh-process saved datablocks and evaluated dependency graph",
        "objects": objects,
        "corrected_driver": driver,
        "driver_gating": gating,
        "combined_evaluated": evaluated,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("FACIAL_EXPRESSION_VERIFY_RESULT:" + json.dumps(report))
    raise SystemExit(0 if report["pass"] else 1)


main()
