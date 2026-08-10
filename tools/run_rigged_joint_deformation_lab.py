"""Transfer retopology density reasoning to a genuinely armature-driven limb.

Builds three manually authored organic cages (dense reference, purposeful elbow
density, sparse control), applies identical two-bone weights and pose, and measures
evaluated surface deviation.  No mesh primitive operators are used.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_rigged-joint-deformation"
OUT.mkdir(parents=True, exist_ok=True)
SPECIMENS = None


def smoothstep(edge0, edge1, value):
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def radius_at(y):
    upper_bulge = 0.16 * math.exp(-(((y + 1.25) / 0.62) ** 2))
    forearm_bulge = 0.12 * math.exp(-(((y - 0.85) / 0.72) ** 2))
    taper = 0.58 - 0.055 * ((y + 2.4) / 4.6)
    elbow_narrow = 0.10 * math.exp(-((y / 0.32) ** 2))
    return taper + upper_bulge + forearm_bulge - elbow_narrow


def build_limb_mesh(name, rings, radial_segments=16):
    vertices = []
    for y in rings:
        radius = radius_at(y)
        for segment in range(radial_segments):
            angle = 2.0 * math.pi * segment / radial_segments
            vertices.append((radius * math.cos(angle), y, radius * 0.9 * math.sin(angle)))
    bottom_center = len(vertices)
    vertices.append((0.0, rings[0], 0.0))
    top_center = len(vertices)
    vertices.append((0.0, rings[-1], 0.0))
    faces = []
    for ring_index in range(len(rings) - 1):
        for segment in range(radial_segments):
            nxt = (segment + 1) % radial_segments
            a = ring_index * radial_segments + segment
            b = ring_index * radial_segments + nxt
            d = (ring_index + 1) * radial_segments + segment
            c = (ring_index + 1) * radial_segments + nxt
            faces.append((a, d, c, b))
    for segment in range(radial_segments):
        nxt = (segment + 1) % radial_segments
        faces.append((bottom_center, segment, nxt))
        top_a = (len(rings) - 1) * radial_segments + segment
        top_b = (len(rings) - 1) * radial_segments + nxt
        faces.append((top_center, top_b, top_a))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for loop_index, uv_loop in enumerate(uv.data):
        vertex_index = mesh.loops[loop_index].vertex_index
        if vertex_index < len(rings) * radial_segments:
            ring_index, segment = divmod(vertex_index, radial_segments)
            uv_loop.uv = (segment / radial_segments, ring_index / (len(rings) - 1))
        else:
            uv_loop.uv = (0.5, 0.5)
    obj = bpy.data.objects.new(name, mesh)
    SPECIMENS.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def build_rig(name, mesh_obj, rings, radial_segments=16):
    armature_data = bpy.data.armatures.new(name + "Data")
    armature = bpy.data.objects.new(name, armature_data)
    bpy.context.scene.collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    upper = armature_data.edit_bones.new("Upper")
    upper.head = (0.0, -2.55, 0.0)
    upper.tail = (0.0, 0.0, 0.0)
    lower = armature_data.edit_bones.new("Lower")
    lower.head = (0.0, 0.0, 0.0)
    lower.tail = (0.0, 2.4, 0.0)
    lower.parent = upper
    lower.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    armature.select_set(False)

    upper_group = mesh_obj.vertex_groups.new(name="Upper")
    lower_group = mesh_obj.vertex_groups.new(name="Lower")
    for ring_index, y in enumerate(rings):
        lower_weight = smoothstep(-0.42, 0.42, y)
        indices = list(range(ring_index * radial_segments, (ring_index + 1) * radial_segments))
        upper_group.add(indices, 1.0 - lower_weight, "REPLACE")
        lower_group.add(indices, lower_weight, "REPLACE")
    upper_group.add([len(rings) * radial_segments], 1.0, "REPLACE")
    lower_group.add([len(rings) * radial_segments], 0.0, "REPLACE")
    upper_group.add([len(rings) * radial_segments + 1], 0.0, "REPLACE")
    lower_group.add([len(rings) * radial_segments + 1], 1.0, "REPLACE")

    subdivision = mesh_obj.modifiers.new("SurfaceSubdivision", "SUBSURF")
    subdivision.levels = 1
    subdivision.render_levels = 1
    deform = mesh_obj.modifiers.new("ArmatureDeform", "ARMATURE")
    deform.object = armature
    return armature


def set_pose(armature, degrees):
    pose_bone = armature.pose.bones["Lower"]
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler.x = math.radians(degrees)
    bpy.context.view_layer.update()


def evaluated_mesh(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [vertex.co.copy() for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return vertices, polygons


def surface_error(obj, target_tree):
    vertices, polygons = evaluated_mesh(obj)
    distances = []
    joint_distances = []
    for polygon in polygons:
        center = sum((vertices[index] for index in polygon), Vector()) / len(polygon)
        nearest = target_tree.find_nearest(center)
        distance = nearest[3] if nearest else float("inf")
        distances.append(distance)
        if center.length < 1.25:
            joint_distances.append(distance)
    return {
        "mean": sum(distances) / len(distances),
        "max": max(distances),
        "joint_mean": sum(joint_distances) / len(joint_distances),
        "joint_max": max(joint_distances),
        "faces": len(distances),
        "joint_faces": len(joint_distances),
    }


def material(name, color):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1.0)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.38
    return value


def point_at(obj, target=(0.0, 0.0, 0.0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


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


def render(path, meshes, rigs, pose_degrees):
    for rig in rigs:
        set_pose(rig, pose_degrees)
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            obj.hide_render = True
    scene = bpy.context.scene
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    global SPECIMENS
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    SPECIMENS = bpy.data.collections.new("RiggedJointSpecimens")
    bpy.context.scene.collection.children.link(SPECIMENS)

    dense_rings = [-2.4 + index * (4.6 / 46) for index in range(47)]
    adequate_rings = [-2.4, -2.32, -1.9, -1.45, -1.05, -0.72, -0.48, -0.30, -0.16, -0.07,
                      0.0, 0.07, 0.16, 0.30, 0.48, 0.72, 1.05, 1.45, 1.85, 2.12, 2.2]
    sparse_rings = [-2.4, -2.32, -1.75, -1.1, -0.48, 0.0, 0.48, 1.1, 1.65, 2.12, 2.2]
    specs = [
        ("Dense_RiggedReference", dense_rings, (0.62, 0.68, 0.76)),
        ("Purposeful_JointLoops", adequate_rings, (0.34, 0.78, 0.50)),
        ("Sparse_JointFailure", sparse_rings, (0.92, 0.31, 0.20)),
    ]
    meshes, rigs = [], []
    for name, rings, color in specs:
        mesh = build_limb_mesh(name, rings)
        mesh.data.materials.append(material(name + "Material", color))
        rig = build_rig(name + "Rig", mesh, rings)
        meshes.append(mesh)
        rigs.append(rig)

    for rig in rigs:
        set_pose(rig, 82.0)
    target_vertices, target_polygons = evaluated_mesh(meshes[0])
    target_tree = BVHTree.FromPolygons(target_vertices, target_polygons, all_triangles=False)
    adequate_error = surface_error(meshes[1], target_tree)
    sparse_error = surface_error(meshes[2], target_tree)
    ratio = sparse_error["joint_mean"] / adequate_error["joint_mean"]

    offsets = (-4.1, 0.0, 4.1)
    for offset, mesh, rig in zip(offsets, meshes, rigs):
        mesh.location.x = offset
        rig.location.x = offset
    bpy.ops.object.camera_add(location=(10.5, -15.0, 7.5))
    camera = bpy.context.object
    point_at(camera, (0.0, 0.2, 0.5))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 13.0
    bpy.context.scene.camera = camera
    area_light("Key", (5.5, -6.0, 8.0), 1500, 4.0)
    area_light("Fill", (-6.0, -4.0, 3.0), 420, 5.0, (0.72, 0.84, 1.0))
    area_light("Rim", (2.0, 5.0, 6.0), 1100, 3.0, (1.0, 0.72, 0.55))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    render(OUT / "rigged_joint_rest.png", meshes, rigs, 0.0)
    render(OUT / "rigged_joint_pose.png", meshes, rigs, 82.0)

    report = {
        "lab": "real_armature_joint_density_transfer",
        "blender_version": bpy.app.version_string,
        "specimen": "manually authored stylized organic limb with two connected bones and smooth vertex-group weights",
        "pose_degrees": 82.0,
        "modifier_order": ["Subdivision Surface", "Armature"],
        "ring_counts": {"dense_reference": 47, "purposeful": len(adequate_rings), "sparse": len(sparse_rings)},
        "purposeful_error": adequate_error,
        "sparse_error": sparse_error,
        "sparse_over_purposeful_joint_mean_ratio": ratio,
        "assertions": {
            "purposeful_joint_mean_better": adequate_error["joint_mean"] < sparse_error["joint_mean"],
            "purposeful_joint_max_better": adequate_error["joint_max"] < sparse_error["joint_max"],
            "meaningful_improvement": ratio > 1.35,
            "real_armature_modifiers": all(any(mod.type == "ARMATURE" for mod in mesh.modifiers) for mesh in meshes),
            "two_bone_weight_groups": all({"Upper", "Lower"}.issubset(mesh.vertex_groups.keys()) for mesh in meshes),
        },
        "limitations": [
            "This is one stylized elbow-like joint, not a full character or facial rig.",
            "Nearest-surface error measures geometric fidelity to a dense rigged reference, not animation appeal.",
            "Linear blend skinning and one pose do not cover twist, muscle simulation, or corrective shape keys."
        ],
    }
    report["pass"] = all(report["assertions"].values())
    (OUT / "rigged_joint_deformation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "rigged_joint_deformation.blend"))
    print("RIGGED_JOINT_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("rigged joint density transfer failed")


main()
