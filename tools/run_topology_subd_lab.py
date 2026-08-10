"""Create and measure topology-context and Subdivision Surface specimens."""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def output_directory():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected one OUTPUT_DIR after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def mesh_object(name, vertices, faces, location):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def add_subd(obj, levels=2):
    mod = obj.modifiers.new("Subdivision Surface", "SUBSURF")
    mod.subdivision_type = "CATMULL_CLARK"
    mod.levels = levels
    mod.render_levels = levels


def pole_fan(name, valence, location):
    vertices = [(0, 0, 0)] + [
        (math.cos(2 * math.pi * index / valence), math.sin(2 * math.pi * index / valence), 0)
        for index in range(valence)
    ]
    faces = [(0, 1 + index, 1 + ((index + 1) % valence)) for index in range(valence)]
    return mesh_object(name, vertices, faces, location)


def grid_patch(name, location, *, curved=False, triangulate_center=False, x_values=None):
    xs = x_values or [-1.0, 0.0, 1.0]
    ys = [-1.0, 0.0, 1.0]
    vertices = []
    for y in ys:
        for x in xs:
            z = 0.25 * (x * x + y * y) if curved else 0.0
            vertices.append((x, y, z))
    width = len(xs)
    faces = []
    for row in range(2):
        for column in range(width - 1):
            a = row * width + column
            quad = (a, a + 1, a + 1 + width, a + width)
            if triangulate_center and row == 0 and column == 0:
                faces.extend([(quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])])
            else:
                faces.append(quad)
    return mesh_object(name, vertices, faces, location)


def ngon_patch(name, location, *, curved=False, sides=6):
    vertices = []
    for index in range(sides):
        angle = 2 * math.pi * index / sides
        z = 0.3 * math.sin(angle * 2) if curved else 0.0
        vertices.append((math.cos(angle), math.sin(angle), z))
    return mesh_object(name, vertices, [tuple(range(sides))], location)


def support_cube(name, location, width):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    bevel = obj.modifiers.new("Support Loops via Bevel", "BEVEL")
    bevel.width = width
    bevel.segments = 1
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(30)
    add_subd(obj, 2)
    return obj


def cylinder_routing(name, location, segments=16):
    vertices = []
    levels = [-1.0, 0.0, 1.0]
    for z in levels:
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            vertices.append((math.cos(angle), math.sin(angle), z))
    faces = []
    for row in range(len(levels) - 1):
        for index in range(segments):
            a = row * segments + index
            b = row * segments + (index + 1) % segments
            c = (row + 1) * segments + (index + 1) % segments
            d = (row + 1) * segments + index
            faces.append((a, b, c, d))
    return mesh_object(name, vertices, faces, location)


def base_metrics(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        valences = [len(vertex.link_edges) for vertex in bm.verts]
        distribution = {str(value): valences.count(value) for value in sorted(set(valences))}
        max_nonplanarity = 0.0
        for face in bm.faces:
            if len(face.verts) <= 3:
                continue
            origin = face.verts[0].co
            normal = face.normal.normalized()
            max_nonplanarity = max(max_nonplanarity, *(abs((vertex.co - origin).dot(normal)) for vertex in face.verts))
        edge_lengths = [edge.calc_length() for edge in bm.edges]
        return {
            "vertices": len(bm.verts),
            "edges": len(bm.edges),
            "faces": len(bm.faces),
            "triangles": sum(len(face.verts) == 3 for face in bm.faces),
            "quads": sum(len(face.verts) == 4 for face in bm.faces),
            "ngons": sum(len(face.verts) > 4 for face in bm.faces),
            "valence_distribution": distribution,
            "maximum_face_nonplanarity": max_nonplanarity,
            "edge_length_ratio": max(edge_lengths) / min(edge_lengths) if edge_lengths and min(edge_lengths) > 0 else None,
        }
    finally:
        bm.free()


def evaluated_metrics(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            areas = [face.calc_area() for face in bm.faces if face.calc_area() > 1e-12]
            angles = [edge.calc_face_angle(0.0) for edge in bm.edges if len(edge.link_faces) == 2]
            coords = [vertex.co for vertex in bm.verts]
            base_coords = [vertex.co for vertex in obj.data.vertices]
            base_dims = [max(v[i] for v in base_coords) - min(v[i] for v in base_coords) for i in range(3)]
            eval_dims = [max(v[i] for v in coords) - min(v[i] for v in coords) for i in range(3)]
            return {
                "vertices": len(bm.verts),
                "edges": len(bm.edges),
                "faces": len(bm.faces),
                "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
                "area_coefficient_of_variation": statistics.pstdev(areas) / statistics.mean(areas) if len(areas) > 1 else 0.0,
                "maximum_adjacent_face_angle_degrees": math.degrees(max(angles, default=0.0)),
                "z_range": [min(v.z for v in coords), max(v.z for v in coords)],
                "shrinkage_ratio_xyz": [eval_dims[i] / base_dims[i] if base_dims[i] > 1e-9 else None for i in range(3)],
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def add_record(records, obj, category, question, add_subdivision=True):
    if add_subdivision:
        add_subd(obj, 2)
    entry = {"object": obj.name, "category": category, "question": question, "base": base_metrics(obj), "evaluated": evaluated_metrics(obj)}
    records.append(entry)
    return entry


def main():
    output = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    records = []
    by_name = {}

    for index, valence in enumerate((3, 5, 6)):
        obj = pole_fan(f"Pole_{valence}_Flat", valence, (-9 + index * 3, 5, 0))
        by_name[obj.name] = add_record(records, obj, "pole", f"How does a valence-{valence} pole behave on a flat open surface?")

    for index, curved in enumerate((False, True)):
        label = "Curved" if curved else "Flat"
        obj = grid_patch(f"Triangle_{label}_Surface", (-8 + index * 4, 1, 0), curved=curved, triangulate_center=True)
        by_name[obj.name] = add_record(records, obj, "triangle_context", f"How does one triangulated quad behave on a {label.lower()} SubD patch?")

    for index, curved in enumerate((False, True)):
        label = "Curved" if curved else "Flat"
        obj = ngon_patch(f"Ngon_{label}_Surface", (0 + index * 4, 1, 0), curved=curved)
        by_name[obj.name] = add_record(records, obj, "ngon_context", f"How does a six-sided n-gon behave when {label.lower()}?")

    uniform = grid_patch("Spacing_Uniform", (-8, -3, 0), x_values=[-1.0, -0.333, 0.333, 1.0])
    by_name[uniform.name] = add_record(records, uniform, "edge_spacing", "What surface-density signal does uniform spacing produce?")
    uneven = grid_patch("Spacing_Uneven", (-4, -3, 0), x_values=[-1.0, -0.9, 0.7, 1.0])
    by_name[uneven.name] = add_record(records, uneven, "edge_spacing", "What surface-density signal does uneven spacing produce?")

    tight = support_cube("Support_Tight", (1, -3, 0), 0.1)
    by_name[tight.name] = add_record(records, tight, "support_loops", "How much silhouette does a tight support width retain?", add_subdivision=False)
    wide = support_cube("Support_Wide", (5, -3, 0), 0.4)
    by_name[wide.name] = add_record(records, wide, "support_loops", "How does a wide support width broaden the transition?", add_subdivision=False)

    cylinder = cylinder_routing("Cylindrical_Quad_Routing", (9, -3, 0))
    by_name[cylinder.name] = add_record(records, cylinder, "cylindrical_routing", "Do matched circumferential loops preserve an all-quad cylindrical side?")

    termination = pole_fan("Loop_Termination_Valence5", 5, (9, 2, 0))
    by_name[termination.name] = add_record(records, termination, "loop_termination", "Can a loop terminate through an explicit valence-5 pole on a flat region?")

    assertions = {
        "pole_valences_are_exact": all(by_name[f"Pole_{value}_Flat"]["base"]["valence_distribution"].get(str(value), 0) >= 1 for value in (3, 5, 6)),
        "flat_triangle_patch_stays_planar": max(abs(v) for v in by_name["Triangle_Flat_Surface"]["evaluated"]["z_range"]) < 1e-8,
        "curved_triangle_patch_has_normal_change": by_name["Triangle_Curved_Surface"]["evaluated"]["maximum_adjacent_face_angle_degrees"] > 1.0,
        "flat_ngon_is_planar": by_name["Ngon_Flat_Surface"]["base"]["maximum_face_nonplanarity"] < 1e-8,
        "curved_ngon_is_nonplanar": by_name["Ngon_Curved_Surface"]["base"]["maximum_face_nonplanarity"] > 0.1,
        "uneven_spacing_increases_area_variation": by_name["Spacing_Uneven"]["evaluated"]["area_coefficient_of_variation"] > by_name["Spacing_Uniform"]["evaluated"]["area_coefficient_of_variation"],
        "tight_support_retains_more_silhouette": by_name["Support_Tight"]["evaluated"]["shrinkage_ratio_xyz"][0] > by_name["Support_Wide"]["evaluated"]["shrinkage_ratio_xyz"][0],
        "cylinder_side_is_all_quads": by_name["Cylindrical_Quad_Routing"]["base"]["quads"] == by_name["Cylindrical_Quad_Routing"]["base"]["faces"],
        "loop_termination_contains_valence5": by_name["Loop_Termination_Valence5"]["base"]["valence_distribution"].get("5", 0) >= 1,
    }
    report = {
        "lab": "topology_context_and_subdivision_surface",
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode("utf-8"),
        "records": records,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "interpretation_boundary": "These metrics expose context and surface behavior; they do not classify every pole, triangle, or n-gon as universally good or bad.",
    }
    (output / "topology_subd_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "topology_subd_lab.blend"))
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("one or more topology/SubD assertions failed")


if __name__ == "__main__":
    main()
