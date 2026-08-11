"""Package the seam-authored tangent bake for a real Godot import test.

Run with Blender in background mode. The script opens the existing UV/bake lab,
exports a correctly wired GLB, and exports a deliberate material-semantic failure
whose identical normal image is incorrectly wired as base color.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE_BLEND = ROOT / "runs" / "2026-08-10_uv-bake-learning" / "uv_bake_learning_lab.blend"
OUT = ROOT / "runs" / "2026-08-11_godot-engine-validation"


def make_material(name: str, image: bpy.types.Image, *, valid_normal_semantics: bool):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = (0.18, 0.24, 0.32, 1.0)
    principled.inputs["Metallic"].default_value = 0.15
    principled.inputs["Roughness"].default_value = 0.42
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Seam Authored Tangent Bake"
    texture.image = image
    if valid_normal_semantics:
        normal = nodes.new("ShaderNodeNormalMap")
        normal.name = "Tangent Normal Decode"
        normal.space = "TANGENT"
        links.new(texture.outputs["Color"], normal.inputs["Color"])
        links.new(normal.outputs["Normal"], principled.inputs["Normal"])
    else:
        # Deliberate control failure: the same Non-Color tangent-vector pixels are
        # treated as display color, so neither normal semantics nor tangents export.
        links.new(texture.outputs["Color"], principled.inputs["Base Color"])
    return material


def export_one(obj: bpy.types.Object, path: Path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.hide_render = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    result = bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_tangents=True,
    )
    return sorted(result)


def mesh_state(obj: bpy.types.Object):
    world = obj.matrix_world
    corners = [world @ obj.data.vertices[index].co for index in range(len(obj.data.vertices))]
    return {
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "uv_layers": [layer.name for layer in obj.data.uv_layers],
        "dimensions_blender_xyz": list(obj.dimensions),
        "bounds_blender_xyz": [
            [min(point[axis] for point in corners), max(point[axis] for point in corners)]
            for axis in range(3)
        ],
        "scale": list(obj.scale),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
    low = bpy.data.objects["UV_Bake_Low"]
    image = bpy.data.images["Housing_Tangent_Normal"]
    image.colorspace_settings.name = "Non-Color"
    image.filepath = str(OUT.parent / "2026-08-10_uv-bake-learning" / "housing_tangent_normal.png")

    for material in list(low.data.materials):
        low.data.materials.pop(index=0)
    success_material = make_material("Godot_Tangent_Bake_Valid", image, valid_normal_semantics=True)
    low.data.materials.append(success_material)
    low.name = "Godot_Tangent_Bake_Valid"
    success_path = OUT / "godot_tangent_bake_valid.glb"
    success_result = export_one(low, success_path)

    failure = low.copy()
    failure.data = low.data.copy()
    bpy.context.scene.collection.objects.link(failure)
    failure.name = "Godot_Tangent_Bake_Invalid_Color_Wiring"
    failure.data.materials.clear()
    failure_material = make_material("Godot_Tangent_Bake_Invalid_Color_Wiring", image, valid_normal_semantics=False)
    failure.data.materials.append(failure_material)
    low.hide_set(True)
    failure_path = OUT / "godot_tangent_bake_invalid_color_wiring.glb"
    failure_result = export_one(failure, failure_path)

    assertions = {
        "source_image_is_non_color": image.colorspace_settings.name == "Non-Color",
        "source_has_authored_uv": bool(low.data.uv_layers),
        "source_transform_scale_is_applied": all(abs(value - 1.0) < 1e-8 for value in low.scale),
        "valid_export_finished": "FINISHED" in success_result and success_path.stat().st_size > 0,
        "invalid_control_export_finished": "FINISHED" in failure_result and failure_path.stat().st_size > 0,
    }
    report = {
        "lab": "godot_tangent_bake_packaging",
        "blender_version": bpy.app.version_string,
        "source_blend": str(SOURCE_BLEND),
        "source": mesh_state(low),
        "normal_image": {
            "name": image.name,
            "size": list(image.size),
            "colorspace": image.colorspace_settings.name,
        },
        "exports": {
            "valid": {"path": str(success_path), "bytes": success_path.stat().st_size, "result": success_result},
            "invalid_color_wiring": {"path": str(failure_path), "bytes": failure_path.stat().st_size, "result": failure_result},
        },
        "failure_control": "same tangent-normal pixels wired to Base Color instead of a tangent Normal Map node",
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (OUT / "blender_export_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("GODOT_TANGENT_PACKAGE_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
