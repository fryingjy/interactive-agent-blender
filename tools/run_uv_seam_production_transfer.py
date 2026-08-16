"""Reproduce and transfer seam-directed UV planning in Blender 5.2.

This is a controlled production experiment, not a reference asset.  Two connected
all-quad tube cages use authored seams, live Solidify/Bevel stacks, selected-to-
active tangent bakes, multiview silhouettes, and low-only GLB exports.  A matched
no-seam control tests whether UV quality can be inferred from a layer's existence.
"""

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
OUT = ROOT / "runs" / "2026-08-16_uv-seam-production-transfer"
BLENDER_OPS = ROOT / "blender_ops"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BLENDER_OPS) not in sys.path:
    sys.path.insert(0, str(BLENDER_OPS))

from knowledge_engine.high_low_audit import HighLowEvidence, audit_production_high_low
from render_passes import render_diagnostic_pass, render_silhouette


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)


def collection(name: str):
    item = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(item)
    return item


def activate(obj, *, include=()) -> None:
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for candidate in include:
        candidate.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def radial_point(index: int, count: int, t: float, *, detailed: bool) -> tuple[float, float]:
    angle = math.tau * index / count
    radius = 1.02 + 0.13 * math.sin(math.pi * t) - 0.05 * math.cos(2.0 * math.pi * t)
    if detailed:
        radius += 0.022 * math.sin(4.0 * angle) * math.sin(math.pi * t) ** 2
    return radius * math.cos(angle), radius * math.sin(angle)


def rounded_rect_point(index: int, count: int, t: float, *, detailed: bool) -> tuple[float, float]:
    angle = math.tau * index / count
    exponent = 0.50
    cx, sy = math.cos(angle), math.sin(angle)
    x = math.copysign(abs(cx) ** exponent, cx) * (1.05 + 0.08 * math.sin(math.pi * t))
    y = math.copysign(abs(sy) ** exponent, sy) * (0.72 + 0.05 * math.cos(math.pi * t))
    if detailed:
        y += 0.018 * math.sin(3.0 * angle) * math.sin(math.pi * t) ** 2
    return x, y


def make_tube(name: str, family: str, segments: int, rings: int, target, *, detailed: bool):
    vertices = []
    for ring in range(rings):
        t = ring / (rings - 1)
        z = -1.55 + 3.10 * t
        center_x = 0.0 if family == "radial" else 0.22 * math.sin((t - 0.5) * math.pi)
        for index in range(segments):
            if family == "radial":
                x, y = radial_point(index, segments, t, detailed=detailed)
            else:
                x, y = rounded_rect_point(index, segments, t, detailed=detailed)
            vertices.append((x + center_x, y, z))
    faces = []
    for ring in range(rings - 1):
        for index in range(segments):
            nxt = (index + 1) % segments
            a = ring * segments + index
            b = ring * segments + nxt
            c = (ring + 1) * segments + nxt
            d = (ring + 1) * segments + index
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj["construction"] = "ONE_CONNECTED_ALL_QUAD_TUBE_CAGE"
    obj["modifier_application_policy"] = "LEAVE_UNAPPLIED_FOR_USER"
    obj["family"] = family
    return obj


def add_live_stack(obj) -> None:
    solidify = obj.modifiers.new("Shell Thickness - Unapplied", "SOLIDIFY")
    solidify.thickness = 0.075
    solidify.offset = 0.0
    solidify.use_even_offset = True
    bevel = obj.modifiers.new("Manufactured Edge Radius - Unapplied", "BEVEL")
    bevel.limit_method = "ANGLE"
    bevel.width = 0.025
    bevel.segments = 2
    bevel.harden_normals = True


def edge_key(a: int, b: int) -> frozenset[int]:
    return frozenset((a, b))


def mark_longitudinal_seam(obj, segments: int, rings: int) -> int:
    seam_pairs = {
        edge_key(ring * segments, (ring + 1) * segments)
        for ring in range(rings - 1)
    }
    for edge in obj.data.edges:
        edge.use_seam = edge_key(*edge.vertices) in seam_pairs
    return sum(edge.use_seam for edge in obj.data.edges)


def unwrap(obj) -> None:
    activate(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")


def polygon_area_2d(points: list[Vector]) -> float:
    return abs(sum(
        points[index].x * points[(index + 1) % len(points)].y
        - points[(index + 1) % len(points)].x * points[index].y
        for index in range(len(points))
    ) * 0.5)


def corner_angle(a: Vector, center: Vector, b: Vector) -> float:
    left = (a - center).normalized()
    right = (b - center).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, left.dot(right)))))


def connected_uv_islands(obj) -> int:
    mesh = obj.data
    uv_layer = mesh.uv_layers.active
    edge_index_by_key = {edge_key(*edge.vertices): edge.index for edge in mesh.edges}
    edge_faces: dict[int, list[int]] = {}
    face_uvs: dict[int, dict[int, Vector]] = {}
    for polygon in mesh.polygons:
        face_uvs[polygon.index] = {
            mesh.loops[loop_index].vertex_index: uv_layer.data[loop_index].uv.copy()
            for loop_index in polygon.loop_indices
        }
        for vertices in polygon.edge_keys:
            edge_faces.setdefault(edge_index_by_key[edge_key(*vertices)], []).append(polygon.index)
    graph = {polygon.index: set() for polygon in mesh.polygons}
    for edge_index, faces in edge_faces.items():
        if len(faces) != 2:
            continue
        a, b = mesh.edges[edge_index].vertices
        left, right = faces
        uv_continuous = (
            (face_uvs[left][a] - face_uvs[right][a]).length <= 1e-6
            and (face_uvs[left][b] - face_uvs[right][b]).length <= 1e-6
        )
        if uv_continuous:
            graph[left].add(right)
            graph[right].add(left)
    remaining = set(graph)
    islands = 0
    while remaining:
        islands += 1
        stack = [remaining.pop()]
        while stack:
            for neighbor in graph[stack.pop()]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return islands


def uv_metrics(obj) -> dict:
    mesh = obj.data
    layer = mesh.uv_layers.active
    if layer is None:
        return {"layer": None}
    area_ratios = []
    angle_errors = []
    uv_areas = []
    all_uvs = []
    for polygon in mesh.polygons:
        uv = [layer.data[index].uv.copy() for index in polygon.loop_indices]
        xyz = [mesh.vertices[index].co.copy() for index in polygon.vertices]
        all_uvs.extend(uv)
        uv_area = polygon_area_2d(uv)
        uv_areas.append(uv_area)
        world_area = polygon.area
        if world_area > 1e-12:
            area_ratios.append(uv_area / world_area)
        for index in range(len(uv)):
            uv_angle = corner_angle(uv[index - 1], uv[index], uv[(index + 1) % len(uv)])
            xyz_angle = corner_angle(xyz[index - 1], xyz[index], xyz[(index + 1) % len(xyz)])
            angle_errors.append(abs(uv_angle - xyz_angle))
    mean_ratio = statistics.mean(area_ratios)
    return {
        "layer": layer.name,
        "seam_edges": sum(edge.use_seam for edge in mesh.edges),
        "island_count": connected_uv_islands(obj),
        "loop_count": len(layer.data),
        "degenerate_faces": sum(area < 1e-10 for area in uv_areas),
        "minimum_face_uv_area": min(uv_areas),
        "inside_unit_tile": all(-1e-6 <= value.x <= 1.000001 and -1e-6 <= value.y <= 1.000001 for value in all_uvs),
        "world_texel_ratio_cv": statistics.pstdev(area_ratios) / mean_ratio,
        "mean_corner_angle_error_degrees": statistics.mean(angle_errors),
        "max_corner_angle_error_degrees": max(angle_errors),
    }


def connected_components(obj) -> int:
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
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def image_metrics(image) -> dict:
    pixels = list(image.pixels)
    rgb = [pixels[index:index + 3] for index in range(0, len(pixels), 4)]
    changed = sum(
        math.dist(value, (0.5, 0.5, 1.0)) > 0.03
        for value in rgb
        if max(value) > 0.02
    )
    return {
        "width": image.size[0],
        "height": image.size[1],
        "non_neutral_pixels": changed,
        "channel_standard_deviation": [statistics.pstdev(value[channel] for value in rgb) for channel in range(3)],
    }


def bake_normal(family: str, high, low) -> dict:
    image = bpy.data.images.new(f"{family}_Tangent_Normal", width=256, height=256, alpha=False)
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
    principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    low.data.materials.append(material)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.use_clear = True
    scene.render.bake.margin = 12
    scene.render.bake.cage_extrusion = 0.06
    scene.render.bake.max_ray_distance = 0.12
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
        "path": str(path.relative_to(ROOT)),
        "colorspace": image.colorspace_settings.name,
        "metrics": image_metrics(image),
    }


def alpha_mask(path: Path) -> list[bool]:
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        return [alpha > 0.5 for alpha in image.pixels[3::4]]
    finally:
        bpy.data.images.remove(image)


def silhouette_iou(high, low, family: str) -> tuple[dict[str, float], list[dict]]:
    scores = {}
    records = []
    for view in ("front", "side", "top"):
        high_path = OUT / "silhouettes" / f"{family}_high_{view}.png"
        low_path = OUT / "silhouettes" / f"{family}_low_{view}.png"
        records.append(render_silhouette(high.name, str(high_path), view=view, resolution=320, frame_name=high.name))
        records.append(render_silhouette(low.name, str(low_path), view=view, resolution=320, frame_name=high.name))
        high_mask, low_mask = alpha_mask(high_path), alpha_mask(low_path)
        intersection = sum(a and b for a, b in zip(high_mask, low_mask))
        union = sum(a or b for a, b in zip(high_mask, low_mask))
        scores[view] = round(intersection / union if union else 0.0, 6)
    return scores, records


def export_low(family: str, low) -> str:
    activate(low)
    path = OUT / f"{family}_low.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=False, export_materials="EXPORT",
    )
    return str(path.relative_to(ROOT))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    clear_scene()
    high_collection = collection("HIGH_POLY")
    low_collection = collection("LOW_POLY")
    control_collection = collection("FAILURE_CONTROLS")
    families = {
        "radial": {"low_segments": 12, "high_segments": 16, "low_rings": 5, "high_rings": 13},
        "bent_rect": {"low_segments": 12, "high_segments": 16, "low_rings": 6, "high_rings": 15},
    }
    report_families = {}
    renders = []
    for family, settings in families.items():
        high = make_tube(
            f"{family}_HIGH", family, settings["high_segments"], settings["high_rings"],
            high_collection, detailed=True,
        )
        low = make_tube(
            f"{family}_LOW", family, settings["low_segments"], settings["low_rings"],
            low_collection, detailed=False,
        )
        add_live_stack(high)
        add_live_stack(low)
        authored_seams = mark_longitudinal_seam(low, settings["low_segments"], settings["low_rings"])
        unwrap(low)
        authored_uv = uv_metrics(low)

        control = low.copy()
        control.data = low.data.copy()
        control.name = f"{family}_NO_SEAM_CONTROL"
        control_collection.objects.link(control)
        for edge in control.data.edges:
            edge.use_seam = False
        unwrap(control)
        no_seam_uv = uv_metrics(control)

        bake = bake_normal(family, high, low)
        scores, silhouette_records = silhouette_iou(high, low, family)
        renders.extend(silhouette_records)
        renders.append(render_diagnostic_pass(high.name, str(OUT / f"{family}_high_matcap.png"), "matcap", view="isometric", resolution=480))
        renders.append(render_diagnostic_pass(low.name, str(OUT / f"{family}_low_wireframe.png"), "wireframe", view="isometric", resolution=480))
        export_path = export_low(family, low)

        high_health, low_health = evaluated_health(high), evaluated_health(low)
        evidence = HighLowEvidence(
            high_object=high.name,
            low_object=low.name,
            separate_collections=True,
            independent_mesh_datablocks=high.data is not low.data,
            high_base_faces=len(high.data.polygons),
            low_base_faces=len(low.data.polygons),
            high_connected_components=connected_components(high),
            low_connected_components=connected_components(low),
            high_live_modifiers=tuple(modifier.type for modifier in high.modifiers),
            low_live_modifiers=tuple(modifier.type for modifier in low.modifiers),
            low_uv_layer=authored_uv["layer"],
            low_uv_loop_count=authored_uv["loop_count"],
            low_degenerate_uv_faces=authored_uv["degenerate_faces"],
            low_uv_inside_unit_tile=authored_uv["inside_unit_tile"],
            silhouette_iou_by_view=scores,
        )
        production_audit = audit_production_high_low(evidence, minimum_silhouette_iou=0.90)
        report_families[family] = {
            "settings": settings,
            "objects": {"high": high.name, "low": low.name, "no_seam_control": control.name},
            "base_topology": {
                "high": {"vertices": len(high.data.vertices), "edges": len(high.data.edges), "faces": len(high.data.polygons)},
                "low": {"vertices": len(low.data.vertices), "edges": len(low.data.edges), "faces": len(low.data.polygons)},
                "all_base_faces_are_quads": all(len(face.vertices) == 4 for face in high.data.polygons) and all(len(face.vertices) == 4 for face in low.data.polygons),
            },
            "live_modifiers": {
                "high": [modifier.type for modifier in high.modifiers],
                "low": [modifier.type for modifier in low.modifiers],
            },
            "authored_seam_edges": authored_seams,
            "authored_uv": authored_uv,
            "no_seam_control_uv": no_seam_uv,
            "evaluated_health": {"high": high_health, "low": low_health},
            "silhouette_iou_by_view": scores,
            "production_audit": production_audit,
            "bake": bake,
            "export": export_path,
        }

    checks = {
        "two_shape_families": set(report_families) == {"radial", "bent_rect"},
        "all_source_cages_connected_and_all_quad": all(
            item["base_topology"]["all_base_faces_are_quads"]
            and item["production_audit"]["checks"]["single_connected_component_each"]
            for item in report_families.values()
        ),
        "all_source_modifiers_live_and_unapplied": all(
            item["live_modifiers"]["high"] == ["SOLIDIFY", "BEVEL"]
            and item["live_modifiers"]["low"] == ["SOLIDIFY", "BEVEL"]
            for item in report_families.values()
        ),
        "authored_cut_graph_is_one_longitudinal_path": all(
            item["authored_seam_edges"] == item["settings"]["low_rings"] - 1
            for item in report_families.values()
        ),
        "authored_uvs_are_valid_and_packed": all(
            item["authored_uv"]["degenerate_faces"] == 0
            and item["authored_uv"]["inside_unit_tile"]
            and item["authored_uv"]["island_count"] == 1
            for item in report_families.values()
        ),
        "no_seam_control_has_worse_mean_angle_error": all(
            item["no_seam_control_uv"]["mean_corner_angle_error_degrees"]
            > item["authored_uv"]["mean_corner_angle_error_degrees"] + 0.25
            for item in report_families.values()
        ),
        "evaluated_shells_closed_and_clean": all(
            item["evaluated_health"][variant]["non_manifold_edges"] == 0
            and item["evaluated_health"][variant]["degenerate_faces"] == 0
            for item in report_families.values() for variant in ("high", "low")
        ),
        "both_production_audits_pass": all(item["production_audit"]["pass"] for item in report_families.values()),
        "both_tangent_bakes_have_signal": all(
            "FINISHED" in item["bake"]["operator_result"]
            and item["bake"]["colorspace"] == "Non-Color"
            and item["bake"]["metrics"]["non_neutral_pixels"] > 500
            for item in report_families.values()
        ),
        "both_low_only_exports_exist": all((ROOT / item["export"]).is_file() for item in report_families.values()),
    }
    report = {
        "schema_version": 1,
        "experiment": "official_video_seam_directed_uv_production_transfer",
        "blender_version": bpy.app.version_string,
        "source_episode": "runs/2026-08-16_real-video-uv-review/episode_review.json",
        "hypothesis": "An authored longitudinal cut on a connected tube cage lowers unwrap angle distortion versus an otherwise identical no-seam cage, while preserving a production-ready editable source.",
        "frozen_thresholds": {
            "minimum_silhouette_iou": 0.90,
            "minimum_bake_non_neutral_pixels": 500,
            "minimum_mean_angle_error_improvement_degrees": 0.25,
        },
        "families": report_families,
        "checks": checks,
        "pass": all(checks.values()),
        "render_records": renders,
        "claim_boundary": (
            "Controlled connected radial and bent rounded-rectangular tube families only. This proves "
            "that seam placement changes these unwraps and that the retained source remains production-"
            "inspectable; it does not author UVs for an unreviewed real prop or prove universal seam placement."
        ),
    }
    (OUT / "uv_seam_production_transfer_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.context.scene["pipeline_applied_modifiers"] = False
    bpy.context.scene["evidence_report"] = "uv_seam_production_transfer_report.json"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "uv_seam_production_transfer.blend"))
    print(json.dumps({"checks": checks, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
