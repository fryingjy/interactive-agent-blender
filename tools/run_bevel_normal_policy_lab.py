"""Compare Bevel normal policies under Blender 5.2 Workbench and evaluated normals."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-16_bevel-normal-policy"
BLEND = OUT / "bevel_normal_policy.blend"
REPORT = OUT / "lab_report.json"
RENDER = OUT / "bevel_normal_policy_solid.png"


def make_variant(name: str, x: float, policy: str) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(x, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    obj.color = {
        "PLAIN_SMOOTH": (0.45, 0.55, 0.68, 1.0),
        "HARDEN_NORMALS": (0.38, 0.68, 0.52, 1.0),
        "FACE_STRENGTH_WEIGHTED": (0.73, 0.53, 0.32, 1.0),
    }[policy]
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    bevel = obj.modifiers.new("Physical edge radius", "BEVEL")
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(30.0)
    bevel.width = 0.18
    bevel.segments = 3
    if policy == "HARDEN_NORMALS":
        bevel.harden_normals = True
    elif policy == "FACE_STRENGTH_WEIGHTED":
        bevel.face_strength_mode = "FSTR_AFFECTED"
        weighted = obj.modifiers.new("Panel-biased normals", "WEIGHTED_NORMAL")
        weighted.mode = "FACE_AREA_WITH_ANGLE"
        weighted.keep_sharp = True
        weighted.use_face_influence = True
        weighted.weight = 50
    obj["normal_policy"] = policy
    return obj


def evaluated_metrics(obj: bpy.types.Object) -> dict[str, object]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        mesh.calc_loop_triangles()
        panel_faces = sorted(mesh.polygons, key=lambda polygon: polygon.area, reverse=True)[:6]
        panel_errors = []
        for polygon in panel_faces:
            face_normal = polygon.normal.normalized()
            for loop_index in polygon.loop_indices:
                corner_normal = mesh.corner_normals[loop_index].vector.normalized()
                dot = max(-1.0, min(1.0, face_normal.dot(corner_normal)))
                panel_errors.append(math.degrees(math.acos(dot)))
        bm = bmesh.new()
        bm.from_mesh(mesh)
        non_manifold = sum(not edge.is_manifold for edge in bm.edges)
        degenerate = sum(face.calc_area() <= 1e-12 for face in bm.faces)
        bm.free()
        return {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "panel_face_areas": [polygon.area for polygon in panel_faces],
            "panel_corner_normal_error_mean_deg": sum(panel_errors) / len(panel_errors),
            "panel_corner_normal_error_max_deg": max(panel_errors),
            "custom_normal_attribute": "custom_normal" in mesh.attributes,
            "non_manifold_edges": non_manifold,
            "degenerate_faces": degenerate,
        }
    finally:
        evaluated.to_mesh_clear()


def point_camera(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def render_scene() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 420
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER)
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_specular_highlight = True
    scene.display.shading.background_type = "WORLD"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Review_World")
    scene.world.color = (0.035, 0.045, 0.06)
    camera_data = bpy.data.cameras.new("Review_Camera")
    camera = bpy.data.objects.new("Review_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (7.6, -11.5, 7.0)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 9.2
    point_camera(camera, Vector((0.0, 0.0, 0.0)))
    scene.camera = camera
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    variants = [
        make_variant("Plain_Smooth_Bevel", -2.8, "PLAIN_SMOOTH"),
        make_variant("Harden_Normals_Bevel", 0.0, "HARDEN_NORMALS"),
        make_variant("Face_Strength_Weighted_Normal", 2.8, "FACE_STRENGTH_WEIGHTED"),
    ]
    bpy.context.view_layer.update()
    metrics = {obj["normal_policy"]: evaluated_metrics(obj) for obj in variants}
    plain = metrics["PLAIN_SMOOTH"]
    hardened = metrics["HARDEN_NORMALS"]
    weighted = metrics["FACE_STRENGTH_WEIGHTED"]
    topology = {(item["vertices"], item["edges"], item["faces"]) for item in metrics.values()}
    assertions = {
        "all_variants_share_evaluated_topology": len(topology) == 1,
        "all_variants_closed_and_nondegenerate": all(item["non_manifold_edges"] == 0 and item["degenerate_faces"] == 0 for item in metrics.values()),
        "plain_smooth_bends_panel_corner_normals": plain["panel_corner_normal_error_max_deg"] > 1.0,
        "harden_normals_reduces_panel_error": hardened["panel_corner_normal_error_max_deg"] < plain["panel_corner_normal_error_max_deg"],
        "weighted_face_influence_reduces_panel_error": weighted["panel_corner_normal_error_max_deg"] < plain["panel_corner_normal_error_max_deg"],
        "hardened_panel_error_is_sub_degree": hardened["panel_corner_normal_error_max_deg"] < 1.0,
        "weighted_panel_error_is_sub_degree": weighted["panel_corner_normal_error_max_deg"] < 1.0,
        "hardened_evaluated_mesh_has_custom_normals": hardened["custom_normal_attribute"],
        "weighted_evaluated_mesh_has_custom_normals": weighted["custom_normal_attribute"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    render_scene()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report = {
        "blender_version": bpy.app.version_string,
        "official_sources": [
            "https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html",
            "https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/weighted_normal.html",
        ],
        "variant_order_left_to_right": [obj["normal_policy"] for obj in variants],
        "metrics": metrics,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "claim_boundary": "A matched cube fixture measuring large-panel corner normals. It establishes the documented normal-policy effects in Blender 5.2, not a universal recommendation or a substitute for geometry, reference judgment, or semantic edge selection.",
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    raise SystemExit(0 if report["pass"] else 2)


main()
