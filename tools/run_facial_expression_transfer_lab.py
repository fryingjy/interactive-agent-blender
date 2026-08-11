"""Transfer driven corrective deformation to Blender's official animation head.

Run after opening the official Human Base Meshes bundle:
    blender bundle.blend --background --python this_file.py -- OUTPUT_DIR

The source datablocks are copied and transformed into a new isolated scene.  The
source file is never saved or modified.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SOURCE_NAME = "GEO-head_animation_realistic"
COLLECTION_NAME = "FacialExpressionTransfer"


def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def output_directory():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(values) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    output = Path(values[0]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


def centered_source_mesh(source):
    mesh = source.data.copy()
    mesh.transform(source.matrix_world)
    xs = [vert.co.x for vert in mesh.vertices]
    ys = [vert.co.y for vert in mesh.vertices]
    zs = [vert.co.z for vert in mesh.vertices]
    center = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
    mesh.transform(Matrix.Translation(-center))
    bounds = {
        "min": [min(vert.co[index] for vert in mesh.vertices) for index in range(3)],
        "max": [max(vert.co[index] for vert in mesh.vertices) for index in range(3)],
    }
    return mesh, center, bounds


def make_head(name, base_mesh, collection):
    mesh = base_mesh.copy()
    mesh.name = name + "Mesh"
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def feature_frame(bounds):
    mins, maxs = bounds["min"], bounds["max"]
    height = maxs[2] - mins[2]
    width = maxs[0] - mins[0]
    depth = maxs[1] - mins[1]
    return {
        "height": height,
        "width": width,
        "depth": depth,
        "front_y": mins[1],
        "mouth_z": mins[2] + height * 0.335,
        "chin_z": mins[2] + height * 0.22,
        "jaw_hinge_z": mins[2] + height * 0.43,
    }


def front_weight(co, frame):
    return 1.0 - smoothstep(frame["front_y"] + frame["depth"] * 0.18, frame["front_y"] + frame["depth"] * 0.58, co.y)


def mouth_corner_weight(co, frame):
    half_corner = frame["width"] * 0.17
    dx = abs(co.x)
    x_weight = math.exp(-(((dx - half_corner) / (frame["width"] * 0.105)) ** 2))
    z_weight = math.exp(-(((co.z - frame["mouth_z"]) / (frame["height"] * 0.075)) ** 2))
    return x_weight * z_weight * front_weight(co, frame)


def mouth_region_weight(co, frame, broad=False):
    x_scale = frame["width"] * (0.33 if broad else 0.26)
    z_scale = frame["height"] * (0.12 if broad else 0.09)
    radial = math.exp(-((co.x / x_scale) ** 2) - (((co.z - frame["mouth_z"]) / z_scale) ** 2))
    return radial * front_weight(co, frame)


def add_shapes(obj, frame, corrective="none"):
    obj.shape_key_add(name="Basis")
    smile = obj.shape_key_add(name="SmileWide")
    for index, vertex in enumerate(obj.data.vertices):
        co = vertex.co
        weight = mouth_corner_weight(co, frame)
        direction = -1.0 if co.x < 0 else 1.0
        smile.data[index].co.x += direction * frame["width"] * 0.036 * weight
        smile.data[index].co.z += frame["height"] * 0.022 * weight
        smile.data[index].co.y -= frame["depth"] * 0.012 * weight
    correction = None
    if corrective != "none":
        correction = obj.shape_key_add(name="JawSmileCorrective")
        fine = corrective == "fine"
        for index, vertex in enumerate(obj.data.vertices):
            co = vertex.co
            weight = mouth_region_weight(co, frame, broad=fine)
            corner = mouth_corner_weight(co, frame)
            lower = 1.0 - smoothstep(frame["mouth_z"] - frame["height"] * 0.015, frame["mouth_z"] + frame["height"] * 0.05, co.z)
            correction.data[index].co.y -= frame["depth"] * (0.026 if fine else 0.022) * weight
            correction.data[index].co.z += frame["height"] * (0.030 if fine else 0.025) * weight * lower
            correction.data[index].co.x += (1 if co.x >= 0 else -1) * frame["width"] * (0.010 if fine else 0.008) * corner
    return smile, correction


def driver_variable(driver, name, rig, bone, transform):
    variable = driver.variables.new()
    variable.name = name
    variable.type = "TRANSFORMS"
    target = variable.targets[0]
    target.id = rig
    target.bone_target = bone
    target.transform_type = transform
    target.transform_space = "LOCAL_SPACE"


def build_rig(name, obj, frame, smile_key, corrective_key=None):
    armature = bpy.data.armatures.new(name + "Data")
    rig = bpy.data.objects.new(name, armature)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root = armature.edit_bones.new("HeadRoot")
    root.head, root.tail = (0, 0.02, -frame["height"] * 0.45), (0, 0.02, frame["height"] * 0.40)
    jaw = armature.edit_bones.new("Jaw")
    jaw.head = (0, frame["depth"] * 0.18, frame["jaw_hinge_z"])
    jaw.tail = (0, frame["front_y"] * 0.55, frame["chin_z"])
    jaw.parent = root
    for side, sign in (("L", -1), ("R", 1)):
        control = armature.edit_bones.new("Smile." + side)
        control.head = (sign * frame["width"] * 0.19, frame["front_y"] * 1.08, frame["mouth_z"])
        control.tail = control.head + Vector((0, 0, frame["height"] * 0.08))
        control.parent = root
        control.use_deform = False
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)

    # Non-quads in the official source are intentional closure/interior
    # structures.  Keep their complete one-ring out of the jaw weights so a
    # partial weighted triangle/n-gon cannot tear against the quad lip flow.
    forbidden = set()
    for polygon in obj.data.polygons:
        if len(polygon.vertices) != 4:
            forbidden.update(polygon.vertices)
    jaw_group = obj.vertex_groups.new(name="Jaw")
    jaw_vertices = []
    for vertex in obj.data.vertices:
        co = vertex.co
        below = 1.0 - smoothstep(frame["mouth_z"] - frame["height"] * 0.02, frame["mouth_z"] + frame["height"] * 0.02, co.z)
        neck_guard = smoothstep(frame["chin_z"] - frame["height"] * 0.02, frame["chin_z"] + frame["height"] * 0.06, co.z)
        weight = below * neck_guard * (0.45 + 0.55 * front_weight(co, frame))
        if weight > 0.001 and vertex.index not in forbidden:
            jaw_group.add([vertex.index], weight, "REPLACE")
            jaw_vertices.append(vertex.index)
    modifier = obj.modifiers.new("Facial_Armature", "ARMATURE")
    modifier.object = rig
    modifier.use_deform_preserve_volume = True
    subd = obj.modifiers.new("Review_Subdivision", "SUBSURF")
    subd.levels = subd.render_levels = 1

    curve = smile_key.driver_add("value")
    driver = curve.driver
    driver.type = "SCRIPTED"
    driver_variable(driver, "left", rig, "Smile.L", "LOC_X")
    driver_variable(driver, "right", rig, "Smile.R", "LOC_X")
    driver.expression = f"min(1,(abs(left)+abs(right))/{frame['width'] * 0.18:.9f})"
    if corrective_key is not None:
        curve = corrective_key.driver_add("value")
        driver = curve.driver
        driver.type = "SCRIPTED"
        driver_variable(driver, "jaw", rig, "Jaw", "ROT_X")
        driver_variable(driver, "left", rig, "Smile.L", "LOC_X")
        driver_variable(driver, "right", rig, "Smile.R", "LOC_X")
        driver.expression = f"min(1,abs(jaw)/{math.radians(8):.9f})*min(1,(abs(left)+abs(right))/{frame['width'] * 0.18:.9f})"
    return rig, jaw_vertices


def pose(rig, frame, jaw_degrees, smile_value):
    jaw = rig.pose.bones["Jaw"]
    jaw.rotation_mode = "XYZ"
    jaw.rotation_euler.x = math.radians(jaw_degrees)
    rig.pose.bones["Smile.L"].location.x = -frame["width"] * 0.09 * smile_value
    rig.pose.bones["Smile.R"].location.x = frame["width"] * 0.09 * smile_value
    bpy.context.view_layer.update()


def evaluated(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    verts = [vertex.co.copy() for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    eval_obj.to_mesh_clear()
    return verts, polygons


def surface_error(obj, tree, frame):
    verts, polygons = evaluated(obj)
    all_distances, mouth_distances = [], []
    for polygon in polygons:
        center = sum((verts[index] for index in polygon), Vector()) / len(polygon)
        nearest = tree.find_nearest(center)
        distance = nearest[3] if nearest else float("inf")
        all_distances.append(distance)
        if abs(center.x) < frame["width"] * 0.34 and abs(center.z - frame["mouth_z"]) < frame["height"] * 0.18 and center.y < frame["front_y"] + frame["depth"] * 0.6:
            mouth_distances.append(distance)
    return {
        "mean": sum(all_distances) / len(all_distances),
        "max": max(all_distances),
        "mouth_mean": sum(mouth_distances) / len(mouth_distances),
        "mouth_max": max(mouth_distances),
        "mouth_faces": len(mouth_distances),
    }


def topology_stats(obj, jaw_indices, frame):
    jaw_set = set(jaw_indices)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    stats = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "jaw_weighted_vertices": len(jaw_set),
        "non_quad_faces_touching_weighted_jaw": sum(len(face.verts) != 4 and any(vert.index in jaw_set for vert in face.verts) for face in bm.faces),
    }
    bm.free()
    return stats


def material(name, color):
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.48
    return value


def point_at(obj, target=(0, 0, 0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(path, heads, rigs, frame, jaw, smile):
    for rig in rigs:
        pose(rig, frame, jaw, smile)
        # Armatures have no renderable surface.  Do not hide them: hiding a
        # parent armature also hides its child head from the render.
        rig.hide_render = False
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_focus(path, focus_index, heads, rigs, frame, jaw, smile):
    scene = bpy.context.scene
    camera = scene.camera
    previous_scale = camera.data.ortho_scale
    previous_location = camera.location.copy()
    hidden = [head.hide_render for head in heads]
    try:
        for index, head in enumerate(heads):
            head.hide_render = index != focus_index
        for rig in rigs:
            pose(rig, frame, jaw, smile)
        camera.data.ortho_scale = frame["height"] * 1.42
        camera.location.x = rigs[focus_index].location.x
        point_at(camera, (rigs[focus_index].location.x, 0, 0))
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
    finally:
        for head, value in zip(heads, hidden):
            head.hide_render = value
        camera.data.ortho_scale = previous_scale
        camera.location = previous_location
        point_at(camera)


def main():
    output = output_directory()
    source_path = bpy.data.filepath
    source = bpy.data.objects.get(SOURCE_NAME)
    if source is None:
        raise SystemExit(f"source bundle lacks {SOURCE_NAME}")
    base_mesh, source_center, bounds = centered_source_mesh(source)
    frame = feature_frame(bounds)

    scene = bpy.data.scenes.new("FacialExpressionTransferScene")
    bpy.context.window.scene = scene
    collection = bpy.data.collections.new(COLLECTION_NAME)
    scene.collection.children.link(collection)
    target = make_head("Dense_Corrected_Reference", base_mesh, collection)
    uncorrected = make_head("Purposeful_Uncorrected_Face", base_mesh, collection)
    corrected = make_head("Purposeful_DrivenCorrective_Face", base_mesh, collection)
    target_smile, target_correction = add_shapes(target, frame, "fine")
    uncorrected_smile, _ = add_shapes(uncorrected, frame, "none")
    corrected_smile, corrected_correction = add_shapes(corrected, frame, "coarse")
    target_rig, target_jaw = build_rig("Dense_Face_Rig", target, frame, target_smile, target_correction)
    uncorrected_rig, uncorrected_jaw = build_rig("Uncorrected_Face_Rig", uncorrected, frame, uncorrected_smile)
    corrected_rig, corrected_jaw = build_rig("Corrected_Face_Rig", corrected, frame, corrected_smile, corrected_correction)
    target.modifiers["Review_Subdivision"].levels = target.modifiers["Review_Subdivision"].render_levels = 2
    heads = [target, uncorrected, corrected]
    rigs = [target_rig, uncorrected_rig, corrected_rig]
    for obj, color in zip(heads, ((0.58, 0.64, 0.74), (0.78, 0.10, 0.07), (0.08, 0.52, 0.22))):
        obj.data.materials.clear()
        obj.data.materials.append(material(obj.name + "Material", color))

    for rig in rigs:
        pose(rig, frame, 10.0, 1.0)
    target_verts, target_polygons = evaluated(target)
    tree = BVHTree.FromPolygons(target_verts, target_polygons, all_triangles=False)
    uncorrected_error = surface_error(uncorrected, tree, frame)
    corrected_error = surface_error(corrected, tree, frame)
    improvement = uncorrected_error["mouth_mean"] / max(corrected_error["mouth_mean"], 1e-12)
    combined_value = corrected.data.shape_keys.key_blocks["JawSmileCorrective"].value
    pose(corrected_rig, frame, 10.0, 0.0)
    jaw_only_value = corrected.data.shape_keys.key_blocks["JawSmileCorrective"].value
    pose(corrected_rig, frame, 0.0, 1.0)
    smile_only_value = corrected.data.shape_keys.key_blocks["JawSmileCorrective"].value
    pose(corrected_rig, frame, 0.0, 0.0)
    rest_value = corrected.data.shape_keys.key_blocks["JawSmileCorrective"].value

    topology = topology_stats(corrected, corrected_jaw, frame)
    assertions = {
        "closed_source_copy": topology["non_manifold_edges"] == 0,
        "no_degenerate_faces": topology["degenerate_faces"] == 0,
        "weighted_jaw_region_is_all_quad": topology["non_quad_faces_touching_weighted_jaw"] == 0,
        "jaw_region_has_targeted_density": topology["jaw_weighted_vertices"] >= 100,
        "corrective_zero_at_rest": rest_value < 0.01,
        "corrective_rejects_jaw_only": jaw_only_value < 0.01,
        "corrective_rejects_smile_only": smile_only_value < 0.01,
        "corrective_activates_combined": combined_value > 0.9,
        "corrective_improves_mouth_mean": corrected_error["mouth_mean"] < uncorrected_error["mouth_mean"],
        "corrective_improves_mouth_max": corrected_error["mouth_max"] < uncorrected_error["mouth_max"],
        "meaningful_mouth_improvement": improvement > 1.15,
    }

    spacing = frame["width"] * 1.45
    for offset, obj, rig in zip((-spacing, 0.0, spacing), heads, rigs):
        obj.parent = rig
        obj.matrix_parent_inverse = rig.matrix_world.inverted()
        rig.location.x = offset
    camera_data = bpy.data.cameras.new("FacialReviewCameraData")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(frame["height"] * 1.42, spacing * 2 + frame["width"] * 1.25)
    camera = bpy.data.objects.new("FacialReviewCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0, frame["front_y"] - frame["depth"] * 7.0, 0)
    point_at(camera)
    scene.camera = camera
    for name, location, energy, size, color in (
        ("Key", (-0.45, -0.7, 0.55), 70, 0.45, (1.0, 0.80, 0.68)),
        ("Fill", (0.55, -0.55, 0.1), 30, 0.55, (0.65, 0.78, 1.0)),
        ("Rim", (0.1, 0.45, 0.5), 50, 0.35, (1.0, 0.65, 0.5)),
    ):
        data = bpy.data.lights.new(name + "Data", "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        point_at(light)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1500, 680
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("FacialReviewWorld")
    scene.world.color = (0.008, 0.01, 0.015)
    scene.view_settings.look = "AgX - Medium High Contrast"
    render(output / "facial_rest.png", heads, rigs, frame, 0.0, 0.0)
    render(output / "facial_combined_expression.png", heads, rigs, frame, 10.0, 1.0)
    render_focus(output / "facial_uncorrected_expression.png", 1, heads, rigs, frame, 10.0, 1.0)
    render_focus(output / "facial_corrected_expression.png", 2, heads, rigs, frame, 10.0, 1.0)

    report = {
        "lab": "official_human_base_mesh_facial_expression_transfer",
        "blender_version": bpy.app.version_string,
        "source_blend": source_path,
        "source_object": SOURCE_NAME,
        "source_copy_center_world": list(source_center),
        "feature_frame": frame,
        "expression": {"jaw_rotation_x_degrees": 10.0, "bilateral_smile_control": 1.0},
        "rig": "Jaw deform bone + non-deforming bilateral smile controls + driven combined-pose relative corrective",
        "driver_values": {"rest": rest_value, "jaw_only": jaw_only_value, "smile_only": smile_only_value, "combined": combined_value},
        "topology": topology,
        "uncorrected": uncorrected_error,
        "corrected": corrected_error,
        "uncorrected_over_corrected_mouth_mean_ratio": improvement,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "limitations": [
            "The official CC0 animation base mesh supplies the anatomy and topology; this run tests rig/corrective transfer, not autonomous head modeling or retopology authorship.",
            "The dense target and low-cage correction share an authored deformation hypothesis; nearest-surface improvement is mechanism evidence, not independent anatomical truth.",
            "One combined jaw-open/smile pose does not establish a complete FACS set, lip sync, eyelid behavior, or production animator acceptance.",
            "The source mesh contains non-quads outside the weighted jaw region; the weighted expression region is checked separately rather than relabeling the whole mesh all-quad.",
        ],
    }
    (output / "facial_expression_transfer_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "facial_expression_transfer.blend"))
    print("FACIAL_EXPRESSION_TRANSFER_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("facial expression transfer assertions failed")


main()
