"""Build two purpose-authored high/low pairs with live modifiers, UVs, bakes, and exports."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
import tempfile
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_production-high-low-audit"
BLENDER_OPS = ROOT / "blender_ops"
if str(BLENDER_OPS) not in sys.path:
    sys.path.insert(0, str(BLENDER_OPS))

from render_passes import render_diagnostic_pass, render_silhouette


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for item in list(bpy.data.collections):
        bpy.data.collections.remove(item)


def make_collection(name: str):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def link_only(obj, target) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    target.objects.link(obj)


def mesh_object(name: str, vertices, faces, target_collection):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target_collection.objects.link(obj)
    return obj


def rounded_profile(width: float, height: float, radius: float, segments: int = 4):
    points = []
    centers = (
        (width / 2 - radius, height / 2 - radius, 0.0),
        (-width / 2 + radius, height / 2 - radius, math.pi / 2),
        (-width / 2 + radius, -height / 2 + radius, math.pi),
        (width / 2 - radius, -height / 2 + radius, 3 * math.pi / 2),
    )
    for cx, cz, start in centers:
        for index in range(segments + 1):
            angle = start + index * (math.pi / 2) / segments
            points.append((cx + radius * math.cos(angle), cz + radius * math.sin(angle)))
    return points


def extruded_profile(name: str, points, depth: float, target_collection):
    vertices = [(x, -depth / 2, z) for x, z in points]
    vertices += [(x, depth / 2, z) for x, z in points]
    count = len(points)
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    return mesh_object(name, vertices, faces, target_collection)


def cube(name: str, dimensions, target_collection):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_Mesh"
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    link_only(obj, target_collection)
    return obj


def vessel(name: str, segments: int, rings: int, target_collection, *, detailed: bool):
    z_values = [-1.5 + index * (3.0 / (rings - 1)) for index in range(rings)]
    vertices = []
    for z in z_values:
        normalized = z / 1.5
        radius = 1.35 - 0.20 * abs(normalized) + 0.08 * math.cos(normalized * math.pi)
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            detail = 0.0
            if detailed:
                detail = 0.035 * math.sin(6 * angle) * math.exp(-((z - 0.25) / 0.4) ** 2)
            r = radius + detail
            vertices.append((r * math.cos(angle), r * math.sin(angle), z))
    bottom = len(vertices)
    vertices.append((0.0, 0.0, z_values[0]))
    top = len(vertices)
    vertices.append((0.0, 0.0, z_values[-1]))
    faces = []
    for ring in range(rings - 1):
        for index in range(segments):
            nxt = (index + 1) % segments
            a = ring * segments + index
            b = ring * segments + nxt
            c = (ring + 1) * segments + nxt
            d = (ring + 1) * segments + index
            faces.append((a, b, c, d))
    top_start = (rings - 1) * segments
    for index in range(segments):
        nxt = (index + 1) % segments
        faces.append((bottom, nxt, index))
        faces.append((top, top_start + index, top_start + nxt))
    return mesh_object(name, vertices, faces, target_collection)


def add_live_modifier(obj, width: float) -> None:
    modifier = obj.modifiers.new("Manual Bevel - Unapplied", "BEVEL")
    modifier.width = width
    modifier.segments = 2
    modifier.limit_method = "ANGLE"
    modifier.show_viewport = True
    modifier.show_render = True
    obj["modifier_application_policy"] = "LEAVE_UNAPPLIED_FOR_USER"


def activate(obj, include=()) -> None:
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for item in include:
        item.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def unwrap(obj) -> None:
    activate(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")


def image_metrics(image) -> dict:
    pixels = list(image.pixels)
    rgb = [pixels[index:index + 3] for index in range(0, len(pixels), 4)]
    occupied = [value for value in rgb if max(value) > 0.02]
    neutral = (0.5, 0.5, 1.0)
    changed = sum(
        math.sqrt(sum((value[channel] - neutral[channel]) ** 2 for channel in range(3))) > 0.03
        for value in occupied
    )
    return {
        "occupied_pixels": len(occupied),
        "non_neutral_pixels": changed,
        "channel_standard_deviation": [
            statistics.pstdev(value[channel] for value in occupied) for channel in range(3)
        ],
    }


def bake_normal(family: str, high, low) -> dict:
    image = bpy.data.images.new(
        f"{family}_Tangent_Normal", width=128, height=128, alpha=False, float_buffer=False
    )
    image.generated_color = (0.5, 0.5, 1.0, 1.0)
    image.colorspace_settings.name = "Non-Color"
    material = bpy.data.materials.new(f"{family}_Low_Material")
    material.use_nodes = True
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.name = "Active Normal Bake Target"
    texture.image = image
    material.node_tree.nodes.active = texture
    normal_map = material.node_tree.nodes.new("ShaderNodeNormalMap")
    normal_map.name = "Tangent Normal Map"
    normal_map.space = "TANGENT"
    principled = next(
        node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"
    )
    low.data.materials.append(material)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.use_clear = True
    scene.render.bake.margin = 8
    scene.render.bake.cage_extrusion = 0.10
    scene.render.bake.max_ray_distance = 0.20
    activate(low, include=(high,))
    result = bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    material.node_tree.links.new(texture.outputs["Color"], normal_map.inputs["Color"])
    material.node_tree.links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
    path = OUT / f"{family}_tangent_normal.png"
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return {
        "operator_result": sorted(result),
        "path": str(path),
        "colorspace": image.colorspace_settings.name,
        "metrics": image_metrics(image),
    }


def export_low(family: str, low) -> str:
    activate(low)
    path = OUT / f"{family}_low.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=False,
        export_materials="EXPORT",
    )
    return str(path)


def mask_hash(path: Path) -> str:
    image = bpy.data.images.load(str(path))
    try:
        packed = bytes(1 if value > 0.5 else 0 for value in image.pixels[3::4])
        return hashlib.sha256(packed).hexdigest()
    finally:
        bpy.data.images.remove(image)


def render_pair(family: str, high, low, temp_dir: Path) -> tuple[dict, list[dict]]:
    evidence = {}
    records = []
    for view in ("front", "side", "top"):
        high_path = OUT / "masks" / f"{family}_high_{view}.png"
        records.append(render_silhouette(
            high.name, str(high_path), view=view, resolution=384, margin=1.18,
            frame_name=high.name,
        ))
        high_hash = mask_hash(high_path)
        temp_low = temp_dir / f"{family}_low_{view}.png"
        record = render_silhouette(
            low.name, str(temp_low), view=view, resolution=384, margin=1.18,
            frame_name=high.name,
        )
        low_hash = mask_hash(temp_low)
        equal = low_hash == high_hash
        retained_path = None
        if not equal:
            retained = OUT / "masks" / f"{family}_low_{view}.png"
            retained.write_bytes(temp_low.read_bytes())
            retained_path = str(retained)
        record["output_path"] = retained_path
        record["retained"] = not equal
        records.append(record)
        evidence[view] = {
            "high_path": str(high_path),
            "high_mask_sha256": high_hash,
            "low_path": retained_path,
            "low_mask_sha256": low_hash,
            "equal_masks": equal,
        }
    for label, obj in (("high", high), ("low", low)):
        for view in ("front", "top"):
            path = OUT / "review" / f"{family}_{label}_{view}_wireframe.png"
            records.append(render_diagnostic_pass(
                obj.name, str(path), "wireframe", view=view, resolution=384,
                margin=1.18, frame_name=high.name,
            ))
    return evidence, records


def copy_equal_control(source, high_collection, low_collection):
    high = source.copy()
    high.data = source.data.copy()
    high.name = "Equal_Cage_HIGH"
    high.data.name = "Equal_Cage_HIGH_Mesh"
    high_collection.objects.link(high)
    low = high.copy()
    low.data = high.data.copy()
    low.name = "Equal_Cage_LOW"
    low.data.name = "Equal_Cage_LOW_Mesh"
    low_collection.objects.link(low)
    high["production_variant"] = "HIGH_POLY"
    low["production_variant"] = "LOW_POLY"
    return high, low


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    clear_scene()
    bpy.context.preferences.filepaths.save_version = 0
    high_collection = make_collection("HIGH_POLY")
    low_collection = make_collection("LOW_POLY")
    equal_high_collection = make_collection("EQUAL_HIGH")
    equal_low_collection = make_collection("EQUAL_LOW")

    box_high = extruded_profile(
        "Box_HIGH", rounded_profile(4.0, 3.0, 0.18, 4), 2.0, high_collection
    )
    box_low = cube("Box_LOW", (4.0, 2.0, 3.0), low_collection)
    box_high.location.x = box_low.location.x = -4.0
    radial_high = vessel("Radial_HIGH", 48, 17, high_collection, detailed=True)
    radial_low = vessel("Radial_LOW", 12, 5, low_collection, detailed=False)
    radial_high.location.x = radial_low.location.x = 4.0

    pairs = {
        "box": (box_high, box_low),
        "radial": (radial_high, radial_low),
    }
    for family, (high, low) in pairs.items():
        high["production_variant"] = "HIGH_POLY"
        low["production_variant"] = "LOW_POLY"
        high["retopology_scope"] = "controlled purpose-authored source"
        low["retopology_scope"] = "controlled purpose-authored low topology"
        add_live_modifier(high, 0.025)
        add_live_modifier(low, 0.025)
        unwrap(low)

    equal_high, equal_low = copy_equal_control(
        box_high, equal_high_collection, equal_low_collection
    )

    render_evidence = {}
    render_records = []
    with tempfile.TemporaryDirectory(prefix="production-high-low-", dir=OUT) as temp:
        temp_dir = Path(temp)
        for family, (high, low) in pairs.items():
            evidence, records = render_pair(family, high, low, temp_dir)
            render_evidence[family] = evidence
            render_records.extend(records)

    bakes = {family: bake_normal(family, high, low) for family, (high, low) in pairs.items()}
    exports = {family: export_low(family, low) for family, (_, low) in pairs.items()}
    bpy.context.scene["experiment"] = "production-high-low-audit"
    bpy.context.scene["pipeline_applied_modifiers"] = False
    blend_path = OUT / "production_high_low_audit.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report = {
        "blender_version": bpy.app.version_string,
        "blend_path": str(blend_path),
        "pairs": {
            family: {"high": high.name, "low": low.name}
            for family, (high, low) in pairs.items()
        },
        "equal_cage_control": {"high": equal_high.name, "low": equal_low.name},
        "render_evidence": render_evidence,
        "render_records": render_records,
        "bakes": bakes,
        "exports": exports,
        "source_modifier_policy": "All source modifiers remain live and unapplied for the user.",
        "pass": (
            all("FINISHED" in bake["operator_result"] for bake in bakes.values())
            and all(bake["metrics"]["non_neutral_pixels"] > 100 for bake in bakes.values())
            and all(Path(path).exists() for path in exports.values())
            and all("error" not in record for record in render_records)
        ),
        "claim_boundary": "Controlled authored pairs; no autonomous retopology inference.",
    }
    (OUT / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "bakes": bakes, "exports": exports}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
