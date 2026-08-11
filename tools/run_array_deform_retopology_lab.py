"""Controlled Array, Shrinkwrap, Simple Deform, and retopology foundation lab."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def output_directory() -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected one OUTPUT_DIR after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def cube(name, location, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    return obj


def grid(name, location, size=2.4, subdivisions=7):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subdivisions, y_subdivisions=subdivisions, size=size, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj


def sphere(name, location, segments=32, rings=16, radius=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj


def evaluated_metrics(obj, reference_center=None):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            world = evaluated.matrix_world
            points = [world @ vertex.co for vertex in bm.verts]
            base_points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
            displacements = []
            if len(points) == len(base_points):
                displacements = [(a - b).length for a, b in zip(points, base_points)]
            xs = [point.x for point in points]
            ys = [point.y for point in points]
            zs = [point.z for point in points]
            radial = []
            if reference_center is not None:
                center = Vector(reference_center)
                radial = [(point - center).length for point in points]
            return {
                "base": {"vertices": len(obj.data.vertices), "edges": len(obj.data.edges), "faces": len(obj.data.polygons)},
                "evaluated": {
                    "vertices": len(bm.verts),
                    "edges": len(bm.edges),
                    "faces": len(bm.faces),
                    "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                    "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
                    "ngons": sum(len(face.verts) > 4 for face in bm.faces),
                    "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
                    "bounds": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]},
                    "max_base_vertex_displacement": max(displacements, default=None),
                    "mean_base_vertex_displacement": sum(displacements) / len(displacements) if displacements else None,
                    "radial_min": min(radial, default=None),
                    "radial_max": max(radial, default=None),
                    "radial_mean": sum(radial) / len(radial) if radial else None,
                },
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def evaluated_local_points(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [vertex.co.copy() for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def add_array(obj, *, count=3, relative=(1.0, 0.0, 0.0), constant=None, merge=False, threshold=0.001):
    mod = obj.modifiers.new("Array", "ARRAY")
    mod.count = count
    mod.use_relative_offset = relative is not None
    if relative is not None:
        mod.relative_offset_displace = relative
    mod.use_constant_offset = constant is not None
    if constant is not None:
        mod.constant_offset_displace = constant
    mod.use_merge_vertices = merge
    mod.merge_threshold = threshold
    return mod


def add_shrinkwrap(obj, target, *, method="NEAREST_SURFACEPOINT", offset=0.0, negative=True, positive=False):
    mod = obj.modifiers.new("Shrinkwrap", "SHRINKWRAP")
    mod.target = target
    mod.wrap_method = method
    mod.wrap_mode = "ON_SURFACE"
    mod.offset = offset
    if method == "PROJECT":
        mod.use_project_z = True
        mod.use_negative_direction = negative
        mod.use_positive_direction = positive
    return mod


def add_simple_deform(obj, *, method, axis, angle=0.0, factor=0.0):
    mod = obj.modifiers.new("Simple Deform", "SIMPLE_DEFORM")
    mod.deform_method = method
    mod.deform_axis = axis
    # Angle and factor are mode-specific views of the same underlying amount
    # in Blender 5.2. Setting both silently resets the first value.
    if method in {"TWIST", "BEND"}:
        mod.angle = angle
    else:
        mod.factor = factor
    return mod


def record(records, obj, question, settings, reference_center=None):
    entry = {"object": obj.name, "question": question, "settings": settings, **evaluated_metrics(obj, reference_center)}
    records.append(entry)
    return entry


def main():
    output = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    records = []

    array_relative = cube("Array_Relative", (-10, 5, 0), scale=(1.0, 0.6, 0.6))
    add_array(array_relative, relative=(1.0, 0, 0))
    relative = record(records, array_relative, "Does relative offset follow base bounding-box size?", {"count": 3, "relative": [1.0, 0, 0]})

    array_combined = cube("Array_RelativePlusConstant", (-10, 2, 0), scale=(1.0, 0.6, 0.6))
    add_array(array_combined, relative=(1.0, 0, 0), constant=(0.3, 0, 0))
    combined = record(records, array_combined, "Are relative and constant offsets additive?", {"count": 3, "relative": [1, 0, 0], "constant": [0.3, 0, 0]})

    array_scaled = cube("Array_UnappliedScale", (-10, -1, 0), scale=(2.0, 0.6, 0.6))
    add_array(array_scaled, relative=(1.0, 0, 0))
    scaled = record(records, array_scaled, "How does unapplied object scale affect world array span?", {"count": 3, "relative": [1, 0, 0], "object_scale": [2, 0.6, 0.6]})

    centers = [(0, 5, 0), (4, 5, 0), (8, 5, 0)]
    shrink_records = []
    for index, (label, method, offset, negative, positive) in enumerate([
        ("Nearest", "NEAREST_SURFACEPOINT", 0.0, True, False),
        ("NearestOffset", "NEAREST_SURFACEPOINT", 0.2, True, False),
        ("ProjectWrongDirection", "PROJECT", 0.0, False, True),
    ]):
        center = centers[index]
        target = sphere(f"Shrink_Target_{label}", center, radius=1.0)
        source = grid(f"Shrink_{label}", (center[0], center[1], center[2] + 1.6), size=1.4, subdivisions=7)
        add_shrinkwrap(source, target, method=method, offset=offset, negative=negative, positive=positive)
        shrink_records.append(record(records, source, f"Shrinkwrap {label} behavior", {"method": method, "offset": offset, "negative": negative, "positive": positive}, center))

    twist_low = cube("SimpleDeform_Twist_LowDensity", (-6, -5, 0), scale=(0.6, 0.6, 2.0))
    active(twist_low)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    add_simple_deform(twist_low, method="TWIST", axis="Z", angle=math.pi)
    low = record(records, twist_low, "How does Twist behave on a low-density cage?", {"method": "TWIST", "axis": "Z", "angle": math.pi})

    twist_dense = cube("SimpleDeform_Twist_Subdivided", (-2, -5, 0), scale=(0.6, 0.6, 2.0))
    active(twist_dense)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    subdiv = twist_dense.modifiers.new("Pre-Deform Subdivision", "SUBSURF")
    subdiv.subdivision_type = "SIMPLE"
    subdiv.levels = 3
    dense_control = twist_dense.copy()
    dense_control.data = twist_dense.data.copy()
    dense_control.name = "SimpleDeform_Twist_Subdivided_CONTROL"
    bpy.context.scene.collection.objects.link(dense_control)
    add_simple_deform(twist_dense, method="TWIST", axis="Z", angle=math.pi)
    dense = record(records, twist_dense, "Does pre-deform resolution provide intermediate twist samples?", {"pre_subdivision": 3, "method": "TWIST", "axis": "Z", "angle": math.pi})
    dense_points = evaluated_local_points(twist_dense)
    control_points = evaluated_local_points(dense_control)
    dense["deform_vs_subdivision_control"] = {
        "correspondence_valid": len(dense_points) == len(control_points),
        "maximum_vertex_displacement": max(
            ((deformed - control).length for deformed, control in zip(dense_points, control_points)),
            default=0.0,
        ),
        "mean_vertex_displacement": (
            sum((deformed - control).length for deformed, control in zip(dense_points, control_points)) / len(dense_points)
            if dense_points and len(dense_points) == len(control_points) else None
        ),
    }

    bend_noop = grid("SimpleDeform_Bend_X_Noop", (3, -5, 0), size=3.0, subdivisions=9)
    add_simple_deform(bend_noop, method="BEND", axis="X", angle=math.pi / 2)
    noop = record(records, bend_noop, "Can an unsuitable local-axis plane make Bend a no-op?", {"method": "BEND", "axis": "X", "angle": math.pi / 2})

    center = (8, -4, 0)
    high = sphere("Retopo_HighDensity_Target", center, segments=64, rings=32, radius=1.0)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.25, location=center)
    low_retopo = bpy.context.object
    low_retopo.name = "Retopo_LowDensity_Shrinkwrapped"
    add_shrinkwrap(low_retopo, high, method="NEAREST_SURFACEPOINT")
    retopo = record(records, low_retopo, "Can a low-density cage conform while preserving a far lower vertex count?", {"workflow": "low-density icosphere -> Shrinkwrap high-density sphere"}, center)

    assertions = {
        "array_count_triples_cube_topology": relative["evaluated"]["vertices"] == 24,
        "relative_and_constant_offsets_are_additive": combined["evaluated"]["bounds"]["x"][1] > relative["evaluated"]["bounds"]["x"][1],
        "unapplied_scale_expands_world_array_span": (scaled["evaluated"]["bounds"]["x"][1] - scaled["evaluated"]["bounds"]["x"][0]) > (relative["evaluated"]["bounds"]["x"][1] - relative["evaluated"]["bounds"]["x"][0]),
        "nearest_shrinkwrap_reaches_target_surface": abs(shrink_records[0]["evaluated"]["radial_mean"] - 1.0) < 0.02,
        "shrinkwrap_offset_changes_radius": shrink_records[1]["evaluated"]["radial_mean"] > shrink_records[0]["evaluated"]["radial_mean"] + 0.15,
        "wrong_project_direction_is_noop": (shrink_records[2]["evaluated"]["max_base_vertex_displacement"] or 0.0) < 1e-6,
        "pre_deform_subdivision_adds_samples": dense["evaluated"]["vertices"] > low["evaluated"]["vertices"],
        "subdivided_twist_changes_intermediate_vertices": dense["deform_vs_subdivision_control"]["maximum_vertex_displacement"] > 0.1,
        "unsuitable_bend_axis_is_noop": (noop["evaluated"]["max_base_vertex_displacement"] or 0.0) < 1e-6,
        "retopo_cage_is_much_lower_density": retopo["evaluated"]["vertices"] * 10 < len(high.data.vertices),
        "retopo_cage_conforms_to_target": abs(retopo["evaluated"]["radial_mean"] - 1.0) < 0.02,
    }
    report = {
        "lab": "array_shrinkwrap_simple_deform_retopology",
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode("utf-8"),
        "records": records,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (output / "array_deform_retopology_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "array_deform_retopology_lab.blend"))
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("one or more assertions failed")


if __name__ == "__main__":
    main()
