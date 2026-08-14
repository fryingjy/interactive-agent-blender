"""Controlled UV, material, sculpt/remesh, and production-organization lab."""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix


def output_directory():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected one OUTPUT_DIR after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def active(obj):
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def cube(name, location, scale=(1, 1, 1), apply_scale=False):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if apply_scale:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def mark_box_seams(obj):
    for edge in obj.data.edges:
        a, b = (obj.data.vertices[index].co for index in edge.vertices)
        horizontal = abs(a.z - b.z) < 1e-8
        one_vertical = abs(a.x + 1.0) < 1e-6 and abs(a.y + 1.0) < 1e-6 and abs(b.x + 1.0) < 1e-6 and abs(b.y + 1.0) < 1e-6
        edge.use_seam = horizontal or one_vertical


def unwrap(obj, method="ANGLE_BASED", seams=True):
    active(obj)
    if seams:
        mark_box_seams(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    if method == "SMART_PROJECT":
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    else:
        bpy.ops.uv.unwrap(method=method, margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")


def polygon_world_area(obj, polygon):
    points = [obj.matrix_world @ obj.data.vertices[index].co for index in polygon.vertices]
    if len(points) < 3:
        return 0.0
    return sum(((points[index] - points[0]).cross(points[index + 1] - points[0])).length * 0.5 for index in range(1, len(points) - 1))


def uv_metrics(obj):
    layer = obj.data.uv_layers.active
    if layer is None:
        return {"uv_layer": False}
    ratios = []
    uv_areas = []
    all_uvs = []
    for polygon in obj.data.polygons:
        coords = [layer.data[index].uv.copy() for index in polygon.loop_indices]
        all_uvs.extend(coords)
        uv_area = abs(sum(coords[index].x * coords[(index + 1) % len(coords)].y - coords[(index + 1) % len(coords)].x * coords[index].y for index in range(len(coords))) * 0.5)
        world_area = polygon_world_area(obj, polygon)
        uv_areas.append(uv_area)
        if world_area > 1e-12:
            ratios.append(uv_area / world_area)
    mean_ratio = statistics.mean(ratios)
    return {
        "uv_layer": True,
        "seam_edges": sum(edge.use_seam for edge in obj.data.edges),
        "uv_bounds": {
            "u": [min(uv.x for uv in all_uvs), max(uv.x for uv in all_uvs)],
            "v": [min(uv.y for uv in all_uvs), max(uv.y for uv in all_uvs)],
        },
        "minimum_face_uv_area": min(uv_areas),
        "maximum_face_uv_area": max(uv_areas),
        "world_texel_ratio_cv": statistics.pstdev(ratios) / mean_ratio if mean_ratio > 0 else None,
        "all_uvs_inside_unit_tile": all(-1e-6 <= uv.x <= 1.000001 and -1e-6 <= uv.y <= 1.000001 for uv in all_uvs),
    }


def nonzero_uv_loops(obj):
    layer = obj.data.uv_layers.active
    if layer is None:
        return 0
    return sum(abs(item.uv.x) > 1e-8 or abs(item.uv.y) > 1e-8 for item in layer.data)


def principled_material(name, color, roughness, metallic=0.0, set_node=True):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (*color, 1.0)
    principled = material.node_tree.nodes.get("Principled BSDF")
    if set_node:
        principled.inputs["Base Color"].default_value = (*color, 1.0)
        principled.inputs["Roughness"].default_value = roughness
        principled.inputs["Metallic"].default_value = metallic
    return material


def material_metrics(obj):
    slots = list(obj.data.materials)
    used = {polygon.material_index for polygon in obj.data.polygons}
    records = []
    for index, material in enumerate(slots):
        principled = material.node_tree.nodes.get("Principled BSDF") if material and material.use_nodes else None
        output = material.node_tree.nodes.get("Material Output") if material and material.use_nodes else None
        connected = False
        if principled and output:
            connected = any(link.from_node == principled and link.to_node == output for link in material.node_tree.links)
        records.append({
            "slot": index,
            "name": material.name if material else None,
            "used": index in used,
            "principled_connected": connected,
            "diffuse_color": list(material.diffuse_color) if material else None,
            "principled_base_color": list(principled.inputs["Base Color"].default_value) if principled else None,
            "roughness": principled.inputs["Roughness"].default_value if principled else None,
            "metallic": principled.inputs["Metallic"].default_value if principled else None,
        })
    return {"slots": records, "orphan_slot_count": sum(not record["used"] for record in records)}


def mesh_metrics(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            return {
                "vertices": len(bm.verts),
                "edges": len(bm.edges),
                "faces": len(bm.faces),
                "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                "ngons": sum(len(face.verts) > 4 for face in bm.faces),
                "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def lumpy_sculpt_source(name, location):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0, matrix=Matrix.Identity(4))
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.75, matrix=Matrix.Translation((0.8, 0, 0)))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def production_audit(collection):
    objects = list(collection.objects)
    return {
        "object_count": len(objects),
        "unnamed_objects": [obj.name for obj in objects if obj.name.startswith(("Cube", "Sphere", "Plane"))],
        "unapplied_scale": [obj.name for obj in objects if any(abs(value - 1.0) > 1e-6 for value in obj.scale)],
        "unnamed_modifiers": [f"{obj.name}:{mod.name}" for obj in objects for mod in obj.modifiers if mod.name == mod.type.title()],
        "hidden_objects": [obj.name for obj in objects if obj.hide_viewport or obj.hide_render],
    }


def main():
    output = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    records = []

    uv_unapplied = cube("UV_UnappliedScale", (-8, 4, 0), scale=(2.0, 1.0, 0.5), apply_scale=False)
    unwrap(uv_unapplied)
    unapplied_uv = uv_metrics(uv_unapplied)
    records.append({"object": uv_unapplied.name, "category": "uv", "case": "seam unwrap with unapplied non-uniform scale", "metrics": unapplied_uv})

    uv_applied = cube("UV_AppliedScale", (-3, 4, 0), scale=(2.0, 1.0, 0.5), apply_scale=True)
    unwrap(uv_applied)
    applied_uv = uv_metrics(uv_applied)
    records.append({"object": uv_applied.name, "category": "uv", "case": "seam unwrap after applying non-uniform scale", "metrics": applied_uv})

    uv_smart = cube("UV_SmartProject", (2, 4, 0))
    unwrap(uv_smart, method="SMART_PROJECT", seams=False)
    smart_uv = uv_metrics(uv_smart)
    records.append({"object": uv_smart.name, "category": "uv", "case": "Smart UV Project packed layout", "metrics": smart_uv})

    diffuse_only = cube("Material_DiffuseOnly", (-8, 0, 0))
    diffuse_material = principled_material("DiffuseMetadataOnly", (0.8, 0.05, 0.02), 0.25, set_node=False)
    diffuse_only.data.materials.append(diffuse_material)
    diffuse_metrics = material_metrics(diffuse_only)
    records.append({"object": diffuse_only.name, "category": "material", "case": "diffuse metadata changed but Principled Base Color untouched", "metrics": diffuse_metrics})

    principled_obj = cube("Material_PrincipledConnected", (-4, 0, 0))
    principled = principled_material("PaintedMetal", (0.08, 0.2, 0.7), 0.32, metallic=0.85, set_node=True)
    principled_obj.data.materials.append(principled)
    principled_metrics = material_metrics(principled_obj)
    records.append({"object": principled_obj.name, "category": "material", "case": "Principled PBR values set on connected shader", "metrics": principled_metrics})

    orphan = cube("Material_OrphanSlot", (0, 0, 0))
    orphan.data.materials.append(principled_material("Used", (0.2, 0.2, 0.2), 0.5))
    orphan.data.materials.append(principled_material("Unused", (0.8, 0.8, 0.8), 0.5))
    orphan_metrics = material_metrics(orphan)
    records.append({"object": orphan.name, "category": "material", "case": "second slot exists but no polygon uses it", "metrics": orphan_metrics})

    assigned = cube("Material_AssignedSlots", (4, 0, 0))
    assigned.data.materials.append(principled_material("Body", (0.2, 0.25, 0.3), 0.55))
    assigned.data.materials.append(principled_material("Accent", (0.8, 0.2, 0.05), 0.3))
    for polygon in assigned.data.polygons:
        polygon.material_index = polygon.index % 2
    assigned_metrics = material_metrics(assigned)
    records.append({"object": assigned.name, "category": "material", "case": "both slots assigned reproducibly", "metrics": assigned_metrics})

    multires = cube("Sculpt_MultiresFoundation", (8, 0, 0))
    active(multires)
    modifier = multires.modifiers.new("Sculpt Multires", "MULTIRES")
    bpy.ops.object.multires_subdivide(modifier=modifier.name, mode="CATMULL_CLARK")
    bpy.ops.object.multires_subdivide(modifier=modifier.name, mode="CATMULL_CLARK")
    multires_metrics = mesh_metrics(multires)
    records.append({"object": multires.name, "category": "sculpt", "case": "two Multires levels for non-destructive sculpt detail", "modifier_levels": modifier.total_levels, "metrics": multires_metrics})

    remesh = lumpy_sculpt_source("Sculpt_VoxelRemesh", (0, -5, 0))
    remesh_uv = remesh.data.uv_layers.new(name="PreRemeshUV")
    for loop in remesh.data.loops:
        coordinate = remesh.data.vertices[loop.vertex_index].co
        remesh_uv.data[loop.index].uv = (coordinate.x * 0.25 + 0.5, coordinate.y * 0.25 + 0.5)
    before = mesh_metrics(remesh)
    before_uv_layers = len(remesh.data.uv_layers)
    before_nonzero_uv_loops = nonzero_uv_loops(remesh)
    active(remesh)
    remesh.data.remesh_voxel_size = 0.22
    bpy.ops.object.voxel_remesh()
    after = mesh_metrics(remesh)
    after_uv_layers = len(remesh.data.uv_layers)
    after_nonzero_uv_loops = nonzero_uv_loops(remesh)
    records.append({"object": remesh.name, "category": "sculpt", "case": "voxel remesh overlapping sculpt masses", "before": before, "after": after, "uv_layers_before": before_uv_layers, "uv_layers_after": after_uv_layers, "nonzero_uv_loops_before": before_nonzero_uv_loops, "nonzero_uv_loops_after": after_nonzero_uv_loops})

    production = bpy.data.collections.new("Production_Ready")
    bpy.context.scene.collection.children.link(production)
    prod = cube("PROD_MainBody", (7, -5, 0), apply_scale=True)
    for collection in list(prod.users_collection):
        collection.objects.unlink(prod)
    production.objects.link(prod)
    bevel = prod.modifiers.new("Primary Edge Softening", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 2
    audit = production_audit(production)
    records.append({"object": prod.name, "category": "production", "case": "named collection/object/modifier with clean transforms", "audit": audit})

    diffuse_slot = diffuse_metrics["slots"][0]
    principled_slot = principled_metrics["slots"][0]
    assertions = {
        "applied_scale_improves_world_texel_consistency": applied_uv["world_texel_ratio_cv"] < unapplied_uv["world_texel_ratio_cv"],
        "smart_project_packs_inside_unit_tile": smart_uv["all_uvs_inside_unit_tile"],
        "diffuse_metadata_does_not_change_principled_base": diffuse_slot["diffuse_color"] != diffuse_slot["principled_base_color"],
        "principled_shader_is_connected": principled_slot["principled_connected"],
        "pbr_values_reach_principled_inputs": abs(principled_slot["roughness"] - 0.32) < 1e-6 and abs(principled_slot["metallic"] - 0.85) < 1e-6,
        "orphan_slot_is_detected": orphan_metrics["orphan_slot_count"] == 1,
        "assigned_slots_have_no_orphans": assigned_metrics["orphan_slot_count"] == 0,
        "multires_has_two_levels": modifier.total_levels == 2 and multires_metrics["vertices"] > len(multires.data.vertices),
        "voxel_remesh_changes_topology": after["vertices"] != before["vertices"],
        "voxel_remesh_produces_manifold_result": after["non_manifold_edges"] == 0,
        "pre_remesh_uv_data_was_meaningful": before_nonzero_uv_loops > 0,
        "production_audit_is_clean": not any(audit[key] for key in ("unnamed_objects", "unapplied_scale", "unnamed_modifiers", "hidden_objects")),
    }
    report = {
        "lab": "uv_material_sculpt_production",
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode("utf-8"),
        "records": records,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (output / "uv_material_sculpt_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "uv_material_sculpt_lab.blend"))
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("one or more UV/material/sculpt assertions failed")


if __name__ == "__main__":
    main()
