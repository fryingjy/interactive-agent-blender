"""Measure Bevel normal policies on uniform, uneven, and tapered curved cages."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-16_curved-bevel-normal-policy"
BLEND = OUT / "curved_bevel_normal_policy.blend"
REPORT = OUT / "curved_bevel_normal_policy_report.json"
RENDER = OUT / "curved_bevel_normal_policy_matcap.png"

POLICIES = ("NO_BEVEL_BASELINE", "PLAIN_SMOOTH", "HARDEN_NORMALS", "FACE_STRENGTH_WEIGHTED")
FAMILIES = {
    "UNIFORM_CYLINDER_12": {
        "angles_deg": [index * 30.0 for index in range(12)],
        "bottom_radius": 1.0,
        "top_radius": 1.0,
        "half_height": 1.25,
    },
    "UNEVEN_CYLINDER_12": {
        "angles_deg": [0.0, 20.0, 60.0, 80.0, 120.0, 140.0, 180.0, 200.0, 240.0, 260.0, 300.0, 320.0],
        "bottom_radius": 1.0,
        "top_radius": 1.0,
        "half_height": 1.25,
    },
    "UNIFORM_TAPER_16": {
        "angles_deg": [index * 22.5 for index in range(16)],
        "bottom_radius": 1.15,
        "top_radius": 0.82,
        "half_height": 1.25,
    },
}


def make_frustum(name, family_name, family, policy, location):
    angles = [math.radians(value) for value in family["angles_deg"]]
    count = len(angles)
    bottom_radius = family["bottom_radius"]
    top_radius = family["top_radius"]
    half_height = family["half_height"]
    vertices = []
    for z, radius in ((-half_height, bottom_radius), (half_height, top_radius)):
        vertices.extend((radius * math.cos(angle), radius * math.sin(angle), z) for angle in angles)
    faces = []
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, count + following, count + index))
    faces.append(tuple(reversed(range(count))))
    faces.append(tuple(range(count, count * 2)))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.color = {
        "NO_BEVEL_BASELINE": (0.42, 0.42, 0.44, 1.0),
        "PLAIN_SMOOTH": (0.32, 0.48, 0.68, 1.0),
        "HARDEN_NORMALS": (0.27, 0.66, 0.46, 1.0),
        "FACE_STRENGTH_WEIGHTED": (0.72, 0.47, 0.23, 1.0),
    }[policy]
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if policy == "NO_BEVEL_BASELINE":
        # With no physical rim radius, the manufactured cap/side transition is
        # intentionally sharp: flat cap corners and smooth radial side panels.
        for polygon in mesh.polygons[-2:]:
            polygon.use_smooth = False
    if policy != "NO_BEVEL_BASELINE":
        bevel = obj.modifiers.new("Physical rim radius", "BEVEL")
        bevel.limit_method = "ANGLE"
        bevel.angle_limit = math.radians(45.0)
        bevel.width = 0.12
        bevel.segments = 3
        if policy == "HARDEN_NORMALS":
            bevel.harden_normals = True
        elif policy == "FACE_STRENGTH_WEIGHTED":
            bevel.face_strength_mode = "FSTR_AFFECTED"
            weighted = obj.modifiers.new("Face-strength weighted normals", "WEIGHTED_NORMAL")
            weighted.mode = "FACE_AREA_WITH_ANGLE"
            weighted.keep_sharp = True
            weighted.use_face_influence = True
            weighted.weight = 50
    obj["fixture_family"] = family_name
    obj["normal_policy"] = policy
    obj["bottom_radius"] = bottom_radius
    obj["top_radius"] = top_radius
    obj["half_height"] = half_height
    obj["source_segment_count"] = count
    return obj


def angle_degrees(first, second):
    dot = max(-1.0, min(1.0, first.normalized().dot(second.normalized())))
    return math.degrees(math.acos(dot))


def metrics(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        cap_errors = []
        side_errors = []
        cap_faces = 0
        side_faces = 0
        bottom_radius = float(obj["bottom_radius"])
        top_radius = float(obj["top_radius"])
        half_height = float(obj["half_height"])
        radial_slope = (top_radius - bottom_radius) / (2.0 * half_height)
        for polygon in mesh.polygons:
            normal = polygon.normal.normalized()
            if abs(normal.z) > 0.95 and polygon.area > 0.5:
                cap_faces += 1
                for loop_index in polygon.loop_indices:
                    cap_errors.append(angle_degrees(mesh.corner_normals[loop_index].vector, normal))
            elif abs(normal.z) < 0.5 and polygon.area > 0.35:
                side_faces += 1
                for loop_index in polygon.loop_indices:
                    vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
                    radial = Vector((vertex.co.x, vertex.co.y, 0.0))
                    expected = Vector((radial.x, radial.y, -radial_slope * radial.length))
                    side_errors.append(angle_degrees(mesh.corner_normals[loop_index].vector, expected))
        bm = bmesh.new()
        bm.from_mesh(mesh)
        result = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "cap_faces_sampled": cap_faces,
            "cap_corners_sampled": len(cap_errors),
            "side_faces_sampled": side_faces,
            "side_corners_sampled": len(side_errors),
            "cap_normal_error_mean_deg": sum(cap_errors) / len(cap_errors),
            "cap_normal_error_max_deg": max(cap_errors),
            "side_analytic_error_mean_deg": sum(side_errors) / len(side_errors),
            "side_analytic_error_max_deg": max(side_errors),
            "custom_normal_attribute": "custom_normal" in mesh.attributes,
            "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
            "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        }
        bm.free()
        return result
    finally:
        evaluated.to_mesh_clear()


def render(objects):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 820
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER)
    scene.display.shading.type = "SOLID"
    scene.display.shading.light = "MATCAP"
    scene.display.shading.studio_light = "hard_surface_grey.exr"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_specular_highlight = True
    scene.display.shading.background_type = "WORLD"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Curved_Normal_Review_World")
    scene.world.color = (0.025, 0.032, 0.045)
    camera_data = bpy.data.cameras.new("Curved_Normal_Review_Camera")
    camera = bpy.data.objects.new("Curved_Normal_Review_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0.0, -18.0, 16.0)
    camera.rotation_euler = (Vector((0.0, 0.0, 0.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 13.0
    scene.camera = camera
    bpy.ops.render.render(write_still=True)


def classify(measured):
    outcomes = {}
    for family_name in FAMILIES:
        family = measured[family_name]
        baseline = family["NO_BEVEL_BASELINE"]
        plain = family["PLAIN_SMOOTH"]
        hardened = family["HARDEN_NORMALS"]
        weighted = family["FACE_STRENGTH_WEIGHTED"]
        outcomes[family_name] = {
            "harden_cap_improvement_deg": plain["cap_normal_error_max_deg"] - hardened["cap_normal_error_max_deg"],
            "weighted_cap_improvement_deg": plain["cap_normal_error_max_deg"] - weighted["cap_normal_error_max_deg"],
            "plain_side_delta_vs_unbeveled_deg": plain["side_analytic_error_max_deg"] - baseline["side_analytic_error_max_deg"],
            "harden_side_delta_vs_unbeveled_deg": hardened["side_analytic_error_max_deg"] - baseline["side_analytic_error_max_deg"],
            "weighted_side_delta_vs_unbeveled_deg": weighted["side_analytic_error_max_deg"] - baseline["side_analytic_error_max_deg"],
            "harden_side_delta_vs_plain_deg": hardened["side_analytic_error_max_deg"] - plain["side_analytic_error_max_deg"],
            "weighted_side_delta_vs_plain_deg": weighted["side_analytic_error_max_deg"] - plain["side_analytic_error_max_deg"],
            "lower_side_error_policy": min(POLICIES, key=lambda policy: family[policy]["side_analytic_error_max_deg"]),
        }
    return outcomes


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    objects = []
    family_y = {"UNIFORM_CYLINDER_12": 3.0, "UNEVEN_CYLINDER_12": 0.0, "UNIFORM_TAPER_16": -3.0}
    policy_x = {"NO_BEVEL_BASELINE": -4.8, "PLAIN_SMOOTH": -1.6, "HARDEN_NORMALS": 1.6, "FACE_STRENGTH_WEIGHTED": 4.8}
    for family_name, family in FAMILIES.items():
        for policy in POLICIES:
            objects.append(make_frustum(
                f"{family_name}_{policy}", family_name, family, policy,
                (policy_x[policy], family_y[family_name], 0.0),
            ))
    bpy.context.view_layer.update()
    measured = {
        family_name: {
            policy: metrics(bpy.data.objects[f"{family_name}_{policy}"])
            for policy in POLICIES
        }
        for family_name in FAMILIES
    }
    outcomes = classify(measured)
    assertions = {
        "all_twelve_variants_measured": sum(len(family) for family in measured.values()) == 12,
        "matched_bevel_topology_within_each_family": all(
            len({(family[policy]["vertices"], family[policy]["edges"], family[policy]["faces"]) for policy in POLICIES if policy != "NO_BEVEL_BASELINE"}) == 1
            for family in measured.values()
        ),
        "all_evaluated_meshes_closed_and_nondegenerate": all(
            item["non_manifold_edges"] == 0 and item["degenerate_faces"] == 0
            for family in measured.values() for item in family.values()
        ),
        "all_expected_caps_and_side_panels_sampled": all(
            item["cap_faces_sampled"] == 2
            and item["side_faces_sampled"] == int(bpy.data.objects[f"{family_name}_{policy}"]["source_segment_count"])
            for family_name, family in measured.items() for policy, item in family.items()
        ),
        "plain_smooth_bends_cap_normals_in_every_family": all(
            family["PLAIN_SMOOTH"]["cap_normal_error_max_deg"] > family["NO_BEVEL_BASELINE"]["cap_normal_error_max_deg"] + 1.0
            for family in measured.values()
        ),
        "harden_normals_flattens_caps_in_every_family": all(
            family["HARDEN_NORMALS"]["cap_normal_error_max_deg"] < 1.0
            for family in measured.values()
        ),
        "weighted_face_influence_flattens_caps_in_every_family": all(
            family["FACE_STRENGTH_WEIGHTED"]["cap_normal_error_max_deg"] < 1.0
            for family in measured.values()
        ),
        "corrected_variants_store_custom_normals": all(
            family[policy]["custom_normal_attribute"]
            for family in measured.values() for policy in ("HARDEN_NORMALS", "FACE_STRENGTH_WEIGHTED")
        ),
        "harden_normals_restores_unbeveled_side_baseline": all(
            abs(family["HARDEN_NORMALS"]["side_analytic_error_max_deg"] - family["NO_BEVEL_BASELINE"]["side_analytic_error_max_deg"]) < 0.05
            for family in measured.values()
        ),
    }
    render(objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report = {
        "lab": "curved_bevel_normal_policy",
        "blender_version": bpy.app.version_string,
        "hypotheses": {
            "H1": "A plain smooth rim Bevel bends cap and side normals away from the unbeveled smooth baseline; both correction policies reduce planar cap distortion.",
            "H2": "Harden Normals restores the unbeveled side-normal baseline, exposing residual error caused by uneven angular spacing rather than by the bevel.",
            "H3": "Face-area weighting may alter analytic curved-side error when adjacent panel areas differ, so it is not a blanket curved-surface policy.",
        },
        "official_sources": [
            "https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html",
            "https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/weighted_normal.html",
        ],
        "families": FAMILIES,
        "policies": list(POLICIES),
        "metrics": measured,
        "outcomes": outcomes,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "claim_boundary": "Controlled low-sided manufactured radial fixtures with rim Bevels. Analytic side-normal error and planar-cap error are measured separately. This does not certify unfamiliar-asset fidelity, arbitrary curvature, SubD behavior, or a universal modifier prescription.",
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CURVED_BEVEL_NORMAL_POLICY_RESULT:" + json.dumps(report))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
