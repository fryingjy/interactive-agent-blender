"""Fresh-process verification for the Blender 5.2 seam-directed UV transfer."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-16_uv-seam-production-transfer"


def components(obj) -> int:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    remaining = set(bm.verts)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            vert = stack.pop()
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    bm.free()
    return count


def evaluated_health(obj) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def corner_angle(a: Vector, center: Vector, b: Vector) -> float:
    left = (a - center).normalized()
    right = (b - center).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, left.dot(right)))))


def uv_metrics(obj) -> dict:
    mesh = obj.data
    layer = mesh.uv_layers.active
    errors = []
    degenerate_faces = 0
    all_uvs = []
    for polygon in mesh.polygons:
        uv = [layer.data[index].uv.copy() for index in polygon.loop_indices]
        xyz = [mesh.vertices[index].co.copy() for index in polygon.vertices]
        all_uvs.extend(uv)
        area = abs(sum(
            uv[index].x * uv[(index + 1) % len(uv)].y
            - uv[(index + 1) % len(uv)].x * uv[index].y
            for index in range(len(uv))
        ) * 0.5)
        degenerate_faces += area < 1e-10
        for index in range(len(uv)):
            errors.append(abs(
                corner_angle(uv[index - 1], uv[index], uv[(index + 1) % len(uv)])
                - corner_angle(xyz[index - 1], xyz[index], xyz[(index + 1) % len(xyz)])
            ))
    return {
        "mean_corner_angle_error_degrees": statistics.mean(errors),
        "max_corner_angle_error_degrees": max(errors),
        "degenerate_faces": degenerate_faces,
        "inside_unit_tile": all(
            -1e-6 <= value.x <= 1.000001 and -1e-6 <= value.y <= 1.000001
            for value in all_uvs
        ),
    }


def imported_glb(path: Path) -> dict:
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    record = {
        "operator_result": sorted(result),
        "mesh_count": len(meshes),
        "mesh_names": [obj.name for obj in meshes],
        "uv_layers": [list(obj.data.uv_layers.keys()) for obj in meshes],
        "material_counts": [len(obj.data.materials) for obj in meshes],
        "contains_high_name": any("HIGH" in obj.name.upper() for obj in imported),
    }
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    return record


def main() -> None:
    blend = OUT / "uv_seam_production_transfer.blend"
    report_path = OUT / "uv_seam_production_transfer_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    source = (ROOT / "tools" / "run_uv_seam_production_transfer.py").read_text(encoding="utf-8")
    families = {}
    for family, expected in report["families"].items():
        high = bpy.data.objects.get(expected["objects"]["high"])
        low = bpy.data.objects.get(expected["objects"]["low"])
        control = bpy.data.objects.get(expected["objects"]["no_seam_control"])
        image = bpy.data.images.get(f"{family}_Tangent_Normal")
        material = low.data.materials[0] if low and low.data.materials else None
        normal_nodes = [node for node in material.node_tree.nodes if node.type == "NORMAL_MAP"] if material else []
        image_nodes = [node for node in material.node_tree.nodes if node.type == "TEX_IMAGE"] if material else []
        families[family] = {
            "objects_exist": all((high, low, control)),
            "collections": {
                "high": [item.name for item in high.users_collection],
                "low": [item.name for item in low.users_collection],
                "control": [item.name for item in control.users_collection],
            },
            "independent_meshes": len({id(high.data), id(low.data), id(control.data)}) == 3,
            "base_faces": {"high": len(high.data.polygons), "low": len(low.data.polygons)},
            "all_quad": all(len(face.vertices) == 4 for obj in (high, low) for face in obj.data.polygons),
            "components": {"high": components(high), "low": components(low)},
            "seam_edges": sum(edge.use_seam for edge in low.data.edges),
            "control_seam_edges": sum(edge.use_seam for edge in control.data.edges),
            "uv": {
                "layer": low.data.uv_layers.active.name if low.data.uv_layers.active else None,
                "loops": len(low.data.uv_layers.active.data) if low.data.uv_layers.active else 0,
                "authored": uv_metrics(low),
                "no_seam_control": uv_metrics(control),
            },
            "modifier_stack": {
                "high": [modifier.type for modifier in high.modifiers],
                "low": [modifier.type for modifier in low.modifiers],
            },
            "manual_application_policy": {
                "high": high.get("modifier_application_policy"),
                "low": low.get("modifier_application_policy"),
            },
            "evaluated_health": {"high": evaluated_health(high), "low": evaluated_health(low)},
            "normal_bake": {
                "exists": image is not None,
                "packed": bool(image and image.packed_file),
                "non_color": bool(image and image.colorspace_settings.name == "Non-Color"),
                "image_node_uses_bake": bool(image_nodes and image_nodes[0].image is image),
                "normal_node_connected": bool(normal_nodes and normal_nodes[0].outputs["Normal"].is_linked),
            },
            "export": imported_glb(OUT / f"{family}_low.glb"),
        }

    checks = {
        "opened_expected_blend": Path(bpy.data.filepath).resolve() == blend.resolve(),
        "builder_never_applies_modifiers": "modifier_apply(" not in source,
        "scene_declares_no_pipeline_modifier_application": bpy.context.scene.get("pipeline_applied_modifiers") is False,
        "report_passed": report.get("pass") is True,
        "all_objects_exist_in_exact_collections": all(
            item["objects_exist"]
            and item["collections"]["high"] == ["HIGH_POLY"]
            and item["collections"]["low"] == ["LOW_POLY"]
            and item["collections"]["control"] == ["FAILURE_CONTROLS"]
            for item in families.values()
        ),
        "all_source_meshes_independent_connected_and_quad": all(
            item["independent_meshes"] and item["all_quad"]
            and item["components"] == {"high": 1, "low": 1}
            for item in families.values()
        ),
        "low_topology_is_materially_lower": all(
            item["base_faces"]["low"] / item["base_faces"]["high"] <= 0.30
            for item in families.values()
        ),
        "authored_seams_and_seamless_controls_persist": all(
            item["seam_edges"] > 0 and item["control_seam_edges"] == 0
            for item in families.values()
        ),
        "uv_layers_persist": all(item["uv"]["layer"] and item["uv"]["loops"] > 0 for item in families.values()),
        "authored_uvs_are_valid_and_independently_better": all(
            item["uv"]["authored"]["degenerate_faces"] == 0
            and item["uv"]["authored"]["inside_unit_tile"]
            and item["uv"]["no_seam_control"]["mean_corner_angle_error_degrees"]
            > item["uv"]["authored"]["mean_corner_angle_error_degrees"] + 0.25
            for item in families.values()
        ),
        "independent_distortion_metrics_match_report": all(
            abs(
                item["uv"]["authored"]["mean_corner_angle_error_degrees"]
                - report["families"][family]["authored_uv"]["mean_corner_angle_error_degrees"]
            ) <= 1e-6
            and abs(
                item["uv"]["no_seam_control"]["mean_corner_angle_error_degrees"]
                - report["families"][family]["no_seam_control_uv"]["mean_corner_angle_error_degrees"]
            ) <= 1e-6
            for family, item in families.items()
        ),
        "all_live_stacks_and_manual_policy_persist": all(
            item["modifier_stack"]["high"] == ["SOLIDIFY", "BEVEL"]
            and item["modifier_stack"]["low"] == ["SOLIDIFY", "BEVEL"]
            and set(item["manual_application_policy"].values()) == {"LEAVE_UNAPPLIED_FOR_USER"}
            for item in families.values()
        ),
        "all_evaluated_shells_closed_and_clean": all(
            health["non_manifold_edges"] == 0 and health["degenerate_faces"] == 0
            for item in families.values() for health in item["evaluated_health"].values()
        ),
        "all_bakes_packed_non_color_and_connected": all(all(item["normal_bake"].values()) for item in families.values()),
        "both_exports_are_low_only_meshes_with_uv_and_material": all(
            item["export"]["operator_result"] == ["FINISHED"]
            and item["export"]["mesh_count"] == 1
            and not item["export"]["contains_high_name"]
            and all(item["export"]["uv_layers"])
            and item["export"]["material_counts"] == [1]
            for item in families.values()
        ),
    }
    result = {
        "schema_version": 1,
        "verifier": "fresh_uv_seam_production_transfer",
        "blender_version": bpy.app.version_string,
        "source_blend": str(blend.relative_to(ROOT)),
        "families": families,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": "Fresh source/export integrity verification; it does not independently judge reference fidelity or professional visual quality.",
    }
    (OUT / "fresh_verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"checks": checks, "pass": result["pass"]}, indent=2))
    raise SystemExit(0 if result["pass"] else 2)


if __name__ == "__main__":
    main()
