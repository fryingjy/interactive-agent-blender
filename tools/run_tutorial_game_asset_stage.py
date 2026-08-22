"""Stage-7 production reproduction of CG Thoughts' stylized medical case workflow."""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-22_tutorial-cgthoughts-game-asset"
BLENDER_OPS = ROOT / "blender_ops"
for entry in (ROOT, BLENDER_OPS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from render_passes import render_diagnostic_pass, render_silhouette
from tools.run_uv_seam_production_transfer import alpha_mask, connected_components, evaluated_health, image_metrics, uv_metrics


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for item in list(bpy.data.collections):
        bpy.data.collections.remove(item)


def collection(name):
    item = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(item)
    return item


def move_only(obj, target):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)


def activate(obj, include=()):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for candidate in include:
        candidate.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def material(name, color, metallic=0.0, roughness=0.4):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    bsdf = next(node for node in result.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return result


def add_box(name, dimensions, location, target, *, high, mat):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_only(obj, target)
    if high:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=2, use_grid_fill=True)
        bm.to_mesh(obj.data)
        bm.free()
    bevel = obj.modifiers.new("Production edge radius - unapplied", "BEVEL")
    bevel.limit_method = "ANGLE"
    bevel.width = 0.16 if high else 0.14
    bevel.segments = 4 if high else 2
    bevel.harden_normals = True
    normal = obj.modifiers.new("Weighted planar normals - unapplied", "WEIGHTED_NORMAL")
    normal.keep_sharp = True
    obj.data.materials.append(mat)
    obj["production_variant"] = "HIGH_POLY" if high else "LOW_POLY"
    return obj


def rounded_sweep(name, centers, radius, segments, target, mat):
    vertices = []
    for ring, center in enumerate(centers):
        previous = Vector(centers[max(0, ring - 1)])
        following = Vector(centers[min(len(centers) - 1, ring + 1)])
        tangent = (following - previous).normalized()
        side = tangent.cross(Vector((0, 0, 1))).normalized()
        if side.length < 0.1:
            side = Vector((1, 0, 0))
        up = side.cross(tangent).normalized()
        for index in range(segments):
            angle = math.tau * index / segments
            point = Vector(center) + side * (math.cos(angle) * radius) + up * (math.sin(angle) * radius)
            vertices.append(tuple(point))
    faces = []
    for ring in range(len(centers) - 1):
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((ring * segments + index, ring * segments + nxt, (ring + 1) * segments + nxt, (ring + 1) * segments + index))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    solidify = obj.modifiers.new("Handle wall - unapplied", "SOLIDIFY")
    solidify.thickness = radius * 0.35
    solidify.offset = 0.0
    obj.data.materials.append(mat)
    return obj


def unwrap(obj):
    activate(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.03)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")


def build_variant(prefix, target, *, high, mats):
    body = add_box(f"{prefix}_body", (4.8, 3.0, 2.25), (0, 0, 0), target, high=high, mat=mats["red"])
    straps = [
        add_box(f"{prefix}_band_left", (0.42, 3.16, 2.42), (-1.62, 0, 0), target, high=high, mat=mats["white"]),
        add_box(f"{prefix}_band_right", (0.42, 3.16, 2.42), (1.62, 0, 0), target, high=high, mat=mats["white"]),
    ]
    latches = [
        add_box(f"{prefix}_latch_left", (0.72, 0.22, 0.28), (-0.78, -1.58, 0.24), target, high=high, mat=mats["dark"]),
        add_box(f"{prefix}_latch_right", (0.72, 0.22, 0.28), (0.78, -1.58, 0.24), target, high=high, mat=mats["dark"]),
    ]
    handle_centers = [
        (-1.05, 0.0, 1.18), (-1.05, 0.0, 1.55), (-0.72, 0.0, 1.82),
        (0.0, 0.0, 1.92), (0.72, 0.0, 1.82), (1.05, 0.0, 1.55), (1.05, 0.0, 1.18),
    ]
    handle = rounded_sweep(f"{prefix}_handle", handle_centers, 0.18, 16 if high else 12, target, mats["dark"])
    objects = [body, *straps, *latches, handle]
    for obj in objects:
        obj["production_variant"] = "HIGH_POLY" if high else "LOW_POLY"
        obj["modifier_application_policy"] = "LEAVE_UNAPPLIED_FOR_USER"
    return {"body": body, "objects": objects}


def target_node(material, label, colorspace):
    image = bpy.data.images.new(label, width=512, height=512, alpha=False)
    image.generated_color = (0, 0, 0, 1)
    image.colorspace_settings.name = colorspace
    node = material.node_tree.nodes.new("ShaderNodeTexImage")
    node.name = label + "_Target"
    node.image = image
    material.node_tree.nodes.active = node
    return image, node


def bake_maps(high, low):
    activate(low, include=(high,))
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.use_clear = True
    scene.render.bake.margin = 16
    scene.render.bake.cage_extrusion = 0.08
    scene.render.bake.max_ray_distance = 0.18
    low_mat = low.data.materials[0]
    outputs = {}
    for channel, bake_type, colorspace in (
        ("BaseColor", "DIFFUSE", "sRGB"),
        ("Roughness", "ROUGHNESS", "Non-Color"),
        ("Normal", "NORMAL", "Non-Color"),
    ):
        image, node = target_node(low_mat, f"medical_case_{channel}", colorspace)
        if bake_type == "DIFFUSE":
            result = bpy.ops.object.bake(type=bake_type, pass_filter={"COLOR"})
        else:
            result = bpy.ops.object.bake(type=bake_type, normal_space="TANGENT") if bake_type == "NORMAL" else bpy.ops.object.bake(type=bake_type)
        path = OUT / f"medical_case_{channel}.png"
        image.filepath_raw = str(path)
        image.file_format = "PNG"
        image.save()
        image.pack()
        outputs[channel] = {"operator_result": sorted(result), "path": str(path.relative_to(ROOT)), "colorspace": colorspace, "metrics": image_metrics(image), "node": node.name}
    metallic, metallic_node = target_node(low_mat, "medical_case_Metallic", "Non-Color")
    pixels = [0.0, 0.0, 0.0, 1.0] * (512 * 512)
    metallic.pixels.foreach_set(pixels)
    metallic.update()
    metallic_path = OUT / "medical_case_Metallic.png"
    metallic.filepath_raw = str(metallic_path)
    metallic.file_format = "PNG"
    metallic.save()
    metallic.pack()
    outputs["Metallic"] = {"operator_result": ["CONSTANT_NON_METAL"], "path": str(metallic_path.relative_to(ROOT)), "colorspace": "Non-Color", "metrics": image_metrics(metallic), "node": metallic_node.name}

    nodes, links = low_mat.node_tree.nodes, low_mat.node_tree.links
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    by_name = {node.image.name: node for node in nodes if node.type == "TEX_IMAGE" and node.image}
    links.new(by_name["medical_case_BaseColor"].outputs["Color"], bsdf.inputs["Base Color"])
    links.new(by_name["medical_case_Roughness"].outputs["Color"], bsdf.inputs["Roughness"])
    links.new(by_name["medical_case_Metallic"].outputs["Color"], bsdf.inputs["Metallic"])
    normal = nodes.new("ShaderNodeNormalMap")
    links.new(by_name["medical_case_Normal"].outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    return outputs


def silhouette_iou(high_objects, low_objects):
    scores, records = {}, []
    high_names = [obj.name for obj in high_objects]
    low_names = [obj.name for obj in low_objects]
    frame = high_names + low_names
    for view in ("front", "side", "top"):
        hp = OUT / f"high_{view}_mask.png"
        lp = OUT / f"low_{view}_mask.png"
        records.append(render_silhouette(high_names, str(hp), view=view, resolution=400, frame_name=frame))
        records.append(render_silhouette(low_names, str(lp), view=view, resolution=400, frame_name=frame))
        hm, lm = alpha_mask(hp), alpha_mask(lp)
        intersection = sum(a and b for a, b in zip(hm, lm))
        union = sum(a or b for a, b in zip(hm, lm))
        scores[view] = round(intersection / union if union else 0.0, 6)
    return scores, records


def export_low(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path = OUT / "medical_case_low.glb"
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_apply=False, export_materials="EXPORT")
    return str(path.relative_to(ROOT))


def render_material(objects, path):
    scene = bpy.context.scene
    wanted = set(objects)
    previous = {obj.name: obj.hide_render for obj in scene.objects}
    for obj in scene.objects:
        obj.hide_render = obj not in wanted
    all_points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    center = sum(all_points, Vector()) / len(all_points)
    radius = max((point - center).length for point in all_points)
    camera_data = bpy.data.cameras.new("Production_Material_Camera")
    camera = bpy.data.objects.new("Production_Material_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = center + Vector((7.0, -9.0, 6.5))
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = radius * 2.35
    scene.camera = camera
    for name, location, energy, size in (
        ("Production_Key", (4.0, -5.0, 8.0), 1000.0, 5.0),
        ("Production_Fill", (-4.0, -2.0, 4.0), 650.0, 4.0),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.size = size
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = center + Vector(location)
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    for name in ("Production_Material_Camera", "Production_Key", "Production_Fill"):
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    for obj in scene.objects:
        if obj.name in previous:
            obj.hide_render = previous[obj.name]
    return str(path.relative_to(ROOT))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    clear_scene()
    high_collection, low_collection = collection("HIGH_POLY"), collection("LOW_POLY")
    mats = {
        "red": material("Medical_Red", (0.55, 0.015, 0.008), roughness=0.32),
        "white": material("Medical_White", (0.72, 0.72, 0.68), roughness=0.38),
        "dark": material("Latch_Dark", (0.025, 0.03, 0.035), metallic=0.15, roughness=0.28),
    }
    high = build_variant("medical_case_HIGH", high_collection, high=True, mats=mats)
    low = build_variant("medical_case_LOW", low_collection, high=False, mats=mats)
    for obj in low["objects"]:
        unwrap(obj)
    maps = bake_maps(high["body"], low["body"])
    scores, records = silhouette_iou(high["objects"], low["objects"])
    records.append(render_diagnostic_pass([obj.name for obj in high["objects"]], str(OUT / "high_isometric_matcap.png"), "matcap", view="isometric", resolution=640))
    records.append(render_diagnostic_pass([obj.name for obj in low["objects"]], str(OUT / "low_isometric_wire.png"), "wireframe", view="isometric", resolution=640))
    export_path = export_low(low["objects"])
    material_render = render_material(low["objects"], OUT / "low_material_render.png")
    low_uv = {obj.name: uv_metrics(obj) for obj in low["objects"]}
    checks = {
        "separate_high_low_collections": set(obj.users_collection[0].name for obj in high["objects"]) == {"HIGH_POLY"} and set(obj.users_collection[0].name for obj in low["objects"]) == {"LOW_POLY"},
        "independent_mesh_datablocks": not any(high_obj.data is low_obj.data for high_obj in high["objects"] for low_obj in low["objects"]),
        "high_has_more_base_faces": sum(len(obj.data.polygons) for obj in high["objects"]) > sum(len(obj.data.polygons) for obj in low["objects"]),
        "modifiers_live_unapplied": all(len(obj.modifiers) > 0 for obj in high["objects"] + low["objects"]),
        "all_low_uvs_valid": all(item["layer"] and item["degenerate_faces"] == 0 and item["inside_unit_tile"] for item in low_uv.values()),
        "four_pbr_channels_saved": set(maps) == {"BaseColor", "Roughness", "Normal", "Metallic"} and all((ROOT / item["path"]).is_file() for item in maps.values()),
        "normal_bake_has_signal": maps["Normal"]["metrics"]["non_neutral_pixels"] > 1000,
        "three_view_fit": min(scores.values()) >= 0.90,
        "low_export_exists": (ROOT / export_path).is_file(),
    }
    report = {
        "schema_version": 1,
        "experiment": "cgthoughts_medical_case_full_game_asset_workflow",
        "blender_version": bpy.app.version_string,
        "source": "https://www.youtube.com/watch?v=NamnBJ4KVeU",
        "topology": {
            "high_base_faces": sum(len(obj.data.polygons) for obj in high["objects"]),
            "low_base_faces": sum(len(obj.data.polygons) for obj in low["objects"]),
            "high_components": len(high["objects"]),
            "low_components": len(low["objects"]),
            "separation_reason": "body shell, two manufactured wrap bands, two moving latches, and one handle assembly"
        },
        "low_uv": low_uv,
        "maps": maps,
        "silhouette_iou_by_view": scores,
        "export": export_path,
        "material_render": material_render,
        "checks": checks,
        "pass": all(checks.values()),
        "render_records": records,
        "claim_boundary": "Stylized medical-case workflow reproduction based on the tutorial thumbnail and audiovisual process evidence. It validates editable high/low organization, UVs, four-channel texture delivery, tangent bake, and GLB export; it is not a pixel-identical copy of the author's downloadable asset."
    }
    (OUT / "stage7_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.context.scene["pipeline_applied_modifiers"] = False
    bpy.context.scene["tutorial_stage"] = 7
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "medical_case_production.blend"))
    print(json.dumps({"checks": checks, "pass": report["pass"], "scores": scores}, indent=2))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
