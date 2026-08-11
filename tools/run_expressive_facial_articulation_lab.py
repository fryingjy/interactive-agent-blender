"""Build and measure a visibly integrated facial-expression articulation study.

The official CC0 animation head supplies anatomy and topology. This experiment
authors only deformation, controls, staging, and evidence. It intentionally
retains a mouth-only smile as a disconnected-expression failure control.

Run:
    blender human_base_meshes_bundle.blend --background --python this_file.py -- OUTPUT_DIR
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector


SOURCE_HEAD = "GEO-head_animation_realistic"
SOURCE_EYES = (
    "GEO-head_animation_realistic.sclera.L",
    "GEO-head_animation_realistic.sclera.R",
    "GEO-head_animation_realistic.iris.L",
    "GEO-head_animation_realistic.iris.R",
)


def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def gaussian(value, center, sigma):
    return math.exp(-((value - center) / sigma) ** 2)


def output_directory():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(values) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    path = Path(values[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def centered_mesh(source):
    mesh = source.data.copy()
    mesh.transform(source.matrix_world)
    mins = [min(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3)]
    maxs = [max(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3)]
    center = Vector(tuple((mins[axis] + maxs[axis]) * 0.5 for axis in range(3)))
    mesh.transform(Matrix.Translation(-center))
    bounds = {
        "min": [min(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3)],
        "max": [max(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3)],
    }
    return mesh, center, bounds


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
        "cheek_z": mins[2] + height * 0.49,
        "eye_z": mins[2] + height * 0.62,
        "brow_z": mins[2] + height * 0.70,
        "chin_z": mins[2] + height * 0.22,
        "jaw_hinge_z": mins[2] + height * 0.43,
    }


def front_weight(co, frame):
    return 1.0 - smoothstep(
        frame["front_y"] + frame["depth"] * 0.24,
        frame["front_y"] + frame["depth"] * 0.72,
        co.y,
    )


def bilateral_weight(co, frame, x_center, z_center, x_sigma, z_sigma):
    return (
        gaussian(abs(co.x), frame["width"] * x_center, frame["width"] * x_sigma)
        * gaussian(co.z, z_center, frame["height"] * z_sigma)
        * front_weight(co, frame)
    )


def mouth_corner_weight(co, frame):
    return bilateral_weight(co, frame, 0.17, frame["mouth_z"], 0.075, 0.050)


def mouth_center_weight(co, frame, z_offset=0.0, z_sigma=0.035):
    return (
        gaussian(co.x, 0.0, frame["width"] * 0.18)
        * gaussian(co.z, frame["mouth_z"] + frame["height"] * z_offset, frame["height"] * z_sigma)
        * front_weight(co, frame)
    )


def cheek_weight(co, frame):
    return bilateral_weight(co, frame, 0.225, frame["cheek_z"], 0.10, 0.09)


def lower_lid_weight(co, frame):
    return bilateral_weight(co, frame, 0.18, frame["eye_z"] - frame["height"] * 0.010, 0.075, 0.035)


def brow_weight(co, frame):
    return bilateral_weight(co, frame, 0.20, frame["brow_z"], 0.10, 0.055)


def create_head(name, base_mesh, collection):
    mesh = base_mesh.copy()
    mesh.name = name + "Mesh"
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    for face in mesh.polygons:
        face.use_smooth = True
    return obj


def add_expression_shapes(obj, frame, integrated):
    basis = obj.shape_key_add(name="Basis")
    smile = obj.shape_key_add(name="SmileIntegrated" if integrated else "SmileMouthOnly")
    for index, vertex in enumerate(obj.data.vertices):
        co = vertex.co
        corner = mouth_corner_weight(co, frame)
        sign = -1.0 if co.x < 0 else 1.0
        smile.data[index].co.x += sign * frame["width"] * 0.075 * corner
        smile.data[index].co.z += frame["height"] * 0.045 * corner
        smile.data[index].co.y -= frame["depth"] * 0.020 * corner
        upper_lip = mouth_center_weight(co, frame, 0.008, 0.030)
        smile.data[index].co.z += frame["height"] * 0.010 * upper_lip
        smile.data[index].co.y -= frame["depth"] * 0.008 * upper_lip
        if integrated:
            cheek = cheek_weight(co, frame)
            lid = lower_lid_weight(co, frame)
            brow = brow_weight(co, frame)
            smile.data[index].co.z += frame["height"] * 0.027 * cheek
            smile.data[index].co.y -= frame["depth"] * 0.018 * cheek
            smile.data[index].co.z += frame["height"] * 0.011 * lid
            smile.data[index].co.y -= frame["depth"] * 0.006 * lid
            smile.data[index].co.z += frame["height"] * (0.007 + 0.004 * abs(co.x) / (frame["width"] * 0.5)) * brow

    affected = [
        index for index in range(len(obj.data.vertices))
        if (smile.data[index].co - basis.data[index].co).length > 1e-7
    ]
    return basis, smile, affected


def driver_variable(driver, name, rig, bone, transform):
    variable = driver.variables.new()
    variable.name = name
    variable.type = "TRANSFORMS"
    target = variable.targets[0]
    target.id = rig
    target.bone_target = bone
    target.transform_type = transform
    target.transform_space = "LOCAL_SPACE"


def build_rig(name, obj, frame, smile_key, affected_indices):
    armature = bpy.data.armatures.new(name + "Data")
    rig = bpy.data.objects.new(name, armature)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root = armature.edit_bones.new("HeadRoot")
    root.head = (0, frame["depth"] * 0.20, -frame["height"] * 0.42)
    root.tail = (0, frame["depth"] * 0.20, frame["height"] * 0.35)
    for side, sign in (("L", -1.0), ("R", 1.0)):
        control = armature.edit_bones.new("Smile." + side)
        control.head = (sign * frame["width"] * 0.20, frame["front_y"] * 1.05, frame["mouth_z"])
        control.tail = control.head + Vector((0, 0, frame["height"] * 0.08))
        control.parent = root
        control.use_deform = False
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)

    expression_region = obj.vertex_groups.new(name="ExpressionShapeRegion")
    expression_region.add(affected_indices, 1.0, "REPLACE")

    curve = smile_key.driver_add("value")
    curve.driver.type = "SCRIPTED"
    driver_variable(curve.driver, "left", rig, "Smile.L", "LOC_X")
    driver_variable(curve.driver, "right", rig, "Smile.R", "LOC_X")
    curve.driver.expression = f"min(1,(abs(left)+abs(right))/{frame['width'] * 0.18:.9f})"
    return rig


def set_pose(rig, frame, smile):
    rig.pose.bones["Smile.L"].location.x = -frame["width"] * 0.09 * smile
    rig.pose.bones["Smile.R"].location.x = frame["width"] * 0.09 * smile
    bpy.context.view_layer.update()


def selected_landmarks(obj, frame):
    regions = {
        "corner_left": lambda co: mouth_corner_weight(co, frame) if co.x < 0 else 0.0,
        "corner_right": lambda co: mouth_corner_weight(co, frame) if co.x > 0 else 0.0,
        "cheek_left": lambda co: cheek_weight(co, frame) if co.x < 0 else 0.0,
        "cheek_right": lambda co: cheek_weight(co, frame) if co.x > 0 else 0.0,
        "lid_left": lambda co: lower_lid_weight(co, frame) if co.x < 0 else 0.0,
        "lid_right": lambda co: lower_lid_weight(co, frame) if co.x > 0 else 0.0,
        "brow_left": lambda co: brow_weight(co, frame) if co.x < 0 else 0.0,
        "brow_right": lambda co: brow_weight(co, frame) if co.x > 0 else 0.0,
    }
    return {
        name: max(obj.data.vertices, key=lambda vertex: function(vertex.co)).index
        for name, function in regions.items()
    }


def shape_landmark_deltas(obj, key_name, landmarks):
    basis = obj.data.shape_keys.key_blocks["Basis"]
    key = obj.data.shape_keys.key_blocks[key_name]
    return {
        name: list(key.data[index].co - basis.data[index].co)
        for name, index in landmarks.items()
    }


def weighted_displacement(obj, key_name, frame, weight_function):
    basis = obj.data.shape_keys.key_blocks["Basis"]
    key = obj.data.shape_keys.key_blocks[key_name]
    weighted, total = 0.0, 0.0
    for index, vertex in enumerate(obj.data.vertices):
        weight = weight_function(vertex.co, frame)
        weighted += (key.data[index].co - basis.data[index].co).length * weight
        total += weight
    return weighted / max(total, 1e-12)


def topology_stats(obj, expression_indices):
    expression_set = set(expression_indices)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    expression_faces = [
        face for face in bm.faces if any(vertex.index in expression_set for vertex in face.verts)
    ]
    expression_quads = sum(len(face.verts) == 4 for face in expression_faces)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "expression_vertices": len(expression_set),
        "expression_faces": len(expression_faces),
        "expression_quads": expression_quads,
        "expression_nonquads": len(expression_faces) - expression_quads,
        "expression_quad_ratio": expression_quads / max(len(expression_faces), 1),
    }
    bm.free()
    return result


def material(name, color, roughness=0.48, metallic=0.0):
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return value


def copy_eye_set(source_center, collection, parent, suffix, materials):
    result = []
    for name in SOURCE_EYES:
        source = bpy.data.objects.get(name)
        if source is None:
            continue
        mesh = source.data.copy()
        mesh.transform(source.matrix_world)
        mesh.transform(Matrix.Translation(-source_center))
        eye = bpy.data.objects.new(name + suffix, mesh)
        collection.objects.link(eye)
        eye.parent = parent
        eye.matrix_parent_inverse = parent.matrix_world.inverted()
        eye.data.materials.clear()
        eye.data.materials.append(materials["iris"] if ".iris." in name else materials["sclera"])
        result.append(eye)
    return result


def point_at(obj, target=(0, 0, 0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, path, visible_heads, all_heads, all_eyes, camera_target, frame, three_quarter=False, wire=False):
    for head in all_heads:
        head.hide_render = head not in visible_heads
        head.show_wire = wire and head in visible_heads
        head.show_all_edges = wire and head in visible_heads
    visible_rigs = {head.parent for head in visible_heads}
    for eye in all_eyes:
        eye.hide_render = wire or eye.parent not in visible_rigs
    camera = scene.camera
    camera.location = (
        camera_target[0] + (frame["width"] * 3.0 if three_quarter else 0.0),
        frame["front_y"] - frame["depth"] * 7.0,
        frame["height"] * 0.04,
    )
    point_at(camera, camera_target)
    camera.data.ortho_scale = frame["height"] * (1.28 if len(visible_heads) == 1 else 1.55)
    temporary_wire = []
    wire_material = None
    if wire:
        wire_material = material("Technical Wire", (0.16, 0.52, 0.72), 0.32, 0.15)
        for head in visible_heads:
            head.data.materials.append(wire_material)
            modifier = head.modifiers.new("Technical_Render_Wire", "WIREFRAME")
            modifier.thickness = frame["width"] * 0.0018
            modifier.use_even_offset = True
            modifier.use_replace = True
            modifier.material_offset = len(head.data.materials) - 1
            temporary_wire.append((head, modifier))
    scene.render.filepath = str(path)
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        for head, modifier in temporary_wire:
            head.modifiers.remove(modifier)
            head.data.materials.pop(index=len(head.data.materials) - 1)
        if wire_material:
            bpy.data.materials.remove(wire_material)


def main():
    output = output_directory()
    source_path = bpy.data.filepath
    source = bpy.data.objects.get(SOURCE_HEAD)
    if source is None:
        raise SystemExit(f"source bundle lacks {SOURCE_HEAD}")
    base_mesh, source_center, bounds = centered_mesh(source)
    frame = feature_frame(bounds)

    scene = bpy.data.scenes.new("ExpressiveFacialArticulationScene")
    bpy.context.window.scene = scene
    collection = bpy.data.collections.new("ExpressiveFacialArticulation")
    scene.collection.children.link(collection)
    baseline = create_head("Failure_MouthOnly_Smile", base_mesh, collection)
    integrated = create_head("Integrated_Duchenne_Smile", base_mesh, collection)
    _, baseline_smile, baseline_region = add_expression_shapes(baseline, frame, integrated=False)
    _, integrated_smile, integrated_region = add_expression_shapes(integrated, frame, integrated=True)
    baseline_rig = build_rig("Failure_Face_Rig", baseline, frame, baseline_smile, baseline_region)
    integrated_rig = build_rig("Integrated_Face_Rig", integrated, frame, integrated_smile, integrated_region)

    baseline.parent = baseline_rig
    baseline.matrix_parent_inverse = baseline_rig.matrix_world.inverted()
    integrated.parent = integrated_rig
    integrated.matrix_parent_inverse = integrated_rig.matrix_world.inverted()
    spacing = frame["width"] * 0.78
    baseline_rig.location.x = -spacing
    integrated_rig.location.x = spacing

    skin_failure = material("Failure Skin", (0.54, 0.18, 0.14), 0.52)
    skin_integrated = material("Integrated Skin", (0.56, 0.31, 0.20), 0.52)
    eye_materials = {
        "sclera": material("Sclera", (0.82, 0.86, 0.88), 0.28),
        "iris": material("Iris", (0.035, 0.11, 0.16), 0.24),
    }
    baseline.data.materials.append(skin_failure)
    integrated.data.materials.append(skin_integrated)
    all_eyes = []
    all_eyes.extend(copy_eye_set(source_center, collection, baseline_rig, ".Failure", eye_materials))
    all_eyes.extend(copy_eye_set(source_center, collection, integrated_rig, ".Integrated", eye_materials))

    landmarks = selected_landmarks(integrated, frame)
    baseline_deltas = shape_landmark_deltas(baseline, "SmileMouthOnly", landmarks)
    integrated_deltas = shape_landmark_deltas(integrated, "SmileIntegrated", landmarks)
    baseline_coupling = {
        "mouth": weighted_displacement(baseline, "SmileMouthOnly", frame, mouth_corner_weight),
        "cheek": weighted_displacement(baseline, "SmileMouthOnly", frame, cheek_weight),
        "lower_lid": weighted_displacement(baseline, "SmileMouthOnly", frame, lower_lid_weight),
        "brow": weighted_displacement(baseline, "SmileMouthOnly", frame, brow_weight),
    }
    integrated_coupling = {
        "mouth": weighted_displacement(integrated, "SmileIntegrated", frame, mouth_corner_weight),
        "cheek": weighted_displacement(integrated, "SmileIntegrated", frame, cheek_weight),
        "lower_lid": weighted_displacement(integrated, "SmileIntegrated", frame, lower_lid_weight),
        "brow": weighted_displacement(integrated, "SmileIntegrated", frame, brow_weight),
    }

    set_pose(integrated_rig, frame, 0.0)
    rest_driver = integrated.data.shape_keys.key_blocks["SmileIntegrated"].value
    set_pose(integrated_rig, frame, 1.0)
    smile_only_driver = integrated.data.shape_keys.key_blocks["SmileIntegrated"].value
    topology = topology_stats(integrated, integrated_region)

    for obj in (baseline, integrated):
        subd = obj.modifiers.new("Review_Subdivision", "SUBSURF")
        subd.levels = 1
        subd.render_levels = 2

    camera_data = bpy.data.cameras.new("FacialReviewCameraData")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("FacialReviewCamera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    for name, location, energy, size, color in (
        ("Key", (-0.45, -0.75, 0.55), 85, 0.38, (1.0, 0.78, 0.64)),
        ("Fill", (0.55, -0.55, 0.18), 36, 0.55, (0.58, 0.76, 1.0)),
        ("Rim", (0.2, 0.45, 0.55), 70, 0.35, (1.0, 0.48, 0.30)),
    ):
        data = bpy.data.lights.new(name + "Data", "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        point_at(light)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1200, 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("FacialReviewWorld")
    scene.world.color = (0.004, 0.006, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"

    all_heads = [baseline, integrated]
    set_pose(baseline_rig, frame, 0.0)
    set_pose(integrated_rig, frame, 0.0)
    render(scene, output / "expression_rest.png", [integrated], all_heads, all_eyes, (spacing, 0, 0), frame)
    set_pose(baseline_rig, frame, 1.0)
    set_pose(integrated_rig, frame, 1.0)
    render(scene, output / "expression_failure_mouth_only.png", [baseline], all_heads, all_eyes, (-spacing, 0, 0), frame)
    render(scene, output / "expression_integrated.png", [integrated], all_heads, all_eyes, (spacing, 0, 0), frame)
    render(scene, output / "expression_comparison.png", all_heads, all_heads, all_eyes, (0, 0, 0), frame)
    render(scene, output / "expression_integrated_three_quarter.png", [integrated], all_heads, all_eyes, (spacing, 0, 0), frame, three_quarter=True)
    render(scene, output / "expression_integrated_wireframe.png", [integrated], all_heads, all_eyes, (spacing, 0, 0), frame, three_quarter=True, wire=True)
    assertions = {
        "source_copy_closed": topology["non_manifold_edges"] == 0,
        "source_copy_nondegenerate": topology["degenerate_faces"] == 0,
        "expression_region_is_over_99_percent_quads": topology["expression_quad_ratio"] > 0.99,
        "mouth_only_failure_lacks_eye_coupling": baseline_coupling["lower_lid"] < frame["height"] * 0.004,
        "integrated_cheek_coupling_exceeds_failure": integrated_coupling["cheek"] > baseline_coupling["cheek"] * 1.35,
        "integrated_lid_coupling_exceeds_failure": integrated_coupling["lower_lid"] > baseline_coupling["lower_lid"] * 1.35,
        "integrated_brow_coupling_exceeds_failure": integrated_coupling["brow"] > baseline_coupling["brow"] * 1.20,
        "mouth_corners_raise_and_widen": all(
            abs(integrated_deltas[name][0]) > frame["width"] * 0.020
            and integrated_deltas[name][2] > frame["height"] * 0.015
            for name in ("corner_left", "corner_right")
        ),
        "cheeks_raise": all(integrated_deltas[name][2] > frame["height"] * 0.008 for name in ("cheek_left", "cheek_right")),
        "lower_lids_raise": all(integrated_deltas[name][2] > frame["height"] * 0.003 for name in ("lid_left", "lid_right")),
        "smile_driver_gates_rest_and_pose": rest_driver < 0.01 and smile_only_driver > 0.9,
        "six_visual_checkpoints_written": all((output / name).stat().st_size > 1000 for name in (
            "expression_rest.png", "expression_failure_mouth_only.png", "expression_integrated.png",
            "expression_comparison.png", "expression_integrated_three_quarter.png", "expression_integrated_wireframe.png",
        )),
    }
    report = {
        "lab": "integrated_expressive_facial_articulation",
        "blender_version": bpy.app.version_string,
        "source_blend": source_path,
        "source_object": SOURCE_HEAD,
        "source_boundary": "official CC0 anatomy/topology; deformation and test authored here",
        "feature_frame": frame,
        "expression": {"bilateral_smile_control": 1.0},
        "landmark_indices": landmarks,
        "failure_mouth_only_landmark_deltas": baseline_deltas,
        "integrated_landmark_deltas": integrated_deltas,
        "failure_coupling": baseline_coupling,
        "integrated_coupling": integrated_coupling,
        "driver_values": {
            "smile_rest": rest_driver,
            "smile_only": smile_only_driver,
        },
        "topology": topology,
        "visual_checkpoints": [
            "expression_rest.png", "expression_failure_mouth_only.png", "expression_integrated.png",
            "expression_comparison.png", "expression_integrated_three_quarter.png", "expression_integrated_wireframe.png",
        ],
        "assertions": assertions,
        "pass": all(assertions.values()),
        "limitations": [
            "The official CC0 head supplies anatomy and topology; this is expression-articulation transfer, not autonomous head retopology.",
            "The action-unit-like landmark thresholds are declared geometric heuristics, not clinical FACS coding or animator approval.",
            "One broad smile does not establish a production facial pose library, speech shapes, asymmetry, or emotional acting range.",
            "Two jaw-opening strategies were rejected after visual review and are retained in the failed evidence directories; this run does not claim jaw-opening quality.",
            "Eye and iris meshes are source accessories copied only to make eyelid behavior readable in controlled renders.",
        ],
    }
    (output / "expressive_facial_articulation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "expressive_facial_articulation.blend"))
    print("EXPRESSIVE_FACIAL_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


main()
