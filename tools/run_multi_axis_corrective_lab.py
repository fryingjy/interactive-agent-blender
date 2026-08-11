"""Test a driven corrective shape on a flexed-and-twisted organic joint."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-11_multi-axis-corrective"
OUT.mkdir(parents=True, exist_ok=True)
COLLECTION = None


def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def radius_at(y):
    upper = 0.13 * math.exp(-(((y + 1.25) / 0.72) ** 2))
    forearm = 0.10 * math.exp(-(((y - 1.05) / 0.82) ** 2))
    elbow = 0.08 * math.exp(-((y / 0.30) ** 2))
    return 0.56 - 0.035 * ((y + 2.5) / 5.0) + upper + forearm - elbow


def build_limb(name, rings, radial_segments):
    verts = []
    for y in rings:
        radius = radius_at(y)
        for segment in range(radial_segments):
            angle = 2 * math.pi * segment / radial_segments
            verts.append((radius * math.cos(angle), y, radius * 0.92 * math.sin(angle)))
    bottom = len(verts)
    verts.append((0.0, rings[0], 0.0))
    top = len(verts)
    verts.append((0.0, rings[-1], 0.0))
    faces = []
    for row in range(len(rings) - 1):
        for segment in range(radial_segments):
            nxt = (segment + 1) % radial_segments
            a = row * radial_segments + segment
            b = row * radial_segments + nxt
            d = (row + 1) * radial_segments + segment
            c = (row + 1) * radial_segments + nxt
            faces.append((a, d, c, b))
    for segment in range(radial_segments):
        nxt = (segment + 1) % radial_segments
        faces.append((bottom, segment, nxt))
        a = (len(rings) - 1) * radial_segments + segment
        b = (len(rings) - 1) * radial_segments + nxt
        faces.append((top, b, a))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        index = loop.vertex_index
        if index < len(rings) * radial_segments:
            row, segment = divmod(index, radial_segments)
            uv.data[loop.index].uv = (segment / radial_segments, row / (len(rings) - 1))
        else:
            uv.data[loop.index].uv = (0.5, 0.5)
    obj = bpy.data.objects.new(name, mesh)
    COLLECTION.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def add_corrective_shape(obj, rings, radial_segments):
    obj.shape_key_add(name="Basis")
    key = obj.shape_key_add(name="CorrectiveFlexTwist")
    for row, y in enumerate(rings):
        elbow = math.exp(-((y / 0.42) ** 2))
        twist_root = math.exp(-(((y - 1.15) / 0.48) ** 2))
        for segment in range(radial_segments):
            index = row * radial_segments + segment
            base = obj.data.vertices[index].co
            key.data[index].co.x = base.x * (1.0 + 0.24 * elbow + 0.10 * twist_root)
            key.data[index].co.z = base.z * (1.0 + 0.14 * elbow + 0.10 * twist_root)
            key.data[index].co.y = base.y - 0.035 * elbow
    return key


def build_rig(name, obj, rings, radial_segments, corrective_key=None):
    data = bpy.data.armatures.new(name + "Data")
    rig = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    upper = data.edit_bones.new("Upper")
    upper.head, upper.tail = (0, -2.55, 0), (0, 0, 0)
    lower = data.edit_bones.new("Lower")
    lower.head, lower.tail = (0, 0, 0), (0, 1.2, 0)
    lower.parent, lower.use_connect = upper, True
    twist = data.edit_bones.new("Twist")
    twist.head, twist.tail = (0, 1.2, 0), (0, 2.5, 0)
    twist.parent, twist.use_connect = lower, True
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)

    groups = {bone: obj.vertex_groups.new(name=bone) for bone in ("Upper", "Lower", "Twist")}
    for row, y in enumerate(rings):
        lower_total = smoothstep(-0.48, 0.48, y)
        twist_weight = smoothstep(0.62, 1.62, y)
        weights = {
            "Upper": 1.0 - lower_total,
            "Lower": lower_total * (1.0 - twist_weight),
            "Twist": lower_total * twist_weight,
        }
        indices = list(range(row * radial_segments, (row + 1) * radial_segments))
        for bone, weight in weights.items():
            groups[bone].add(indices, weight, "REPLACE")
    groups["Upper"].add([len(rings) * radial_segments], 1.0, "REPLACE")
    groups["Twist"].add([len(rings) * radial_segments + 1], 1.0, "REPLACE")

    subd = obj.modifiers.new("Surface Subdivision", "SUBSURF")
    subd.levels = subd.render_levels = 1
    deform = obj.modifiers.new("Armature Flex Twist", "ARMATURE")
    deform.object = rig
    deform.use_deform_preserve_volume = False

    if corrective_key is not None:
        fcurve = corrective_key.driver_add("value")
        driver = fcurve.driver
        driver.type = "SCRIPTED"
        flex = driver.variables.new()
        flex.name = "flex"
        flex.type = "TRANSFORMS"
        flex.targets[0].id = rig
        flex.targets[0].bone_target = "Lower"
        flex.targets[0].transform_type = "ROT_X"
        flex.targets[0].transform_space = "LOCAL_SPACE"
        twist_var = driver.variables.new()
        twist_var.name = "twist"
        twist_var.type = "TRANSFORMS"
        twist_var.targets[0].id = rig
        twist_var.targets[0].bone_target = "Twist"
        twist_var.targets[0].transform_type = "ROT_Y"
        twist_var.targets[0].transform_space = "LOCAL_SPACE"
        driver.expression = "min(1,max(0,(abs(flex)-0.45)/0.75))*min(1,abs(twist)/0.8)"
    return rig


def pose(rig, flex_degrees, splay_degrees, twist_degrees):
    lower = rig.pose.bones["Lower"]
    lower.rotation_mode = "XYZ"
    lower.rotation_euler = (math.radians(flex_degrees), 0.0, math.radians(splay_degrees))
    twist = rig.pose.bones["Twist"]
    twist.rotation_mode = "XYZ"
    twist.rotation_euler.y = math.radians(twist_degrees)
    bpy.context.view_layer.update()


def evaluated(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_obj = obj.evaluated_get(depsgraph)
    mesh = evaluated_obj.to_mesh()
    verts = [vertex.co.copy() for vertex in mesh.vertices]
    polys = [tuple(poly.vertices) for poly in mesh.polygons]
    bm = bmesh.new()
    bm.from_mesh(mesh)
    volume = bm.calc_volume(signed=True)
    bm.free()
    evaluated_obj.to_mesh_clear()
    return verts, polys, volume


def surface_error(obj, target):
    verts, polys, volume = evaluated(obj)
    all_distances, joint_distances = [], []
    for poly in polys:
        center = sum((verts[i] for i in poly), Vector()) / len(poly)
        nearest = target.find_nearest(center)
        distance = nearest[3] if nearest else float("inf")
        all_distances.append(distance)
        if center.length < 1.55:
            joint_distances.append(distance)
    return {
        "mean": sum(all_distances) / len(all_distances),
        "max": max(all_distances),
        "joint_mean": sum(joint_distances) / len(joint_distances),
        "joint_max": max(joint_distances),
        "joint_faces": len(joint_distances),
        "signed_volume": volume,
    }


def mat(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.38
    return material


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(path, rigs, flex, splay, twist):
    for rig in rigs:
        pose(rig, flex, splay, twist)
        rig.hide_render = True
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    global COLLECTION
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    COLLECTION = bpy.data.collections.new("MultiAxisCorrectiveSpecimens")
    bpy.context.scene.collection.children.link(COLLECTION)

    dense_rings = [-2.5 + i * (5.0 / 48) for i in range(49)]
    low_rings = [-2.5, -2.38, -2.0, -1.55, -1.15, -0.82, -0.55, -0.34, -0.20, -0.10,
                 0.0, 0.10, 0.20, 0.34, 0.55, 0.78, 1.0, 1.18, 1.38, 1.65, 1.95, 2.28, 2.5]
    dense = build_limb("Dense_Corrected_Reference", dense_rings, 32)
    uncorrected = build_limb("Purposeful_Uncorrected", low_rings, 16)
    corrected = build_limb("Purposeful_DrivenCorrective", low_rings, 16)
    dense_key = add_corrective_shape(dense, dense_rings, 32)
    corrected_key = add_corrective_shape(corrected, low_rings, 16)
    rigs = [
        build_rig("Dense_Reference_Rig", dense, dense_rings, 32, dense_key),
        build_rig("Uncorrected_Rig", uncorrected, low_rings, 16),
        build_rig("Corrected_Rig", corrected, low_rings, 16, corrected_key),
    ]
    for obj, color in zip(
        (dense, uncorrected, corrected),
        ((0.62, 0.68, 0.76), (0.92, 0.24, 0.12), (0.20, 0.72, 0.38)),
    ):
        obj.data.materials.append(mat(obj.name + "Material", color))

    for rig in rigs:
        pose(rig, 72.0, 18.0, 58.0)
    target_verts, target_polys, target_volume = evaluated(dense)
    target_tree = BVHTree.FromPolygons(target_verts, target_polys, all_triangles=False)
    uncorrected_error = surface_error(uncorrected, target_tree)
    corrected_error = surface_error(corrected, target_tree)
    ratio = uncorrected_error["joint_mean"] / corrected_error["joint_mean"]
    volume_error_uncorrected = abs(uncorrected_error["signed_volume"] - target_volume) / abs(target_volume)
    volume_error_corrected = abs(corrected_error["signed_volume"] - target_volume) / abs(target_volume)
    driven_pose_value = corrected.data.shape_keys.key_blocks["CorrectiveFlexTwist"].value
    pose(rigs[2], 72.0, 18.0, 0.0)
    driven_flex_only_value = corrected.data.shape_keys.key_blocks["CorrectiveFlexTwist"].value
    pose(rigs[2], 0.0, 0.0, 58.0)
    driven_twist_only_value = corrected.data.shape_keys.key_blocks["CorrectiveFlexTwist"].value
    for rig in rigs:
        pose(rig, 0.0, 0.0, 0.0)
    driven_rest_value = corrected.data.shape_keys.key_blocks["CorrectiveFlexTwist"].value

    for offset, obj, rig in zip((-4.2, 0.0, 4.2), (dense, uncorrected, corrected), rigs):
        obj.location.x = offset
        rig.location.x = offset
    bpy.ops.object.camera_add(location=(11.5, -16.5, 8.5))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 13.5
    point_at(camera, (0.0, 0.2, 0.45))
    bpy.context.scene.camera = camera
    for location, energy, size, color in [
        ((5.5, -6.5, 9.0), 1450, 4.5, (1.0, 0.91, 0.82)),
        ((-6.0, -3.0, 4.0), 520, 5.0, (0.72, 0.84, 1.0)),
        ((1.0, 5.5, 7.0), 1050, 3.2, (1.0, 0.68, 0.5)),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy, light.data.size, light.data.color = energy, size, color
        point_at(light, (0, 0.2, 0.3))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1500, 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    render(OUT / "multi_axis_rest.png", rigs, 0.0, 0.0, 0.0)
    render(OUT / "multi_axis_pose.png", rigs, 72.0, 18.0, 58.0)

    assertions = {
        "driver_is_zero_at_rest": driven_rest_value < 0.01,
        "driver_activates_at_combined_pose": driven_pose_value > 0.9,
        "driver_rejects_flex_only": driven_flex_only_value < 0.01,
        "driver_rejects_twist_only": driven_twist_only_value < 0.01,
        "corrective_improves_joint_mean": corrected_error["joint_mean"] < uncorrected_error["joint_mean"],
        "corrective_improves_joint_max": corrected_error["joint_max"] < uncorrected_error["joint_max"],
        "meaningful_joint_improvement": ratio > 1.20,
        "corrective_improves_volume_error": volume_error_corrected < volume_error_uncorrected,
        "three_bone_weights_present": all({"Upper", "Lower", "Twist"}.issubset(obj.vertex_groups.keys()) for obj in (dense, uncorrected, corrected)),
    }
    report = {
        "lab": "multi_axis_flex_twist_driven_corrective",
        "blender_version": bpy.app.version_string,
        "pose_degrees": {"lower_flex_x": 72.0, "lower_splay_z": 18.0, "distal_twist_y": 58.0},
        "correction": "relative shape key with elbow/twist-root volume offsets driven by Lower X rotation and Twist Y rotation",
        "modifier_order": ["shape keys", "Subdivision Surface", "Armature"],
        "driver_values": {
            "rest": driven_rest_value,
            "flex_only": driven_flex_only_value,
            "twist_only": driven_twist_only_value,
            "combined_pose": driven_pose_value
        },
        "dense_reference_volume": target_volume,
        "uncorrected": uncorrected_error,
        "corrected": corrected_error,
        "uncorrected_over_corrected_joint_mean_ratio": ratio,
        "relative_volume_errors": {"uncorrected": volume_error_uncorrected, "corrected": volume_error_corrected},
        "assertions": assertions,
        "pass": all(assertions.values()),
        "limitations": [
            "The dense reference and low cage share an authored corrective hypothesis, so this proves transfer/mechanism rather than autonomous anatomical discovery.",
            "This is one stylized limb-like form and one combined pose, not facial expression or full-character production evidence.",
            "Nearest-surface and volume errors do not replace animator or deformation-specialist review."
        ],
    }
    (OUT / "multi_axis_corrective_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "multi_axis_corrective.blend"))
    print("MULTI_AXIS_CORRECTIVE_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("multi-axis corrective assertions failed")


main()
