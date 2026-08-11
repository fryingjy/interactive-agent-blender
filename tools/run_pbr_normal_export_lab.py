"""Controlled UV/PBR normal-map GLB export and re-import verification."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_pbr-normal-export"


def stats(obj):
    obj.data.calc_loop_triangles()
    world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "triangles": len(obj.data.loop_triangles),
        "uv_layers": [layer.name for layer in obj.data.uv_layers],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "bounds": {
            axis: [min(point[index] for point in world_corners), max(point[index] for point in world_corners)]
            for index, axis in enumerate("xyz")
        },
    }


def material_state(material):
    nodes = list(material.node_tree.nodes) if material and material.node_tree else []
    principled = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    normal = next((node for node in nodes if node.type == "NORMAL_MAP"), None)
    textures = [node for node in nodes if node.type == "TEX_IMAGE"]
    return {
        "node_types": sorted(node.type for node in nodes),
        "normal_map_nodes": len([node for node in nodes if node.type == "NORMAL_MAP"]),
        "image_texture_nodes": len(textures),
        "normal_linked_to_principled": bool(
            principled and principled.inputs["Normal"].is_linked and
            principled.inputs["Normal"].links[0].from_node.type == "NORMAL_MAP"
        ),
        "normal_texture_linked": bool(normal and normal.inputs["Color"].is_linked),
        "roughness": principled.inputs["Roughness"].default_value if principled else None,
        "images": [
            {
                "name": node.image.name if node.image else None,
                "size": list(node.image.size) if node.image else None,
                "colorspace": node.image.colorspace_settings.name if node.image else None,
                "packed": bool(node.image and node.image.packed_file),
            }
            for node in textures
        ],
    }


def create_normal_image(path):
    size = 32
    image = bpy.data.images.new("Engine_Normal", width=size, height=size, alpha=False, float_buffer=False)
    pixels = []
    for y in range(size):
        for x in range(size):
            nx = 0.18 * math.sin(2.0 * math.pi * x / size)
            ny = 0.18 * math.cos(2.0 * math.pi * y / size)
            nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
            pixels.extend((nx * 0.5 + 0.5, ny * 0.5 + 0.5, nz * 0.5 + 0.5, 1.0))
    image.pixels = pixels
    image.colorspace_settings.name = "Non-Color"
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.ops.mesh.primitive_cube_add()
    source = bpy.context.object
    source.name = "PBR_Normal_Source"
    source.scale = (1.4, 0.8, 0.55)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = source.modifiers.new("Production Bevel", "BEVEL")
    bevel.width = 0.12
    bevel.segments = 2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")
    source.data.uv_layers.active.name = "EngineUV"

    normal_image = create_normal_image(OUT / "engine_normal.png")
    material = bpy.data.materials.new("PBR_Normal_Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = (0.16, 0.34, 0.72, 1.0)
    principled.inputs["Metallic"].default_value = 0.2
    principled.inputs["Roughness"].default_value = 0.38
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Packed Tangent Normal"
    texture.image = normal_image
    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "Tangent Normal Decode"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.65
    links.new(texture.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], principled.inputs["Normal"])
    source.data.materials.append(material)

    source_state = {"mesh": stats(source), "material": material_state(material)}
    glb_path = OUT / "pbr_normal_asset.glb"
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    export_result = bpy.ops.export_scene.gltf(
        filepath=str(glb_path), export_format="GLB", use_selection=True, export_apply=True
    )

    source.hide_set(True)
    bpy.ops.object.select_all(action="DESELECT")
    import_result = bpy.ops.import_scene.gltf(filepath=str(glb_path))
    imported_meshes = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
    imported = imported_meshes[0] if len(imported_meshes) == 1 else None
    imported_state = {
        "mesh": stats(imported) if imported else None,
        "material": material_state(imported.material_slots[0].material) if imported and imported.material_slots else None,
    }
    source_bounds = source_state["mesh"]["bounds"]
    imported_bounds = imported_state["mesh"]["bounds"] if imported_state["mesh"] else {}
    bounds_match = all(
        abs(source_bounds[axis][index] - imported_bounds[axis][index]) < 1e-5
        for axis in "xyz" for index in (0, 1)
    ) if imported_bounds else False
    imported_material = imported_state["material"] or {}
    assertions = {
        "normal_texture_file_written": (OUT / "engine_normal.png").stat().st_size > 0,
        "source_has_engine_uv": source_state["mesh"]["uv_layers"] == ["EngineUV"],
        "source_normal_chain_complete": source_state["material"]["normal_linked_to_principled"] and source_state["material"]["normal_texture_linked"],
        "source_image_is_non_color_and_packed": source_state["material"]["images"][0]["colorspace"] == "Non-Color" and source_state["material"]["images"][0]["packed"],
        "glb_written": "FINISHED" in export_result and glb_path.stat().st_size > 0,
        "one_mesh_reimported": "FINISHED" in import_result and len(imported_meshes) == 1,
        "roundtrip_surface_and_bounds_match": bool(imported and imported_state["mesh"]["triangles"] == source_state["mesh"]["triangles"] and bounds_match),
        "roundtrip_uv_and_material_present": bool(imported and imported_state["mesh"]["uv_layers"] and imported_state["mesh"]["materials"]),
        "roundtrip_normal_semantics_preserved": bool(imported_material.get("normal_linked_to_principled") and imported_material.get("normal_texture_linked")),
        "roundtrip_roughness_preserved": abs((imported_material.get("roughness") or 0.0) - 0.38) < 1e-4,
        "roundtrip_normal_image_present": bool(imported_material.get("images") and imported_material["images"][0]["size"] == [32, 32]),
    }
    report = {
        "lab": "pbr_normal_map_glb_roundtrip",
        "blender_version": bpy.app.version_string,
        "source": source_state,
        "export": {"operator_result": sorted(export_result), "path": str(glb_path), "bytes": glb_path.stat().st_size},
        "import": {
            "operator_result": sorted(import_result), "mesh_count": len(imported_meshes),
            "object_name": imported.name if imported else None, **imported_state,
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (OUT / "pbr_normal_export_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "pbr_normal_export_lab.blend"))
    print("PBR_NORMAL_EXPORT_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("one or more assertions failed")


if __name__ == "__main__":
    main()
