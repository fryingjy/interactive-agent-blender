"""Diagnose interacting surface causes on the connected-quad barrel.

Run with the verified stage-3 barrel open.  The script creates a mixed fault
(geometry dent, flipped patch, rough material patch, unnecessary bevel, and bad
review lighting), performs one-variable ablations, then repairs causes
sequentially.  No mesh primitive operator is used.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-11_mixed-surface-diagnosis"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

from knowledge_engine.surface_cause_classifier import (  # noqa: E402
    SurfaceCauseAblation,
    diagnose_mixed_surface_causes,
)


SOURCE_NAME = "Barrel_Body_Profile"
COLLECTION_NAME = "MixedSurfaceDiagnosis"
OBJECT_CAUSES = ("GEOMETRY", "NORMALS", "MATERIAL", "BEVEL_PROFILE")
ALL_CAUSES = (*OBJECT_CAUSES, "LIGHTING")
SPECIMENS = None
LIGHT_RIGS = {}


def point_at(obj, target=(0.0, 0.0, 0.0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def material(name, color, metallic, roughness):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return value


def face_center(mesh, polygon):
    total = Vector((0.0, 0.0, 0.0))
    for index in polygon.vertices:
        total += mesh.vertices[index].co
    return total / len(polygon.vertices)


def make_variant(source, name, causes, clean_material, rough_material):
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = name
    SPECIMENS.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(clean_material)
    for polygon in obj.data.polygons:
        polygon.material_index = 0
        polygon.use_smooth = True

    if "GEOMETRY" in causes:
        for vertex in obj.data.vertices:
            co = vertex.co
            if co.y >= -0.45:
                continue
            distance2 = ((co.x + 0.62) / 0.42) ** 2 + ((co.z - 0.48) / 0.55) ** 2
            influence = math.exp(-2.1 * distance2)
            if influence < 0.015:
                continue
            radius = math.hypot(co.x, co.y)
            if radius > 1e-8:
                repaired_radius = radius - 0.19 * influence
                scale = repaired_radius / radius
                co.x *= scale
                co.y *= scale

    if "NORMALS" in causes:
        candidates = []
        for polygon in obj.data.polygons:
            center = face_center(obj.data, polygon)
            if center.y < -0.85 and abs(center.x - 0.58) < 0.34 and abs(center.z + 0.45) < 0.48:
                candidates.append(polygon.index)
        for index in candidates[:18]:
            obj.data.polygons[index].flip()
        obj["mixed_flipped_faces"] = candidates[:18]

    if "MATERIAL" in causes:
        obj.data.materials.append(rough_material)
        material_faces = []
        for polygon in obj.data.polygons:
            center = face_center(obj.data, polygon)
            if center.y < -0.78 and abs(center.x - 0.48) < 0.42 and abs(center.z - 0.75) < 0.42:
                polygon.material_index = 1
                material_faces.append(polygon.index)
        obj["mixed_material_faces"] = material_faces

    if "BEVEL_PROFILE" in causes:
        modifier = obj.modifiers.new("Unnecessary_Global_Bevel", "BEVEL")
        modifier.width = 0.018
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
        modifier.angle_limit = math.radians(24.0)

    obj.data.update()
    obj["active_surface_causes"] = ",".join(sorted(causes))
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
    obj["diagnosis_energy"] = energy
    point_at(obj, (0.0, 0.0, 0.15))
    return obj


def setup_lighting():
    global LIGHT_RIGS
    clear_lights()
    LIGHT_RIGS = {
        "neutral": [
            area_light("Neutral_Key", (-4.0, -5.0, 5.0), 950, 3.2, (1.0, 0.82, 0.70)),
            area_light("Neutral_Fill", (4.0, -3.0, 1.0), 380, 4.0, (0.68, 0.82, 1.0)),
            area_light("Neutral_Rim", (2.0, 3.5, 4.2), 780, 2.8, (1.0, 0.58, 0.34)),
        ],
        "faulty": [
            area_light("Faulty_Flat_Key", (-0.4, -6.5, 1.2), 1050, 5.8, (0.72, 0.84, 1.0)),
            area_light("Faulty_Hot_Rim", (4.8, 1.0, 2.4), 900, 0.5, (1.0, 0.30, 0.12)),
        ],
    }


def set_lighting(kind):
    if kind not in LIGHT_RIGS:
        raise ValueError(kind)
    for rig_name, lights in LIGHT_RIGS.items():
        for light in lights:
            active = rig_name == kind
            light.hide_render = not active
            light.data.energy = float(light["diagnosis_energy"]) if active else 0.0


def render(obj, path, lighting):
    for candidate in bpy.data.objects:
        if candidate.type == "MESH":
            candidate.hide_render = candidate != obj
    set_lighting(lighting)
    # Object visibility and newly linked light datablocks must reach the render
    # dependency graph before the next background render.  Omitting this update
    # produced a retained stale-light failure where the neutral repeat rendered
    # with the preceding faulty rig.
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(str(path), check_existing=False)
    pixels = tuple(image.pixels[:])
    bpy.data.images.remove(image)
    return pixels


def image_delta(control, candidate):
    values = []
    changed = 0
    for index in range(0, len(control), 4):
        delta = sum(abs(control[index + channel] - candidate[index + channel]) for channel in range(3)) / 3.0
        values.append(delta)
        changed += delta > 0.02
    return {
        "mean_absolute_rgb": sum(values) / len(values),
        "max_absolute_rgb": max(values),
        "pixels_over_0_02": changed,
        "pixel_count": len(values),
    }


def digest(values):
    payload = json.dumps(values, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def state_signature(obj):
    geometry = [[round(value, 7) for value in vertex.co] for vertex in obj.data.vertices]
    winding = [list(polygon.vertices) for polygon in obj.data.polygons]
    materials = [polygon.material_index for polygon in obj.data.polygons]
    bevel = [
        [modifier.name, round(modifier.width, 7), modifier.segments, modifier.limit_method]
        for modifier in obj.modifiers if modifier.type == "BEVEL"
    ]
    return {
        "GEOMETRY": digest(geometry),
        "NORMALS": digest(winding),
        "MATERIAL": digest(materials),
        "BEVEL_PROFILE": digest(bevel),
    }


def evaluated_health(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        return {
            "vertices": len(mesh.vertices),
            "faces": len(mesh.polygons),
            "triangles": len(mesh.loop_triangles),
            "degenerate_faces": sum(polygon.area < 1e-10 for polygon in mesh.polygons),
        }
    finally:
        evaluated.to_mesh_clear()


def main():
    global SPECIMENS
    source = bpy.data.objects.get(SOURCE_NAME)
    if source is None:
        raise SystemExit(f"open the stage-3 barrel; missing {SOURCE_NAME}")

    for collection in list(bpy.data.collections):
        if collection.name == COLLECTION_NAME:
            bpy.data.collections.remove(collection)
    SPECIMENS = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(SPECIMENS)
    source.hide_render = True

    clean_material = material("Diagnosis_CleanPaint", (0.24, 0.055, 0.035), 0.62, 0.24)
    rough_material = material("Diagnosis_RoughPatch", (0.08, 0.16, 0.30), 0.12, 0.92)
    clean = make_variant(source, "Diagnosis_Clean_Control", set(), clean_material, rough_material)
    mixed_object_causes = set(OBJECT_CAUSES)
    mixed = make_variant(source, "Diagnosis_Mixed_FiveCause", mixed_object_causes, clean_material, rough_material)

    old_camera = bpy.context.scene.camera
    if old_camera:
        old_camera.hide_render = True
    camera_data = bpy.data.cameras.new("DiagnosisCameraData")
    camera_data.lens = 66
    camera = bpy.data.objects.new("DiagnosisCamera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (6.2, -8.2, 3.6)
    point_at(camera, (0.0, 0.0, 0.05))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.seed = 37
    scene.cycles.use_animated_seed = False
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.render.resolution_x = 400
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    setup_lighting()

    control_pixels = render(clean, OUT / "control_clean_neutral.png", "neutral")
    mixed_pixels = render(mixed, OUT / "mixed_five_cause.png", "faulty")
    mixed_error = image_delta(control_pixels, mixed_pixels)

    mixed_signature = state_signature(mixed)
    remaining_causes = set(ALL_CAUSES)
    current_object_causes = set(OBJECT_CAUSES)
    current_lighting = "faulty"
    current_object = mixed
    current_error = mixed_error
    selected_evidence = []
    sequential = []
    trial_matrix = []
    for step in range(len(ALL_CAUSES)):
        trials = []
        current_signature = state_signature(current_object)
        for cause in sorted(remaining_causes):
            candidate_object_causes = set(current_object_causes)
            candidate_lighting = current_lighting
            if cause == "LIGHTING":
                candidate_lighting = "neutral"
            else:
                candidate_object_causes.remove(cause)
            candidate = make_variant(
                source,
                f"Diagnosis_Greedy_S{step + 1}_{cause}",
                candidate_object_causes,
                clean_material,
                rough_material,
            )
            pixels = render(candidate, OUT / f"greedy_s{step + 1}_{cause.lower()}.png", candidate_lighting)
            error = image_delta(control_pixels, pixels)
            signature = state_signature(candidate)
            if cause == "LIGHTING":
                target_changed = candidate_lighting != current_lighting
                unrelated_constant = signature == current_signature
            else:
                target_changed = signature[cause] != current_signature[cause]
                unrelated_constant = all(
                    signature[channel] == current_signature[channel]
                    for channel in OBJECT_CAUSES if channel != cause
                )
            trials.append({
                "cause": cause,
                "object": candidate,
                "object_causes": candidate_object_causes,
                "lighting": candidate_lighting,
                "error": error,
                "target_state_changed": target_changed,
                "unrelated_states_held_constant": unrelated_constant,
            })
        selected = min(
            trials,
            key=lambda item: (
                not (
                    item["error"]["mean_absolute_rgb"] < current_error["mean_absolute_rgb"]
                    and item["error"]["pixels_over_0_02"] < current_error["pixels_over_0_02"]
                ),
                item["error"]["mean_absolute_rgb"],
                item["error"]["pixels_over_0_02"],
            ),
        )
        trial_matrix.append({
            "step": step + 1,
            "before_error": current_error,
            "selected": selected["cause"],
            "trials": [
                {"cause": item["cause"], "error": item["error"]}
                for item in trials
            ],
        })
        selected_evidence.append(SurfaceCauseAblation(
            cause=selected["cause"],
            intervention_applied=True,
            target_state_changed=selected["target_state_changed"],
            unrelated_states_held_constant=selected["unrelated_states_held_constant"],
            before_error=current_error["mean_absolute_rgb"],
            after_error=selected["error"]["mean_absolute_rgb"],
            before_changed_pixels=current_error["pixels_over_0_02"],
            after_changed_pixels=selected["error"]["pixels_over_0_02"],
        ))
        sequential.append(selected)
        remaining_causes.remove(selected["cause"])
        current_object_causes = selected["object_causes"]
        current_lighting = selected["lighting"]
        current_object = selected["object"]
        current_error = selected["error"]

    diagnosis = diagnose_mixed_surface_causes(tuple(selected_evidence), minimum_relative_reduction=0.005)
    repaired = sequential[-1]["object"]
    repaired.name = "Diagnosis_Fully_Repaired"
    sequence_errors = [item["error"] for item in sequential]
    sequence_labels = [f"repair_{item['cause'].lower()}" for item in sequential]

    monotonic = all(
        later["mean_absolute_rgb"] <= earlier["mean_absolute_rgb"] + 2e-4
        for earlier, later in zip(sequence_errors, sequence_errors[1:])
    )
    final_error = sequence_errors[-1]
    repeat_pixels = render(clean, OUT / "control_clean_neutral_repeat.png", "neutral")
    repeat_error = image_delta(control_pixels, repeat_pixels)
    repeat_mean_gate = repeat_error["mean_absolute_rgb"] * 1.20 + 0.0005
    repeat_pixel_gate = int(repeat_error["pixels_over_0_02"] * 1.20 + 500)
    mixed_health = evaluated_health(mixed)
    repaired_health = evaluated_health(repaired)
    assertions = {
        "source_body_is_connected_all_quad": (
            len(source.data.polygons) == 5376
            and all(len(polygon.vertices) == 4 for polygon in source.data.polygons)
        ),
        "all_five_causes_confirmed_by_controlled_ablation": set(diagnosis.causes) == set(ALL_CAUSES),
        "no_ablation_rejected": not diagnosis.rejected,
        "each_selected_ablation_reduces_mean_error": all(
            item.after_error < item.before_error for item in selected_evidence
        ),
        "sequential_repairs_nonincreasing": monotonic,
        "full_repair_state_matches_clean": state_signature(repaired) == state_signature(clean),
        "full_repair_within_render_repeatability_mean": final_error["mean_absolute_rgb"] <= repeat_mean_gate,
        "full_repair_within_render_repeatability_pixels": final_error["pixels_over_0_02"] <= repeat_pixel_gate,
        "faulty_blanket_bevel_exposes_degenerates": mixed_health["degenerate_faces"] > 0,
        "repaired_evaluated_has_no_degenerates": repaired_health["degenerate_faces"] == 0,
    }
    report = {
        "lab": "mixed_cause_surface_diagnosis_on_connected_quad_barrel",
        "blender_version": bpy.app.version_string,
        "source_blend": bpy.data.filepath,
        "source_object": SOURCE_NAME,
        "source_boundary": "reuses the source-tuned connected-quad barrel as a production-style diagnosis testbed; not held-out modeling evidence",
        "causes_injected": list(ALL_CAUSES),
        "mixed_error": mixed_error,
        "ablation_evidence": [item.__dict__ for item in selected_evidence],
        "greedy_trial_matrix": trial_matrix,
        "diagnosis": {
            "status": diagnosis.status,
            "causes": list(diagnosis.causes),
            "rejected": list(diagnosis.rejected),
            "confidence": diagnosis.confidence,
            "reductions": [list(item) for item in diagnosis.reductions],
            "next_action": diagnosis.next_action,
        },
        "repair_sequence": [
            {"step": label, "error": error}
            for label, error in zip(sequence_labels, sequence_errors)
        ],
        "render_repeatability": {
            "control_repeat_error": repeat_error,
            "accepted_mean_error_max": repeat_mean_gate,
            "accepted_changed_pixels_max": repeat_pixel_gate,
        },
        "state_signatures": {
            "mixed": mixed_signature,
            "repaired": state_signature(repaired),
        },
        "evaluated_health": {
            "clean": evaluated_health(clean),
            "mixed": mixed_health,
            "repaired": repaired_health,
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
        "limitations": [
            "The five faults are intentionally injected and their ground truth is known; this tests controlled diagnosis and repair, not diagnosis from an unknown beauty image.",
            "The barrel was source-tuned in an earlier corrective benchmark, so this does not add held-out modeling evidence.",
            "Pixel ablation measures this fixed camera/light/material setup and does not replace experienced surface review.",
        ],
    }
    render(repaired, OUT / "fully_repaired.png", "neutral")
    (OUT / "mixed_surface_diagnosis_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj.hide_render = obj != repaired
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "mixed_surface_diagnosis.blend"))
    print("MIXED_SURFACE_DIAGNOSIS_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("mixed surface diagnosis assertions failed")


main()
