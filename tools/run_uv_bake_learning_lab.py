"""Reproduce seam-authored UV reasoning and a real high-to-low tangent normal bake."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_uv-bake-learning"


def vessel_mesh(name, *, segments, z_values, detailed=False):
    vertices = []
    for z in z_values:
        if z < -1.2:
            radius = 0.7 + (z + 1.5) * (0.2 / 0.3)
        elif z > 1.0:
            radius = 0.9 - (z - 1.0) * (0.2 / 0.3)
        else:
            radius = 0.9
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            detail = 0.0
            if detailed:
                detail += 0.035 * math.sin(8.0 * angle) * math.exp(-((z - 0.15) / 0.28) ** 2)
                detail += 0.025 * math.exp(-((z + 0.72) / 0.06) ** 2)
            r = radius + detail
            vertices.append((r * math.cos(angle), r * math.sin(angle), z))
    bottom_center = len(vertices)
    vertices.append((0.0, 0.0, z_values[0]))
    top_center = len(vertices)
    vertices.append((0.0, 0.0, z_values[-1]))
    faces = []
    for ring in range(len(z_values) - 1):
        for index in range(segments):
            nxt = (index + 1) % segments
            a = ring * segments + index
            b = ring * segments + nxt
            c = (ring + 1) * segments + nxt
            d = (ring + 1) * segments + index
            faces.append((a, b, c, d))
    top_start = (len(z_values) - 1) * segments
    for index in range(segments):
        nxt = (index + 1) % segments
        faces.append((bottom_center, nxt, index))
        faces.append((top_center, top_start + index, top_start + nxt))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def activate(obj, *, include=()):
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="DESELECT")
    for item in include:
        item.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def mark_authored_seams(obj, segments, ring_count):
    cap_pairs = set()
    for ring in (0, ring_count - 1):
        for index in range(segments):
            cap_pairs.add(frozenset((ring * segments + index, ring * segments + (index + 1) % segments)))
    longitudinal_pairs = {
        frozenset((ring * segments, (ring + 1) * segments))
        for ring in range(ring_count - 1)
    }
    for edge in obj.data.edges:
        edge.use_seam = frozenset(edge.vertices) in cap_pairs or frozenset(edge.vertices) in longitudinal_pairs


def unwrap(obj):
    activate(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")


def uv_metrics(obj):
    layer = obj.data.uv_layers.active
    ratios = []
    uv_areas = []
    all_uvs = []
    for polygon in obj.data.polygons:
        coords = [layer.data[index].uv.copy() for index in polygon.loop_indices]
        all_uvs.extend(coords)
        uv_area = abs(sum(
            coords[index].x * coords[(index + 1) % len(coords)].y
            - coords[(index + 1) % len(coords)].x * coords[index].y
            for index in range(len(coords))
        ) * 0.5)
        points = [obj.data.vertices[index].co for index in polygon.vertices]
        area = sum(
            ((points[index] - points[0]).cross(points[index + 1] - points[0])).length * 0.5
            for index in range(1, len(points) - 1)
        )
        uv_areas.append(uv_area)
        if area > 1e-12:
            ratios.append(uv_area / area)
    mean = statistics.mean(ratios)
    return {
        "seam_edges": sum(edge.use_seam for edge in obj.data.edges),
        "uv_loop_count": len(layer.data),
        "minimum_face_uv_area": min(uv_areas),
        "degenerate_uv_faces": sum(area < 1e-10 for area in uv_areas),
        "world_texel_ratio_cv": statistics.pstdev(ratios) / mean,
        "inside_unit_tile": all(-1e-6 <= uv.x <= 1.000001 and -1e-6 <= uv.y <= 1.000001 for uv in all_uvs),
    }


def image_metrics(image):
    pixels = list(image.pixels)
    rgb = [pixels[index:index + 3] for index in range(0, len(pixels), 4)]
    occupied = [value for value in rgb if max(value) > 0.02]
    neutral = (0.5, 0.5, 1.0)
    changed = sum(
        math.sqrt(sum((value[channel] - neutral[channel]) ** 2 for channel in range(3))) > 0.03
        for value in occupied
    )
    return {
        "width": image.size[0],
        "height": image.size[1],
        "occupied_pixels": len(occupied),
        "non_neutral_pixels": changed,
        "channel_standard_deviation": [statistics.pstdev(value[channel] for value in occupied) for channel in range(3)],
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    low_z = [-1.5, -1.2, 1.0, 1.3]
    low = vessel_mesh("UV_Bake_Low", segments=12, z_values=low_z)
    mark_authored_seams(low, 12, len(low_z))
    unwrap(low)
    uv_state = uv_metrics(low)

    high_z = [-1.5 + index * (2.8 / 24.0) for index in range(25)]
    high = vessel_mesh("UV_Bake_High", segments=64, z_values=high_z, detailed=True)

    image = bpy.data.images.new("Housing_Tangent_Normal", width=256, height=256, alpha=False, float_buffer=False)
    image.generated_color = (0.5, 0.5, 1.0, 1.0)
    image.colorspace_settings.name = "Non-Color"
    material = bpy.data.materials.new("Bake_Target_Material")
    material.use_nodes = True
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.name = "Active Bake Target"
    texture.image = image
    material.node_tree.nodes.active = texture
    low.data.materials.append(material)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.use_clear = True
    scene.render.bake.margin = 16
    scene.render.bake.cage_extrusion = 0.08
    scene.render.bake.max_ray_distance = 0.16
    scene.render.image_settings.file_format = "PNG"

    activate(low)
    failure_control = {"rejected": False, "error": None}
    try:
        bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    except RuntimeError as exc:
        failure_control = {"rejected": True, "error": str(exc)}

    activate(low, include=(high,))
    result = bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    image.filepath_raw = str(OUT / "housing_tangent_normal.png")
    image.save()
    image.pack()
    baked = image_metrics(image)

    assertions = {
        "authored_seam_graph_matches_two_caps_and_one_longitudinal_cut": uv_state["seam_edges"] == 27,
        "unwrap_has_no_degenerate_faces": uv_state["degenerate_uv_faces"] == 0,
        "packed_uvs_stay_in_unit_tile": uv_state["inside_unit_tile"],
        "missing_high_source_is_rejected": failure_control["rejected"],
        "selected_to_active_bake_finishes": "FINISHED" in result,
        "normal_bake_contains_surface_signal": baked["non_neutral_pixels"] > 1000,
        "normal_texture_is_non_color": image.colorspace_settings.name == "Non-Color",
    }
    report = {
        "lab": "seam_authored_uv_and_high_low_normal_bake",
        "blender_version": bpy.app.version_string,
        "lesson_source": "https://commons.wikimedia.org/wiki/File:UV_Unwrapping_-_Blender_2.80_Fundamentals.webm",
        "official_corroboration": [
            "https://docs.blender.org/manual/en/dev/modeling/meshes/uv/workflows/layout.html",
            "https://docs.blender.org/manual/en/latest/render/cycles/baking.html",
            "https://docs.blender.org/manual/en/dev/render/shader_nodes/vector/normal_map.html",
        ],
        "low_mesh": {"vertices": len(low.data.vertices), "edges": len(low.data.edges), "faces": len(low.data.polygons)},
        "high_mesh": {"vertices": len(high.data.vertices), "edges": len(high.data.edges), "faces": len(high.data.polygons)},
        "uv": uv_state,
        "failure_control": failure_control,
        "bake": {"operator_result": sorted(result), "image": baked, "path": str(OUT / "housing_tangent_normal.png")},
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (OUT / "uv_bake_learning_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "uv_bake_learning_lab.blend"))
    print("UV_BAKE_LEARNING_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
