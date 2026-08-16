"""Fresh-process verifier for the curved Bevel normal-policy lab."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

FAMILIES = ("UNIFORM_CYLINDER_12", "UNEVEN_CYLINDER_12", "UNIFORM_TAPER_16")
POLICIES = ("NO_BEVEL_BASELINE", "PLAIN_SMOOTH", "HARDEN_NORMALS", "FACE_STRENGTH_WEIGHTED")


def angle_degrees(first, second):
    dot = max(-1.0, min(1.0, first.normalized().dot(second.normalized())))
    return math.degrees(math.acos(dot))


def metrics(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        cap_errors = []
        side_errors = []
        cap_faces = 0
        side_faces = 0
        slope = (float(obj["top_radius"]) - float(obj["bottom_radius"])) / (2.0 * float(obj["half_height"]))
        for polygon in mesh.polygons:
            normal = polygon.normal.normalized()
            if abs(normal.z) > 0.95 and polygon.area > 0.5:
                cap_faces += 1
                for loop_index in polygon.loop_indices:
                    cap_errors.append(angle_degrees(mesh.corner_normals[loop_index].vector, normal))
            elif abs(normal.z) < 0.5 and polygon.area > 0.35:
                side_faces += 1
                for loop_index in polygon.loop_indices:
                    vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
                    radial = Vector((vertex.co.x, vertex.co.y, 0.0))
                    expected = Vector((radial.x, radial.y, -slope * radial.length))
                    side_errors.append(angle_degrees(mesh.corner_normals[loop_index].vector, expected))
        bm = bmesh.new()
        bm.from_mesh(mesh)
        result = {
            "vertices": len(mesh.vertices), "edges": len(mesh.edges), "faces": len(mesh.polygons),
            "cap_faces": cap_faces, "side_faces": side_faces,
            "cap_max_deg": max(cap_errors), "side_max_deg": max(side_errors),
            "custom_normal": "custom_normal" in mesh.attributes,
            "non_manifold": sum(not edge.is_manifold for edge in bm.edges),
            "degenerate": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        }
        bm.free()
        return result
    finally:
        evaluated.to_mesh_clear()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    objects = {
        family: {policy: bpy.data.objects.get(f"{family}_{policy}") for policy in POLICIES}
        for family in FAMILIES
    }
    measured = {
        family: {policy: metrics(obj) for policy, obj in policy_objects.items() if obj is not None}
        for family, policy_objects in objects.items()
    }
    stacks = {
        family: {policy: [modifier.type for modifier in obj.modifiers] for policy, obj in policy_objects.items() if obj}
        for family, policy_objects in objects.items()
    }
    expected_stacks = {
        "NO_BEVEL_BASELINE": [],
        "PLAIN_SMOOTH": ["BEVEL"],
        "HARDEN_NORMALS": ["BEVEL"],
        "FACE_STRENGTH_WEIGHTED": ["BEVEL", "WEIGHTED_NORMAL"],
    }
    uniform = measured.get("UNIFORM_CYLINDER_12", {})
    uneven = measured.get("UNEVEN_CYLINDER_12", {})
    taper = measured.get("UNIFORM_TAPER_16", {})
    assertions = {
        "all_twelve_objects_exist": all(obj is not None for family in objects.values() for obj in family.values()),
        "all_modifier_stacks_remain_live_and_ordered": all(
            stacks.get(family, {}).get(policy) == expected_stacks[policy]
            for family in FAMILIES for policy in POLICIES
        ),
        "harden_flags_persist": all(objects[family]["HARDEN_NORMALS"].modifiers[0].harden_normals for family in FAMILIES),
        "face_influence_flags_persist": all(objects[family]["FACE_STRENGTH_WEIGHTED"].modifiers[-1].use_face_influence for family in FAMILIES),
        "all_meshes_closed_and_nondegenerate": len(measured) == 3 and all(
            item["non_manifold"] == 0 and item["degenerate"] == 0
            for family in measured.values() for item in family.values()
        ),
        "all_expected_panels_resampled": all(
            item["cap_faces"] == 2 and item["side_faces"] == int(objects[family][policy]["source_segment_count"])
            for family, policy_items in measured.items() for policy, item in policy_items.items()
        ),
        "plain_bevel_distorts_caps": all(measured[family]["PLAIN_SMOOTH"]["cap_max_deg"] > 8.0 for family in FAMILIES),
        "both_policies_restore_caps": all(
            measured[family][policy]["cap_max_deg"] < 0.001
            for family in FAMILIES for policy in ("HARDEN_NORMALS", "FACE_STRENGTH_WEIGHTED")
        ),
        "harden_restores_each_unbeveled_side_baseline": all(
            abs(measured[family]["HARDEN_NORMALS"]["side_max_deg"] - measured[family]["NO_BEVEL_BASELINE"]["side_max_deg"]) < 0.05
            for family in FAMILIES
        ),
        "uniform_and_taper_corrected_side_error_is_sub_tenth_degree": all(
            measured[family][policy]["side_max_deg"] < 0.1
            for family in ("UNIFORM_CYLINDER_12", "UNIFORM_TAPER_16")
            for policy in ("HARDEN_NORMALS", "FACE_STRENGTH_WEIGHTED")
        ),
        "uneven_baseline_exposes_density_error": 4.9 < uneven["NO_BEVEL_BASELINE"]["side_max_deg"] < 5.1,
        "uneven_weighted_normal_worsens_side_error": (
            uneven["FACE_STRENGTH_WEIGHTED"]["side_max_deg"] > uneven["PLAIN_SMOOTH"]["side_max_deg"] + 0.5
            and uneven["FACE_STRENGTH_WEIGHTED"]["side_max_deg"] > uneven["NO_BEVEL_BASELINE"]["side_max_deg"] + 4.5
        ),
        "equal_segment_count_does_not_equal_equal_curvature_quality": (
            objects["UNIFORM_CYLINDER_12"]["NO_BEVEL_BASELINE"]["source_segment_count"]
            == objects["UNEVEN_CYLINDER_12"]["NO_BEVEL_BASELINE"]["source_segment_count"] == 12
            and uniform["NO_BEVEL_BASELINE"]["side_max_deg"] < 0.1
            and uneven["NO_BEVEL_BASELINE"]["side_max_deg"] > 4.9
        ),
        "taper_fixture_is_present_and_measured": bool(taper),
    }
    result = {
        "verification": "fresh_process_curved_bevel_normal_policy",
        "blend": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "modifier_stacks": stacks,
        "metrics": measured,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "claim_boundary": "Independent saved-file verification of controlled radial fixtures. It verifies live stack state and numeric outcomes, not unfamiliar-asset quality or arbitrary curved topology.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("CURVED_BEVEL_NORMAL_POLICY_FRESH_VERIFY:" + json.dumps(result))
    raise SystemExit(0 if result["pass"] else 2)


if __name__ == "__main__":
    main()
