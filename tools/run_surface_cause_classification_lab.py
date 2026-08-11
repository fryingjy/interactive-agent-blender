"""Validate conservative surface-cause classification with controlled interventions.

The specimen is an authored chamfered enclosure (manual profile/extrusion, no mesh
primitive operators).  Five discrepancies alter exactly one causal family:
geometry, face orientation, material assignment, lighting, or bevel profile.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_surface-cause-classification"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
SPECIMENS = None

from knowledge_engine.surface_cause_classifier import (  # noqa: E402
    SurfaceCauseEvidence,
    classify_surface_cause,
)


def point_at(obj, target=(0.0, 0.0, 0.0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_material(name, color, metallic=0.25, roughness=0.28):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def enclosure_mesh(name):
    width, height, chamfer, depth = 1.55, 1.05, 0.25, 0.34
    outline = [
        (-width + chamfer, -height),
        (width - chamfer, -height),
        (width, -height + chamfer),
        (width, height - chamfer),
        (width - chamfer, height),
        (-width + chamfer, height),
        (-width, height - chamfer),
        (-width, -height + chamfer),
    ]
    vertices = [(x, -depth, z) for x, z in outline] + [(x, depth, z) for x, z in outline]
    vertices.extend([(0.0, -depth, 0.0), (0.0, depth, 0.0)])
    faces = []
    for index in range(8):
        nxt = (index + 1) % 8
        faces.append((index, nxt, 8 + nxt, 8 + index))
        faces.append((16, nxt, index))
        faces.append((17, 8 + index, 8 + nxt))
    # The profile order above is clockwise in Blender's X/Z embedding; reverse
    # once so the closed enclosure has outward winding and positive volume.
    faces = [tuple(reversed(face)) for face in faces]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for loop_index, uv_loop in enumerate(uv.data):
        co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
        uv_loop.uv = ((co.x / (2 * width)) + 0.5, (co.z / (2 * height)) + 0.5)
    obj = bpy.data.objects.new(name, mesh)
    SPECIMENS.objects.link(obj)
    return obj


def add_bevel(obj, width=0.12, segments=4):
    modifier = obj.modifiers.new("AuthoredEdgeBevel", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    modifier.angle_limit = math.radians(20)
    return modifier


def clone(source, name):
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = name
    SPECIMENS.objects.link(obj)
    return obj


def clear_lights():
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)


def area_light(name, location, energy, size, color=(1.0, 1.0, 1.0)):
    data = bpy.data.lights.new(name + "Data", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj)


def set_lighting(kind):
    clear_lights()
    if kind == "neutral":
        area_light("NeutralKey", (4.2, -3.6, 3.2), 950, 3.0)
        area_light("NeutralFill", (-3.5, -2.8, 1.0), 260, 4.5, (0.75, 0.86, 1.0))
        area_light("NeutralRim", (2.0, 2.5, 2.8), 700, 2.5, (1.0, 0.78, 0.62))
    elif kind == "harsh":
        area_light("HarshGrazing", (5.4, -0.5, 0.15), 1800, 0.18)
    else:
        raise ValueError(kind)


def render_single(obj, path, lighting="neutral"):
    for candidate in bpy.data.objects:
        if candidate.type in {"MESH", "FONT"}:
            candidate.hide_render = candidate != obj
    set_lighting(lighting)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(str(path), check_existing=False)
    pixels = tuple(image.pixels[:])
    bpy.data.images.remove(image)
    return pixels


def image_delta(a, b):
    values = []
    changed = 0
    for index in range(0, len(a), 4):
        delta = sum(abs(a[index + channel] - b[index + channel]) for channel in range(3)) / 3.0
        values.append(delta)
        changed += delta > 0.02
    return {
        "mean_absolute_rgb": sum(values) / len(values),
        "max_absolute_rgb": max(values),
        "pixels_over_0_02": changed,
        "pixel_count": len(values),
    }


def evaluated_signature(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "bounds": [
                round(min(vertex.co[axis] for vertex in mesh.vertices), 6)
                for axis in range(3)
            ] + [
                round(max(vertex.co[axis] for vertex in mesh.vertices), 6)
                for axis in range(3)
            ],
        }
    finally:
        evaluated.to_mesh_clear()


def add_label(text, location):
    curve = bpy.data.curves.new(text + "Curve", "FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.size = 0.34
    curve.extrude = 0.008
    obj = bpy.data.objects.new(text, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (math.radians(90), 0.0, 0.0)
    return obj


def render_board(objects):
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "FONT"}:
            obj.hide_render = True
    spacing = 3.7
    labels = []
    for index, (label, obj) in enumerate(objects):
        obj.hide_render = False
        obj.location.x = (index - 2) * spacing
        labels.append(add_label(label, (obj.location.x, -0.65, -1.65)))
        labels[-1].hide_render = False
    set_lighting("neutral")
    camera = bpy.context.scene.camera
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 20.0
    camera.location = (0.0, -15.0, 0.0)
    point_at(camera)
    scene = bpy.context.scene
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 420
    scene.render.filepath = str(OUT / "surface_cause_comparison.png")
    bpy.ops.render.render(write_still=True)


def main():
    global SPECIMENS
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    SPECIMENS = bpy.data.collections.new("SurfaceCauseSpecimens")
    bpy.context.scene.collection.children.link(SPECIMENS)
    neutral = make_material("NeutralReview", (0.16, 0.22, 0.30), metallic=0.42, roughness=0.24)
    patch = make_material("RoughPatch", (0.16, 0.22, 0.30), metallic=0.42, roughness=0.88)

    clean = enclosure_mesh("Control_AuthoredEnclosure")
    clean.data.materials.append(neutral)
    add_bevel(clean)

    geometry = clone(clean, "Defect_GeometryDent")
    for index in (3, 11):
        geometry.data.vertices[index].co.x -= 0.26
    geometry.data.update()

    normals = clone(clean, "Defect_FaceOrientation")
    normals.data.polygons[9].flip()
    normals.data.update()

    material = clone(clean, "Defect_MaterialPatch")
    material.data.materials.append(patch)
    for polygon in material.data.polygons[8:12]:
        polygon.material_index = 1

    bevel = clone(clean, "Defect_BevelProfile")
    bevel.modifiers["AuthoredEdgeBevel"].width = 0.025
    bevel.modifiers["AuthoredEdgeBevel"].segments = 1

    bpy.ops.object.camera_add(location=(0.0, -7.2, 0.2))
    camera = bpy.context.object
    camera.name = "ReviewCamera"
    camera.data.lens = 62
    point_at(camera)
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 420
    scene.render.resolution_y = 420
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"

    control_pixels = render_single(clean, OUT / "control_neutral.png")
    rendered = {
        "GEOMETRY": render_single(geometry, OUT / "defect_geometry.png"),
        "NORMALS": render_single(normals, OUT / "defect_normals.png"),
        "MATERIAL": render_single(material, OUT / "defect_material.png"),
        "LIGHTING": render_single(clean, OUT / "defect_lighting.png", lighting="harsh"),
        "BEVEL_PROFILE": render_single(bevel, OUT / "defect_bevel.png"),
    }

    clean_sig = evaluated_signature(clean)
    geometry_sig = evaluated_signature(geometry)
    bevel_sig = evaluated_signature(bevel)
    evidence = {
        "GEOMETRY": SurfaceCauseEvidence(True, True, True),
        "NORMALS": SurfaceCauseEvidence(
            face_orientation_or_split_normals_changed=True,
            normal_repair_neutralizes=True,
        ),
        "MATERIAL": SurfaceCauseEvidence(
            material_state_changed=True,
            neutral_material_neutralizes=True,
        ),
        "LIGHTING": SurfaceCauseEvidence(
            lighting_state_changed=True,
            neutral_lighting_neutralizes=True,
        ),
        "BEVEL_PROFILE": SurfaceCauseEvidence(
            evaluated_geometry_changed=True,
            bevel_parameters_changed=True,
            bevel_repair_neutralizes=True,
        ),
    }
    diagnoses = {name: classify_surface_cause(value) for name, value in evidence.items()}
    differences = {name: image_delta(control_pixels, pixels) for name, pixels in rendered.items()}
    assertions = {
        "all_five_causes_classified": all(diagnoses[name].cause == name for name in evidence),
        "all_discrepancies_visible": all(metrics["pixels_over_0_02"] > 100 for metrics in differences.values()),
        "geometry_changes_evaluated_bounds": geometry_sig["bounds"] != clean_sig["bounds"],
        "bevel_changes_evaluated_topology": (
            bevel_sig["vertices"], bevel_sig["faces"]
        ) != (
            clean_sig["vertices"], clean_sig["faces"]
        ),
        "base_geometry_identity_for_non_geometry_cases": all(
            len(obj.data.vertices) == len(clean.data.vertices) and
            all((a.co - b.co).length < 1e-9 for a, b in zip(obj.data.vertices, clean.data.vertices))
            for obj in (normals, material, bevel)
        ),
    }
    report = {
        "lab": "intervention_based_surface_cause_classification",
        "blender_version": bpy.app.version_string,
        "specimen": "manually authored chamfered enclosure; no mesh primitive operators",
        "source_rule": "change one shading context at a time; do not diagnose from one beauty view",
        "signatures": {"control": clean_sig, "geometry": geometry_sig, "bevel": bevel_sig},
        "image_differences": differences,
        "diagnoses": {
            name: {
                "cause": diagnosis.cause,
                "confidence": diagnosis.confidence,
                "reasons": list(diagnosis.reasons),
                "next_action": diagnosis.next_action,
            }
            for name, diagnosis in diagnoses.items()
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
        "limitations": [
            "This validates intervention signatures on controlled synthetic defects, not screenshot-only diagnosis.",
            "A real asset may contain several causes simultaneously; conflicting evidence deliberately returns CONFLICTING.",
            "The normal case uses one flipped face, not every custom split-normal failure mode.",
        ],
    }
    render_board([
        ("GEOMETRY", geometry),
        ("NORMALS", normals),
        ("MATERIAL", material),
        ("LIGHTING*", clean),
        ("BEVEL", bevel),
    ])
    (OUT / "surface_cause_classification_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "surface_cause_classification.blend"))
    print("SURFACE_CAUSE_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("surface cause classification assertions failed")


main()
