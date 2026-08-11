"""Fresh-process verifier for the expressive facial articulation run."""

from __future__ import annotations

import json
import sys
from array import array
from pathlib import Path

import bmesh
import bpy


def run_directory():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(values) != 1:
        raise SystemExit("expected RUN_DIR after --")
    return Path(values[0]).resolve()


def mesh_health(obj, evaluated=False):
    mesh = obj.data
    owner = None
    if evaluated:
        owner = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = owner.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
    }
    bm.free()
    if owner:
        owner.to_mesh_clear()
    return result


def driver_state(obj, key_name):
    key = obj.data.shape_keys.key_blocks[key_name]
    curves = [curve for curve in obj.data.shape_keys.animation_data.drivers if curve.data_path == key.path_from_id("value")]
    if len(curves) != 1:
        return {"count": len(curves)}
    driver = curves[0].driver
    return {
        "count": 1,
        "type": driver.type,
        "expression": driver.expression,
        "variables": sorted(variable.name for variable in driver.variables),
        "targets": sorted(variable.targets[0].bone_target for variable in driver.variables),
    }


def delta(obj, key_name, index):
    basis = obj.data.shape_keys.key_blocks["Basis"]
    key = obj.data.shape_keys.key_blocks[key_name]
    return list(key.data[index].co - basis.data[index].co)


def image_state(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    pixels = array("f", [0.0]) * (image.size[0] * image.size[1] * 4)
    image.pixels.foreach_get(pixels)
    cool, sampled = 0, 0
    pixel_stride = max(1, image.size[0] * image.size[1] // 3000)
    for pixel_index in range(0, image.size[0] * image.size[1], pixel_stride):
        index = pixel_index * 4
        red, green, blue = pixels[index], pixels[index + 1], pixels[index + 2]
        if max(red, green, blue) > 0.12:
            sampled += 1
            cool += blue > red * 1.08 and blue > green * 1.01
    result = {
        "name": path.name,
        "width": image.size[0],
        "height": image.size[1],
        "bytes": path.stat().st_size,
        "cool_pixel_fraction": cool / max(sampled, 1),
    }
    bpy.data.images.remove(image)
    return result


def main():
    run = run_directory()
    blend = run / "expressive_facial_articulation.blend"
    report = json.loads((run / "expressive_facial_articulation_report.json").read_text(encoding="utf-8"))
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False)
    baseline = bpy.data.objects.get("Failure_MouthOnly_Smile")
    integrated = bpy.data.objects.get("Integrated_Duchenne_Smile")
    rig = bpy.data.objects.get("Integrated_Face_Rig")
    if not all((baseline, integrated, rig)):
        raise SystemExit("required facial objects missing")

    base_health = mesh_health(integrated, evaluated=False)
    evaluated_health = mesh_health(integrated, evaluated=True)
    shape_names = list(integrated.data.shape_keys.key_blocks.keys())
    baseline_shape_names = list(baseline.data.shape_keys.key_blocks.keys())
    bones = sorted(rig.data.bones.keys())
    driver = driver_state(integrated, "SmileIntegrated")
    frame = report["feature_frame"]
    rig.pose.bones["Smile.L"].location.x = 0.0
    rig.pose.bones["Smile.R"].location.x = 0.0
    bpy.context.view_layer.update()
    rest_value = integrated.data.shape_keys.key_blocks["SmileIntegrated"].value
    rig.pose.bones["Smile.L"].location.x = -frame["width"] * 0.09
    rig.pose.bones["Smile.R"].location.x = frame["width"] * 0.09
    bpy.context.view_layer.update()
    pose_value = integrated.data.shape_keys.key_blocks["SmileIntegrated"].value

    landmark_deltas = {
        name: delta(integrated, "SmileIntegrated", index)
        for name, index in report["landmark_indices"].items()
    }
    report_deltas = report["integrated_landmark_deltas"]
    deltas_match = all(
        abs(actual[axis] - report_deltas[name][axis]) < 1e-8
        for name, actual in landmark_deltas.items()
        for axis in range(3)
    )
    bilateral_pairs = (("corner_left", "corner_right"), ("cheek_left", "cheek_right"), ("lid_left", "lid_right"))
    symmetry = all(
        abs(left[0] + right[0]) < 6e-5
        and abs(left[1] - right[1]) < 6e-5
        and abs(left[2] - right[2]) < 6e-5
        for left, right in ((landmark_deltas[a], landmark_deltas[b]) for a, b in bilateral_pairs)
    )
    group = integrated.vertex_groups.get("ExpressionShapeRegion")
    group_vertices = 0
    if group:
        group_vertices = sum(
            any(membership.group == group.index for membership in vertex.groups)
            for vertex in integrated.data.vertices
        )

    images = [image_state(run / name) for name in report["visual_checkpoints"]]
    image_by_name = {state["name"]: state for state in images}
    failed_dirs = sorted(path.name for path in run.iterdir() if path.is_dir() and path.name.startswith("failed_"))
    failed_reports = {}
    for directory in failed_dirs:
        path = run / directory / "expressive_facial_articulation_report.json"
        if path.exists():
            failed_reports[directory] = json.loads(path.read_text(encoding="utf-8")).get("pass")

    assertions = {
        "report_passes": report.get("pass") is True,
        "required_shape_keys_exact": shape_names == ["Basis", "SmileIntegrated"] and baseline_shape_names == ["Basis", "SmileMouthOnly"],
        "control_rig_is_non_deforming_smile_only": bones == ["HeadRoot", "Smile.L", "Smile.R"] and all(not rig.data.bones[name].use_deform for name in ("Smile.L", "Smile.R")),
        "driver_wiring_exact": driver.get("type") == "SCRIPTED" and driver.get("variables") == ["left", "right"] and driver.get("targets") == ["Smile.L", "Smile.R"],
        "driver_gates_rest_and_pose": rest_value < 0.01 and pose_value > 0.9,
        "saved_landmark_deltas_match_report": deltas_match,
        "bilateral_landmarks_are_symmetric": symmetry,
        "expression_region_membership_matches_report": group_vertices == report["topology"]["expression_vertices"],
        "base_mesh_closed_and_nondegenerate": base_health["non_manifold_edges"] == 0 and base_health["degenerate_faces"] == 0,
        "evaluated_mesh_closed_and_nondegenerate": evaluated_health["non_manifold_edges"] == 0 and evaluated_health["degenerate_faces"] == 0,
        "all_visual_checkpoints_are_1200x900": len(images) == 6 and all(image["width"] == 1200 and image["height"] == 900 and image["bytes"] > 1000 for image in images),
        "wireframe_checkpoint_contains_distinct_cool_wire_geometry": image_by_name["expression_integrated_wireframe.png"]["cool_pixel_fraction"] > 0.25 and image_by_name["expression_integrated_three_quarter.png"]["cool_pixel_fraction"] < 0.10,
        "five_failed_iterations_are_preserved": len(failed_dirs) == 5 and len(failed_reports) == 5,
    }
    result = {
        "lab": "independent_expressive_facial_articulation_verification",
        "method": "fresh factory-startup Blender process; saved scene inspected without importing generator code",
        "blender_version": bpy.app.version_string,
        "blend": str(blend),
        "shape_keys": {"integrated": shape_names, "failure": baseline_shape_names},
        "bones": bones,
        "driver": driver,
        "driver_values": {"rest": rest_value, "pose": pose_value},
        "base_health": base_health,
        "evaluated_health": evaluated_health,
        "landmark_deltas": landmark_deltas,
        "expression_region_vertices": group_vertices,
        "images": images,
        "failed_directories": failed_dirs,
        "failed_report_pass_values": failed_reports,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (run / "expressive_facial_articulation_verify.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("EXPRESSIVE_FACIAL_VERIFY_RESULT:" + json.dumps(result))
    if not result["pass"]:
        raise SystemExit(2)


main()
