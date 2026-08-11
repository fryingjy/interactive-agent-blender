"""Second-shape transfer lab for Solidify on a curved open shell.

Compares Simple, Even Thickness, and Complex modes on the same quarter-cylinder
panel, plus an unapplied non-uniform-scale variant. Measures actual world-space
wall distance from each source vertex to the nearest generated shell vertex.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix


REQUESTED_THICKNESS = 0.2


def output_directory() -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected exactly one OUTPUT_DIR argument after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def curved_panel(name: str, location, *, applied_scale: bool, object_scale=(1.5, 0.75, 1.0)):
    angles = [math.radians(value) for value in (-75, -50, -25, 0, 25, 50, 75)]
    levels = (-1.0, 0.0, 1.0)
    vertices = [
        (math.cos(angle), math.sin(angle), z)
        for z in levels
        for angle in angles
    ]
    width = len(angles)
    faces = []
    for row in range(len(levels) - 1):
        for column in range(width - 1):
            lower = row * width + column
            upper = (row + 1) * width + column
            faces.append((lower, lower + 1, upper + 1, upper))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location

    scale_matrix = Matrix.Diagonal((*object_scale, 1.0))
    if applied_scale:
        obj.data.transform(scale_matrix)
        obj.scale = (1.0, 1.0, 1.0)
    else:
        obj.scale = object_scale
    return obj


def add_solidify(obj, *, mode: str, even: bool = False, thickness_mode: str = "CONSTRAINTS"):
    modifier = obj.modifiers.new("Solidify", "SOLIDIFY")
    modifier.thickness = REQUESTED_THICKNESS
    modifier.offset = -1.0
    modifier.use_rim = True
    modifier.solidify_mode = mode
    modifier.use_even_offset = even
    if mode == "NON_MANIFOLD":
        modifier.nonmanifold_thickness_mode = thickness_mode
    return modifier


def measurements(obj: bpy.types.Object) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            world = evaluated.matrix_world
            evaluated_points = [world @ vertex.co for vertex in bm.verts]
            source_points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]

            source_count = len(source_points)
            correspondence_valid = len(evaluated_points) == source_count * 2
            wall_distances = []
            source_displacements = []
            second_match_distances = []
            if correspondence_valid:
                for source in source_points:
                    nearest = sorted(
                        ((point - source).length, point) for point in evaluated_points
                    )[:2]
                    source_displacements.append(nearest[0][0])
                    second_match_distances.append(nearest[1][0])
                    wall_distances.append((nearest[0][1] - nearest[1][1]).length)
            errors = [abs(distance - REQUESTED_THICKNESS) for distance in wall_distances]

            world_bm = bm.copy()
            try:
                world_bm.transform(world)
                volume = world_bm.calc_volume(signed=True)
            finally:
                world_bm.free()

            return {
                "base": {
                    "vertices": len(obj.data.vertices),
                    "edges": len(obj.data.edges),
                    "faces": len(obj.data.polygons),
                },
                "evaluated": {
                    "vertices": len(bm.verts),
                    "edges": len(bm.edges),
                    "faces": len(bm.faces),
                    "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                    "ngons": sum(len(face.verts) > 4 for face in bm.faces),
                    "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
                    "signed_world_volume": volume,
                },
                "pairing": {
                    "source_vertices": source_count,
                    "evaluated_vertices": len(evaluated_points),
                    "correspondence_valid": correspondence_valid,
                    "correspondence_pairs": len(wall_distances),
                    "max_closest_shell_source_displacement": max(source_displacements, default=0.0),
                    "max_second_shell_source_distance": max(second_match_distances, default=0.0),
                },
                "wall_thickness": {
                    "requested": REQUESTED_THICKNESS,
                    "minimum": min(wall_distances, default=0.0),
                    "maximum": max(wall_distances, default=0.0),
                    "mean": sum(wall_distances) / len(wall_distances),
                    "maximum_absolute_error": max(errors, default=0.0),
                    "mean_absolute_error": sum(errors) / len(errors),
                },
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def main() -> None:
    output_dir = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    variants = [
        ("Simple", "EXTRUDE", False, "CONSTRAINTS"),
        ("Simple_Even", "EXTRUDE", True, "CONSTRAINTS"),
        ("Complex_Fixed", "NON_MANIFOLD", False, "FIXED"),
        ("Complex_Even", "NON_MANIFOLD", False, "EVEN"),
        ("Complex_Constraints", "NON_MANIFOLD", False, "CONSTRAINTS"),
    ]

    records = []
    by_name = {}
    for index, (label, mode, even, thickness_mode) in enumerate(variants):
        obj = curved_panel(
            f"Solidify_Curved_{label}",
            (-8 + index * 4, 2.5, 0),
            applied_scale=True,
        )
        add_solidify(obj, mode=mode, even=even, thickness_mode=thickness_mode)
        entry = {
            "object": obj.name,
            "shape": "elliptical quarter-cylinder panel, scale baked",
            "settings": {
                "solidify_mode": mode,
                "use_even_offset": even,
                "nonmanifold_thickness_mode": thickness_mode if mode == "NON_MANIFOLD" else None,
            },
            **measurements(obj),
        }
        records.append(entry)
        by_name[label] = entry

    unapplied = curved_panel(
        "Solidify_Curved_UnappliedScale",
        (-2, -3.5, 0),
        applied_scale=False,
    )
    add_solidify(unapplied, mode="EXTRUDE", even=False)
    unapplied_entry = {
        "object": unapplied.name,
        "shape": "elliptical quarter-cylinder via unapplied object scale",
        "settings": {
            "solidify_mode": "EXTRUDE",
            "use_even_offset": False,
            "object_scale": [1.5, 0.75, 1.0],
            "scale_applied": False,
        },
        **measurements(unapplied),
    }
    records.append(unapplied_entry)

    assertions = {
        "all_applied_scale_variants_are_closed": all(
            by_name[label]["evaluated"]["non_manifold_edges"] == 0 for label, *_ in variants
        ),
        "all_variants_have_complete_shell_correspondence": all(
            entry["pairing"]["correspondence_valid"]
            and entry["pairing"]["correspondence_pairs"] == entry["pairing"]["source_vertices"]
            for entry in records
        ),
        "applied_simple_hits_requested_vertex_pair_distance": (
            by_name["Simple"]["wall_thickness"]["maximum_absolute_error"] < 1e-5
        ),
        "complex_constraints_is_closed": (
            by_name["Complex_Constraints"]["evaluated"]["non_manifold_edges"] == 0
        ),
        "unapplied_scale_has_more_thickness_error": (
            unapplied_entry["wall_thickness"]["maximum_absolute_error"]
            > by_name["Simple"]["wall_thickness"]["maximum_absolute_error"] + 1e-4
        ),
    }

    report = {
        "lab": "solidify_curved_second_shape_transfer",
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode("utf-8"),
        "records": records,
        "hypotheses": {
            "simple_even_reduces_maximum_vertex_pair_error": (
                by_name["Simple_Even"]["wall_thickness"]["maximum_absolute_error"]
                < by_name["Simple"]["wall_thickness"]["maximum_absolute_error"]
            ),
            "complex_constraints_reduces_maximum_vertex_pair_error": (
                by_name["Complex_Constraints"]["wall_thickness"]["maximum_absolute_error"]
                < by_name["Simple"]["wall_thickness"]["maximum_absolute_error"]
            ),
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
    }

    (output_dir / "solidify_transfer_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "solidify_transfer_lab.blend"))
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("one or more Solidify transfer assertions failed")


if __name__ == "__main__":
    main()
