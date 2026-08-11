"""Run reproducible standalone Boolean and Solidify modifier experiments.

Usage:
    blender --background --factory-startup \
      --python tools/run_boolean_solidify_foundation_lab.py -- OUTPUT_DIR

The lab saves a .blend scene and a JSON report containing base/evaluated
topology, world-space bounds and volume, explicit assertions, and known
failure evidence. It does not apply modifiers or hide poor intermediate
topology behind cleanup.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix


def output_directory() -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected exactly one OUTPUT_DIR argument after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def cube(name: str, location, size: float = 2.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = f"{name}_Mesh"
    return obj


def plane(name: str, location) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = f"{name}_Mesh"
    return obj


def cylinder(name: str, location) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1.0, depth=2.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = f"{name}_Mesh"
    return obj


def torus(name: str, location) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=1.0,
        minor_radius=0.12,
        major_segments=32,
        minor_segments=8,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.name = f"{name}_Mesh"
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


def add_boolean(target, cutter, operation: str, solver: str = "EXACT"):
    modifier = target.modifiers.new(f"Boolean_{operation}_{solver}", "BOOLEAN")
    modifier.operation = operation
    modifier.solver = solver
    modifier.object = cutter
    return modifier


def add_solidify(
    obj,
    *,
    thickness: float,
    offset: float = -1.0,
    use_rim: bool = True,
    use_even_offset: bool = False,
):
    modifier = obj.modifiers.new("Solidify", "SOLIDIFY")
    modifier.thickness = thickness
    modifier.offset = offset
    modifier.use_rim = use_rim
    modifier.use_even_offset = use_even_offset
    return modifier


def evaluated_metrics(obj: bpy.types.Object) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            world = evaluated.matrix_world
            world_points = [world @ vertex.co for vertex in bm.verts]
            world_edge_lengths = [
                ((world @ edge.verts[0].co) - (world @ edge.verts[1].co)).length
                for edge in bm.edges
            ]
            world_bm = bm.copy()
            try:
                world_bm.transform(world)
                signed_volume = world_bm.calc_volume(signed=True)
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
                    "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
                    "ngons": sum(len(face.verts) > 4 for face in bm.faces),
                    "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
                    "signed_world_volume": signed_volume,
                    "min_world_edge_length": min(world_edge_lengths, default=0.0),
                    "world_bounds": {
                        axis: [
                            min((getattr(point, axis) for point in world_points), default=0.0),
                            max((getattr(point, axis) for point in world_points), default=0.0),
                        ]
                        for axis in ("x", "y", "z")
                    },
                },
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def record(records: list[dict], obj, question: str, settings: dict) -> dict:
    entry = {
        "object": obj.name,
        "question": question,
        "settings": settings,
        **evaluated_metrics(obj),
    }
    records.append(entry)
    return entry


def boolean_pair(name: str, location, operation: str, solver: str = "EXACT"):
    target = cube(f"{name}_Target", location)
    cutter_location = (location[0] + 0.75, location[1], location[2])
    cutter = cube(f"{name}_Cutter", cutter_location, size=1.5)
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    add_boolean(target, cutter, operation, solver)
    return target


def main() -> None:
    output_dir = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    records: list[dict] = []

    difference_obj = boolean_pair("Boolean_Difference", (-9, 4, 0), "DIFFERENCE")
    difference = record(
        records,
        difference_obj,
        "Does Exact Difference remove the overlapping cutter volume cleanly?",
        {"operation": "DIFFERENCE", "solver": "EXACT", "cutter_offset_x": 0.75},
    )

    union_obj = boolean_pair("Boolean_Union", (-5, 4, 0), "UNION")
    union = record(
        records,
        union_obj,
        "Does Exact Union combine overlapping closed volumes and remove interior faces?",
        {"operation": "UNION", "solver": "EXACT", "cutter_offset_x": 0.75},
    )

    intersect_obj = boolean_pair("Boolean_Intersect", (-1, 4, 0), "INTERSECT")
    intersect = record(
        records,
        intersect_obj,
        "Does Exact Intersect retain only the shared volume?",
        {"operation": "INTERSECT", "solver": "EXACT", "cutter_offset_x": 0.75},
    )

    manifold_obj = boolean_pair("Boolean_ManifoldDifference", (3, 4, 0), "DIFFERENCE", "MANIFOLD")
    manifold = record(
        records,
        manifold_obj,
        "Does the Manifold solver handle the same closed-mesh Difference case?",
        {"operation": "DIFFERENCE", "solver": "MANIFOLD", "cutter_offset_x": 0.75},
    )

    groove_target = cylinder("Boolean_TangentGroove_Target", (7, 4, 0))
    groove_cutter = torus("Boolean_TangentGroove_Cutter", (7, 4, 0))
    add_boolean(groove_target, groove_cutter, "DIFFERENCE", "EXACT")
    groove = record(
        records,
        groove_target,
        "Does a near-tangent groove cutter reproduce topology-quality defects?",
        {
            "operation": "DIFFERENCE",
            "solver": "EXACT",
            "target": "32-sided cylinder radius 1",
            "cutter": "torus major radius 1, minor radius 0.12",
        },
    )

    rim_on_obj = plane("Solidify_Rim_On", (-9, -3, 0))
    add_solidify(rim_on_obj, thickness=0.2, use_rim=True)
    rim_on = record(
        records,
        rim_on_obj,
        "Does Fill Rim close the boundary between the two offset surfaces?",
        {"thickness": 0.2, "offset": -1.0, "use_rim": True},
    )

    rim_off_obj = plane("Solidify_Rim_Off", (-6, -3, 0))
    add_solidify(rim_off_obj, thickness=0.2, use_rim=False)
    rim_off = record(
        records,
        rim_off_obj,
        "Does disabling Fill Rim intentionally leave open boundaries?",
        {"thickness": 0.2, "offset": -1.0, "use_rim": False},
    )

    offset_records = {}
    for index, offset in enumerate((-1.0, 0.0, 1.0)):
        offset_obj = plane(f"Solidify_Offset_{offset:+.0f}", (-3 + index * 3, -3, 0))
        add_solidify(offset_obj, thickness=0.2, offset=offset, use_rim=True)
        offset_records[offset] = record(
            records,
            offset_obj,
            "How does Offset place thickness relative to the original surface normal?",
            {"thickness": 0.2, "offset": offset, "use_rim": True},
        )

    scaled_obj = plane("Solidify_NonUniformScale", (6, -3, 0))
    scaled_obj.scale = (1.0, 1.0, 2.0)
    add_solidify(scaled_obj, thickness=0.2, use_rim=True)
    scaled = record(
        records,
        scaled_obj,
        "Does non-uniform object scale change world-space thickness?",
        {"thickness": 0.2, "object_scale": [1.0, 1.0, 2.0], "scale_applied": False},
    )

    applied_obj = plane("Solidify_AppliedScale", (9, -3, 0))
    applied_obj.data.transform(Matrix.Diagonal((1.0, 1.0, 2.0, 1.0)))
    applied_obj.scale = (1.0, 1.0, 1.0)
    add_solidify(applied_obj, thickness=0.2, use_rim=True)
    applied = record(
        records,
        applied_obj,
        "Does applying the same scale restore the requested world-space thickness?",
        {"thickness": 0.2, "object_scale": [1.0, 1.0, 1.0], "scale_applied": True},
    )

    abs_volume = lambda entry: abs(entry["evaluated"]["signed_world_volume"])
    z_span = lambda entry: (
        entry["evaluated"]["world_bounds"]["z"][1]
        - entry["evaluated"]["world_bounds"]["z"][0]
    )

    assertions = {
        "difference_is_closed_and_reduces_volume": (
            difference["evaluated"]["non_manifold_edges"] == 0
            and 0.0 < abs_volume(difference) < 8.0
        ),
        "union_is_closed_and_increases_volume": (
            union["evaluated"]["non_manifold_edges"] == 0 and abs_volume(union) > 8.0
        ),
        "intersect_is_closed_shared_volume": (
            intersect["evaluated"]["non_manifold_edges"] == 0
            and 0.0 < abs_volume(intersect) < 8.0
        ),
        "manifold_solver_handles_closed_difference": (
            manifold["evaluated"]["non_manifold_edges"] == 0
            and abs(abs_volume(manifold) - abs_volume(difference)) < 1e-5
        ),
        "tangent_boolean_exposes_quality_defect": (
            groove["evaluated"]["ngons"] > 0
            or groove["evaluated"]["degenerate_faces"] > 0
        ),
        "solidify_fill_rim_is_closed": rim_on["evaluated"]["non_manifold_edges"] == 0,
        "solidify_without_rim_is_open": rim_off["evaluated"]["boundary_edges"] > 0,
        "solidify_offsets_place_shell_as_documented": (
            offset_records[-1.0]["evaluated"]["world_bounds"]["z"][1] <= 1e-6
            and offset_records[1.0]["evaluated"]["world_bounds"]["z"][0] >= -1e-6
            and abs(sum(offset_records[0.0]["evaluated"]["world_bounds"]["z"])) < 1e-6
        ),
        "non_uniform_scale_changes_world_thickness": (
            abs(z_span(scaled) - 2.0 * z_span(applied)) < 1e-5
        ),
    }

    report = {
        "lab": "standalone_boolean_solidify",
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode("utf-8"),
        "records": records,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }

    report_path = output_dir / "boolean_solidify_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "boolean_solidify_lab.blend"))
    print(json.dumps(report, indent=2))

    if not report["pass"]:
        raise SystemExit("one or more Boolean/Solidify foundation assertions failed")


if __name__ == "__main__":
    main()
