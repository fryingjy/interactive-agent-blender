"""Controlled breadth lab for nine secondary modeling modifiers."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_secondary-modifiers"


def active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def evaluated(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    try:
        points = [vertex.co.copy() for vertex in mesh.vertices]
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            return {
                "vertices": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces),
                "triangles": sum(len(face.verts) == 3 for face in bm.faces),
                "quads": sum(len(face.verts) == 4 for face in bm.faces),
                "ngons": sum(len(face.verts) > 4 for face in bm.faces),
                "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
                "points": [list(point) for point in points],
            }
        finally:
            bm.free()
    finally:
        eval_obj.to_mesh_clear()


def max_displacement(base, result):
    if len(base) != len(result):
        return None
    return max((Vector(a) - Vector(b)).length for a, b in zip(base, result))


def roughness(points, edges):
    neighbors = [[] for _ in points]
    for a, b in edges:
        neighbors[a].append(b)
        neighbors[b].append(a)
    values = []
    for index, linked in enumerate(neighbors):
        if linked:
            mean = sum((Vector(points[item]) for item in linked), Vector()) / len(linked)
            values.append((Vector(points[index]) - mean).length)
    return sum(values) / len(values)


def strip_transient_points(value):
    if isinstance(value, dict):
        return {key: strip_transient_points(item) for key, item in value.items() if key != "points"}
    if isinstance(value, list):
        return [strip_transient_points(item) for item in value]
    return value


def sphere(name, location, noisy=False):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    if noisy:
        for vertex in obj.data.vertices:
            direction = vertex.co.normalized()
            vertex.co += direction * (0.10 * math.sin(vertex.index * 2.173))
        obj.data.update()
    return obj


def cube(name, location):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    return obj


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    records = {}

    mesh = bpy.data.meshes.new("ScrewProfileMesh")
    mesh.from_pydata([(0.45, 0, -0.3), (0.75, 0, 0.3)], [(0, 1)], [])
    screw_obj = bpy.data.objects.new("Screw_Helix_Profile", mesh)
    bpy.context.scene.collection.objects.link(screw_obj)
    screw_obj.location = (-8, 4, 0)
    screw = screw_obj.modifiers.new("One Turn Screw", "SCREW")
    screw.angle = 2 * math.pi; screw.screw_offset = 1.2; screw.steps = 24; screw.render_steps = 24
    records["screw"] = evaluated(screw_obj)

    remesh_obj = cube("Remesh_RoundedCube", (-4, 4, 0))
    bevel = remesh_obj.modifiers.new("Pre Remesh Bevel", "BEVEL"); bevel.width = .3; bevel.segments = 3
    remesh = remesh_obj.modifiers.new("Voxel-like Remesh", "REMESH")
    remesh.mode = "VOXEL"; remesh.octree_depth = 5; remesh.use_smooth_shade = True
    records["remesh"] = {"base": len(remesh_obj.data.vertices), "evaluated": evaluated(remesh_obj)}

    decimate_obj = sphere("Decimate_SculptLike", (0, 4, 0))
    decimate_base = len(decimate_obj.data.polygons)
    decimate = decimate_obj.modifiers.new("Quarter Triangle Budget", "DECIMATE")
    decimate.decimate_type = "COLLAPSE"; decimate.ratio = .25
    records["decimate"] = {"base_faces": decimate_base, "evaluated": evaluated(decimate_obj)}

    triangulate_obj = cube("Triangulate_Delivery", (4, 4, 0))
    triangulate = triangulate_obj.modifiers.new("Explicit Delivery Triangles", "TRIANGULATE")
    triangulate.quad_method = "BEAUTY"; triangulate.ngon_method = "BEAUTY"
    records["triangulate"] = evaluated(triangulate_obj)

    smooth_obj = sphere("Smooth_Noisy", (-8, 0, 0), noisy=True)
    base_points = [list(vertex.co) for vertex in smooth_obj.data.vertices]
    edges = [list(edge.vertices) for edge in smooth_obj.data.edges]
    smooth = smooth_obj.modifiers.new("Three Relax Passes", "SMOOTH")
    smooth.factor = .5; smooth.iterations = 3
    smooth_eval = evaluated(smooth_obj)
    records["smooth"] = {
        "base_roughness": roughness(base_points, edges),
        "evaluated_roughness": roughness(smooth_eval["points"], edges),
        "maximum_displacement": max_displacement(base_points, smooth_eval["points"]),
        "evaluated": smooth_eval,
    }

    corrective_obj = sphere("CorrectiveSmooth_Noisy", (-4, 0, 0), noisy=True)
    corrective_base = [list(vertex.co) for vertex in corrective_obj.data.vertices]
    corrective = corrective_obj.modifiers.new("Corrective Preview", "CORRECTIVE_SMOOTH")
    corrective.factor = .5; corrective.iterations = 3; corrective.use_only_smooth = True
    corrective_eval = evaluated(corrective_obj)
    records["corrective_smooth"] = {
        "only_smooth": corrective.use_only_smooth,
        "maximum_displacement": max_displacement(corrective_base, corrective_eval["points"]),
        "evaluated": corrective_eval,
    }

    lap_obj = sphere("LaplacianSmooth_Noisy", (0, 0, 0), noisy=True)
    lap_base = [list(vertex.co) for vertex in lap_obj.data.vertices]
    lap_edges = [list(edge.vertices) for edge in lap_obj.data.edges]
    lap = lap_obj.modifiers.new("Volume Preserving Laplacian", "LAPLACIANSMOOTH")
    lap.lambda_factor = .4; lap.iterations = 3; lap.use_volume_preserve = True
    lap_eval = evaluated(lap_obj)
    records["laplacian_smooth"] = {
        "base_roughness": roughness(lap_base, lap_edges),
        "evaluated_roughness": roughness(lap_eval["points"], lap_edges),
        "maximum_displacement": max_displacement(lap_base, lap_eval["points"]),
        "evaluated": lap_eval,
    }

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=17, y_subdivisions=3, size=4, location=(5, 0, 0))
    curve_mesh = bpy.context.object
    curve_mesh.name = "Curve_Deformed_Strip"
    # Grid lies in XY; align its long X axis with the Curve modifier deformation axis.
    bpy.ops.curve.primitive_bezier_curve_add(location=(3, 0, 0))
    guide = bpy.context.object
    guide.name = "Curve_Guide"
    guide.data.dimensions = "3D"
    guide.data.splines[0].bezier_points[0].co = (0, 0, 0)
    guide.data.splines[0].bezier_points[1].co = (4, 0, 2)
    for point in guide.data.splines[0].bezier_points:
        point.handle_left_type = "AUTO"; point.handle_right_type = "AUTO"
    curve = curve_mesh.modifiers.new("Guide Curve", "CURVE")
    curve.object = guide; curve.deform_axis = "POS_X"
    curve_base = [list(vertex.co) for vertex in curve_mesh.data.vertices]
    curve_eval = evaluated(curve_mesh)
    records["curve"] = {"maximum_displacement": max_displacement(curve_base, curve_eval["points"]), "evaluated": curve_eval}

    lattice_obj = cube("Lattice_Deformed_Cube", (9, 0, 0))
    active(lattice_obj)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=3); bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.add(type="LATTICE", location=(9, 0, 0))
    cage = bpy.context.object
    cage.name = "Lattice_Control"
    cage.scale = (1.2, 1.2, 1.2)
    cage.data.points_u = 3; cage.data.points_v = 3; cage.data.points_w = 3
    for point in cage.data.points:
        if point.co_deform.z > 0:
            point.co_deform.x += .35 * (point.co_deform.z + .5)
    lattice = lattice_obj.modifiers.new("Bent by Lattice", "LATTICE"); lattice.object = cage
    lattice_base = [list(vertex.co) for vertex in lattice_obj.data.vertices]
    lattice_eval = evaluated(lattice_obj)
    records["lattice"] = {"maximum_displacement": max_displacement(lattice_base, lattice_eval["points"]), "evaluated": lattice_eval}

    assertions = {
        "screw_generates_helix_surface": records["screw"]["faces"] >= 24,
        "remesh_rebuilds_density": records["remesh"]["evaluated"]["vertices"] > records["remesh"]["base"],
        "decimate_reduces_faces": records["decimate"]["evaluated"]["faces"] < records["decimate"]["base_faces"] * .4,
        "triangulate_converts_cube_to_12_triangles": records["triangulate"]["faces"] == 12 and records["triangulate"]["triangles"] == 12,
        "smooth_reduces_noisy_laplacian": records["smooth"]["evaluated_roughness"] < records["smooth"]["base_roughness"],
        "corrective_only_smooth_moves_vertices": records["corrective_smooth"]["maximum_displacement"] > .001,
        "laplacian_reduces_noisy_laplacian": records["laplacian_smooth"]["evaluated_roughness"] < records["laplacian_smooth"]["base_roughness"],
        "curve_deforms_strip": (records["curve"]["maximum_displacement"] or 0) > .1,
        "lattice_deforms_subdivided_cube": (records["lattice"]["maximum_displacement"] or 0) > .1,
    }
    report = {
        "lab": "secondary_modifier_breadth",
        "blender_version": bpy.app.version_string,
        "official_source_access": {
            "direct_latest_fetch": "FAILED_HTTP_402",
            "search_index_results": "official Blender Manual snippets available; runtime behavior reproduced in Blender 5.2",
        },
        "records": strip_transient_points(records),
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (OUT / "secondary_modifier_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "secondary_modifier_lab.blend"))
    print("SECONDARY_MODIFIER_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("one or more assertions failed")


if __name__ == "__main__":
    main()
