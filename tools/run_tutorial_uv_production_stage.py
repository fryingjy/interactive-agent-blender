"""Stage-6 tutorial reproduction: connected compound cages, UVs, material, and bake.

The tutorial artifact is a one-component "weird cube" interpreted as a box-like base grown into
a curved tube and enlarged rounded end.  A C-shaped clasp is the different-geometry transfer.
High/low cages are independently generated, modifiers remain live, and a matched no-seam copy is
retained as the failure control.
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
OUT = ROOT / "runs" / "2026-08-22_tutorial-cgboost-uv-production"
BLENDER_OPS = ROOT / "blender_ops"
for entry in (ROOT, BLENDER_OPS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from knowledge_engine.high_low_audit import HighLowEvidence, audit_production_high_low
from render_passes import render_diagnostic_pass, render_silhouette
from tools.run_uv_seam_production_transfer import (
    activate,
    alpha_mask,
    connected_components,
    connected_uv_islands,
    evaluated_health,
    image_metrics,
    uv_metrics,
)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for item in list(bpy.data.collections):
        bpy.data.collections.remove(item)


def get_collection(name: str):
    item = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(item)
    return item


def superellipse(theta: float, exponent: float) -> tuple[float, float]:
    cosine, sine = math.cos(theta), math.sin(theta)
    return (
        math.copysign(abs(cosine) ** exponent, cosine),
        math.copysign(abs(sine) ** exponent, sine),
    )


def sample_path(control: list[tuple[float, float, float, float]], rings: int):
    """Sample a clamped Catmull-Rom x/z center, radius, and cross-section exponent."""
    def catmull(a: float, b: float, c: float, d: float, t: float) -> float:
        return 0.5 * (
            2.0 * b
            + (-a + c) * t
            + (2.0 * a - 5.0 * b + 4.0 * c - d) * t * t
            + (-a + 3.0 * b - 3.0 * c + d) * t * t * t
        )

    result = []
    for ring in range(rings):
        position = ring * (len(control) - 1) / (rings - 1)
        left = min(int(position), len(control) - 2)
        blend = position - left
        p0 = control[max(0, left - 1)]
        p1 = control[left]
        p2 = control[left + 1]
        p3 = control[min(len(control) - 1, left + 2)]
        result.append(tuple(catmull(p0[index], p1[index], p2[index], p3[index], blend) for index in range(4)))
    return result


def make_swept_cage(
    name: str,
    control: list[tuple[float, float, float, float]],
    segments: int,
    rings: int,
    target,
    *,
    detailed: bool,
):
    path = sample_path(control, rings)
    vertices = []
    for ring, (cx, cz, radius, exponent) in enumerate(path):
        previous = path[max(0, ring - 1)]
        following = path[min(rings - 1, ring + 1)]
        tangent = Vector((following[0] - previous[0], 0.0, following[1] - previous[1])).normalized()
        plane_normal = Vector((-tangent.z, 0.0, tangent.x))
        for index in range(segments):
            theta = math.tau * index / segments
            u, v = superellipse(theta, exponent)
            relief = 1.0
            if detailed:
                relief += 0.025 * math.sin(theta * 4.0) * math.sin(math.pi * ring / (rings - 1)) ** 2
            point = Vector((cx, 0.0, cz)) + Vector((0.0, u * radius * relief, 0.0))
            point += plane_normal * (v * radius * relief)
            vertices.append(tuple(point))
    faces = []
    for ring in range(rings - 1):
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((
                ring * segments + index,
                ring * segments + nxt,
                (ring + 1) * segments + nxt,
                (ring + 1) * segments + index,
            ))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj["construction"] = "ONE_CONNECTED_ALL_QUAD_SWEEP_CAGE"
    obj["modifier_application_policy"] = "LEAVE_UNAPPLIED_FOR_USER"
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    solidify = obj.modifiers.new("Live shell thickness - unapplied", "SOLIDIFY")
    solidify.thickness = 0.09
    solidify.offset = 0.0
    solidify.use_even_offset = True
    return obj


def mark_longitudinal_seam(obj, segments: int, rings: int) -> int:
    wanted = {
        frozenset((ring * segments, (ring + 1) * segments))
        for ring in range(rings - 1)
    }
    for edge in obj.data.edges:
        edge.use_seam = frozenset(edge.vertices) in wanted
    return sum(edge.use_seam for edge in obj.data.edges)


def unwrap(obj) -> None:
    activate(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")


def checker_material(name: str):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    coordinates = nodes.new("ShaderNodeTexCoord")
    checker = nodes.new("ShaderNodeTexChecker")
    checker.inputs["Color1"].default_value = (0.025, 0.025, 0.025, 1.0)
    checker.inputs["Color2"].default_value = (0.65, 0.12, 0.04, 1.0)
    checker.inputs["Scale"].default_value = 18.0
    principled.inputs["Roughness"].default_value = 0.38
    links.new(coordinates.outputs["UV"], checker.inputs["Vector"])
    links.new(checker.outputs["Color"], principled.inputs["Base Color"])
    return material


def assign_material(obj, material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.material_index = 0


def bake_normal(label: str, high, low) -> dict:
    material = low.data.materials[0]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    image = bpy.data.images.new(f"{label}_Tangent_Normal", width=512, height=512, alpha=False)
    image.generated_color = (0.5, 0.5, 1.0, 1.0)
    image.colorspace_settings.name = "Non-Color"
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Active Normal Bake Target"
    texture.image = image
    nodes.active = texture
    normal = nodes.new("ShaderNodeNormalMap")
    principled = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.use_clear = True
    scene.render.bake.margin = 16
    scene.render.bake.cage_extrusion = 0.08
    scene.render.bake.max_ray_distance = 0.16
    activate(low, include=(high,))
    result = bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    links.new(texture.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], principled.inputs["Normal"])
    path = OUT / f"{label}_tangent_normal.png"
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


def render_material(obj, path: Path) -> dict:
    """Render the UV checker and baked tangent normal through the actual node material."""
    scene = bpy.context.scene
    previous_hidden = {candidate.name: candidate.hide_render for candidate in scene.objects}
    for candidate in scene.objects:
        candidate.hide_render = candidate is not obj
    camera_data = bpy.data.cameras.new("Stage6_Material_Camera")
    camera = bpy.data.objects.new("Stage6_Material_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (6.5, -8.5, 6.0)
    center = sum((obj.matrix_world @ Vector(corner) for corner in obj.bound_box), Vector()) / 8.0
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    span = max((obj.matrix_world @ Vector(corner) - center).length for corner in obj.bound_box)
    camera_data.ortho_scale = span * 2.45
    scene.camera = camera
    key_data = bpy.data.lights.new("Stage6_Key", "AREA")
    key_data.energy = 850.0
    key_data.shape = "DISK"
    key_data.size = 5.0
    key = bpy.data.objects.new("Stage6_Key", key_data)
    scene.collection.objects.link(key)
    key.location = (3.5, -4.0, 7.0)
    key.rotation_euler = (center - key.location).to_track_quat("-Z", "Y").to_euler()
    fill_data = bpy.data.lights.new("Stage6_Fill", "AREA")
    fill_data.energy = 500.0
    fill_data.size = 4.0
    fill = bpy.data.objects.new("Stage6_Fill", fill_data)
    scene.collection.objects.link(fill)
    fill.location = (-4.0, -1.0, 2.5)
    fill.rotation_euler = (center - fill.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.objects.remove(key, do_unlink=True)
    bpy.data.objects.remove(fill, do_unlink=True)
    for candidate in scene.objects:
        if candidate.name in previous_hidden:
            candidate.hide_render = previous_hidden[candidate.name]
    return {"path": str(path.relative_to(ROOT)), "engine": "BLENDER_EEVEE", "uv_driven_material": True}


def silhouette_iou(high, low, label: str) -> tuple[dict[str, float], list[dict]]:
    scores, records = {}, []
    for view in ("front", "side", "top"):
        high_path = OUT / "silhouettes" / f"{label}_high_{view}.png"
        low_path = OUT / "silhouettes" / f"{label}_low_{view}.png"
        records.append(render_silhouette(high.name, str(high_path), view=view, resolution=320, frame_name=high.name))
        records.append(render_silhouette(low.name, str(low_path), view=view, resolution=320, frame_name=high.name))
        high_mask, low_mask = alpha_mask(high_path), alpha_mask(low_path)
        intersection = sum(a and b for a, b in zip(high_mask, low_mask))
        union = sum(a or b for a, b in zip(high_mask, low_mask))
        scores[view] = round(intersection / union if union else 0.0, 6)
    return scores, records


def topology(obj) -> dict:
    return {
        "vertices": len(obj.data.vertices),
        "edges": len(obj.data.edges),
        "faces": len(obj.data.polygons),
        "all_quads": all(len(face.vertices) == 4 for face in obj.data.polygons),
        "components": connected_components(obj),
    }


def uv_overlap_pairs(obj) -> int:
    """Count positive-area overlaps between convex UV face polygons; shared borders do not count."""
    layer = obj.data.uv_layers.active
    polygons = []
    for face in obj.data.polygons:
        points = [Vector(layer.data[index].uv) for index in face.loop_indices]
        signed = sum(
            points[index].x * points[(index + 1) % len(points)].y
            - points[(index + 1) % len(points)].x * points[index].y
            for index in range(len(points))
        )
        if signed < 0.0:
            points.reverse()
        polygons.append(points)

    def clip(subject, boundary):
        output = subject
        for index, edge_start in enumerate(boundary):
            edge_end = boundary[(index + 1) % len(boundary)]
            source = output
            output = []
            if not source:
                break

            def inside(point):
                edge = edge_end - edge_start
                relative = point - edge_start
                return edge.x * relative.y - edge.y * relative.x >= -1e-10

            def intersection(a, b):
                segment = b - a
                edge = edge_end - edge_start
                denominator = segment.x * edge.y - segment.y * edge.x
                if abs(denominator) < 1e-12:
                    return b
                offset = edge_start - a
                amount = (offset.x * edge.y - offset.y * edge.x) / denominator
                return a + segment * amount

            previous = source[-1]
            for current in source:
                if inside(current):
                    if not inside(previous):
                        output.append(intersection(previous, current))
                    output.append(current)
                elif inside(previous):
                    output.append(intersection(previous, current))
                previous = current
        return output

    overlaps = 0
    for left in range(len(polygons)):
        left_poly = polygons[left]
        left_bounds = (
            min(point.x for point in left_poly), max(point.x for point in left_poly),
            min(point.y for point in left_poly), max(point.y for point in left_poly),
        )
        for right in range(left + 1, len(polygons)):
            right_poly = polygons[right]
            right_bounds = (
                min(point.x for point in right_poly), max(point.x for point in right_poly),
                min(point.y for point in right_poly), max(point.y for point in right_poly),
            )
            if (
                left_bounds[1] <= right_bounds[0] + 1e-10
                or right_bounds[1] <= left_bounds[0] + 1e-10
                or left_bounds[3] <= right_bounds[2] + 1e-10
                or right_bounds[3] <= left_bounds[2] + 1e-10
            ):
                continue
            clipped = clip(left_poly, right_poly)
            area = abs(sum(
                clipped[index].x * clipped[(index + 1) % len(clipped)].y
                - clipped[(index + 1) % len(clipped)].x * clipped[index].y
                for index in range(len(clipped))
            ) * 0.5) if len(clipped) >= 3 else 0.0
            overlaps += area > 1e-9
    return overlaps


def family_run(label, control, settings, collections, material):
    high = make_swept_cage(
        f"{label}_HIGH", control, settings["high_segments"], settings["high_rings"],
        collections["high"], detailed=True,
    )
    low = make_swept_cage(
        f"{label}_LOW", control, settings["low_segments"], settings["low_rings"],
        collections["low"], detailed=False,
    )
    assign_material(low, material)
    seams = mark_longitudinal_seam(low, settings["low_segments"], settings["low_rings"])
    unwrap(low)
    corrected_uv = uv_metrics(low)
    corrected_uv["positive_area_overlap_pairs"] = uv_overlap_pairs(low)

    failure = low.copy()
    failure.data = low.data.copy()
    failure.name = f"{label}_NO_SEAM_FAILURE"
    collections["failure"].objects.link(failure)
    for edge in failure.data.edges:
        edge.use_seam = False
    unwrap(failure)
    failure_uv = uv_metrics(failure)
    failure_uv["positive_area_overlap_pairs"] = uv_overlap_pairs(failure)

    bake = bake_normal(label, high, low)
    material_render = render_material(low, OUT / f"{label}_uv_material.png")
    scores, records = silhouette_iou(high, low, label)
    records.append(render_diagnostic_pass(high.name, str(OUT / f"{label}_high_matcap.png"), "matcap", view="isometric", resolution=480))
    records.append(render_diagnostic_pass(low.name, str(OUT / f"{label}_low_wire.png"), "wireframe", view="isometric", resolution=480))

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
        low_uv_layer=corrected_uv["layer"],
        low_uv_loop_count=corrected_uv["loop_count"],
        low_degenerate_uv_faces=corrected_uv["degenerate_faces"],
        low_uv_inside_unit_tile=corrected_uv["inside_unit_tile"],
        silhouette_iou_by_view=scores,
    )
    return {
        "objects": {"high": high.name, "low": low.name, "failure": failure.name},
        "topology": {"high": topology(high), "low": topology(low)},
        "live_modifiers": {
            "high": [modifier.type for modifier in high.modifiers],
            "low": [modifier.type for modifier in low.modifiers],
        },
        "authored_seam_edges": seams,
        "corrected_uv": corrected_uv,
        "failure_uv": failure_uv,
        "evaluated_health": {"high": evaluated_health(high), "low": evaluated_health(low)},
        "silhouette_iou_by_view": scores,
        "production_audit": audit_production_high_low(evidence, minimum_silhouette_iou=0.88),
        "bake": bake,
        "material_render": material_render,
        "render_records": records,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "silhouettes").mkdir(exist_ok=True)
    clear_scene()
    collections = {
        "high": get_collection("HIGH_POLY"),
        "low": get_collection("LOW_POLY"),
        "failure": get_collection("FAILURE_CONTROLS"),
    }
    material = checker_material("UV_Checker_Production_Material")
    weird_cube = [
        (-1.8, 0.0, 0.78, 0.24), (-1.2, 0.0, 0.78, 0.24), (-0.55, 0.0, 0.76, 0.28),
        (0.10, 0.10, 0.66, 0.38), (0.65, 0.42, 0.48, 0.58), (0.92, 0.92, 0.44, 0.72),
        (1.00, 1.40, 0.48, 0.72), (1.25, 1.78, 0.58, 0.70), (1.72, 1.98, 0.70, 0.62),
    ]
    clasp = [
        (-1.35, 1.0, 0.34, 0.72), (-1.72, 0.45, 0.36, 0.72), (-1.78, -0.25, 0.38, 0.72),
        (-1.40, -0.92, 0.40, 0.72), (-0.70, -1.38, 0.42, 0.72), (0.15, -1.45, 0.42, 0.72),
        (0.90, -1.12, 0.40, 0.72), (1.40, -0.55, 0.37, 0.72), (1.55, 0.12, 0.34, 0.72),
    ]
    families = {
        "tutorial_weird_cube": family_run(
            "tutorial_weird_cube", weird_cube,
            {"low_segments": 12, "high_segments": 16, "low_rings": 11, "high_rings": 25},
            collections, material,
        ),
        "transfer_curved_clasp": family_run(
            "transfer_curved_clasp", clasp,
            {"low_segments": 12, "high_segments": 16, "low_rings": 13, "high_rings": 29},
            collections, material,
        ),
    }
    checks = {
        "tutorial_and_different_transfer_exist": set(families) == {"tutorial_weird_cube", "transfer_curved_clasp"},
        "connected_all_quad_independent_cages": all(
            item["topology"][variant]["all_quads"] and item["topology"][variant]["components"] == 1
            for item in families.values() for variant in ("high", "low")
        ),
        "twelve_sided_low_cross_sections": all(item["topology"]["low"]["vertices"] % 12 == 0 for item in families.values()),
        "purposeful_seam_improves_angle_error": all(
            item["failure_uv"]["mean_corner_angle_error_degrees"]
            > item["corrected_uv"]["mean_corner_angle_error_degrees"] + 0.25
            for item in families.values()
        ),
        "uvs_valid_packed_single_island": all(
            item["corrected_uv"]["degenerate_faces"] == 0
            and item["corrected_uv"]["inside_unit_tile"]
            and item["corrected_uv"]["island_count"] == 1
            and item["corrected_uv"]["positive_area_overlap_pairs"] == 0
            for item in families.values()
        ),
        "live_modifiers_unapplied": all(
            item["live_modifiers"]["high"] == ["SOLIDIFY"]
            and item["live_modifiers"]["low"] == ["SOLIDIFY"]
            for item in families.values()
        ),
        "evaluated_shells_closed": all(
            item["evaluated_health"][variant]["non_manifold_edges"] == 0
            for item in families.values() for variant in ("high", "low")
        ),
        "production_audits_pass": all(item["production_audit"]["pass"] for item in families.values()),
        "normal_bakes_have_signal": all(
            "FINISHED" in item["bake"]["operator_result"]
            and item["bake"]["metrics"]["non_neutral_pixels"] > 1000
            for item in families.values()
        ),
    }
    report = {
        "schema_version": 1,
        "experiment": "cgboost_uv_tutorial_connected_compound_reproduction",
        "blender_version": bpy.app.version_string,
        "source": "https://www.youtube.com/watch?v=JwkgVckqGw4",
        "source_episode": [2018, 2245],
        "hypothesis": "A connected compound cage should be decomposed into topological UV regions and opened with a purposeful longitudinal seam; a UV layer without that cut is not sufficient.",
        "frozen_thresholds": {"minimum_silhouette_iou": 0.88, "minimum_bake_signal_pixels": 1000},
        "families": families,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": "Bounded connected sweep-cage interpretation of the tutorial's weird-cube lesson plus a different curved clasp. It validates seam, distortion, packing, material hookup, and tangent-bake behavior; it does not claim an exact copy of the tutorial project file or universal seam placement.",
    }
    (OUT / "stage6_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.context.scene["pipeline_applied_modifiers"] = False
    bpy.context.scene["tutorial_stage"] = 6
    bpy.context.scene["evidence_report"] = "stage6_report.json"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "uv_production_tutorial.blend"))
    print(json.dumps({"checks": checks, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
