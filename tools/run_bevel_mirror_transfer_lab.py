"""Second-shape transfer lab for Bevel and Mirror on cylindrical geometry."""

from __future__ import annotations

import json
import math
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


def half_cylinder(name: str, location, seam_x: float = 0.0) -> bpy.types.Object:
    angles = [math.radians(value) for value in (-90, -60, -30, 0, 30, 60, 90)]
    bottom = []
    top = []
    for angle in angles:
        x = math.cos(angle)
        if abs(x) < 1e-8:
            x = seam_x
        bottom.append((x, math.sin(angle), -1.0))
        top.append((x, math.sin(angle), 1.0))
    vertices = bottom + top + [(seam_x, 0.0, -1.0), (seam_x, 0.0, 1.0)]
    width = len(angles)
    bottom_center = width * 2
    top_center = bottom_center + 1
    faces = []
    for index in range(width - 1):
        faces.append((index, index + 1, width + index + 1, width + index))
        faces.append((top_center, width + index, width + index + 1))
        faces.append((bottom_center, index + 1, index))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def cylinder(name: str, location, *, applied_z_scale: bool) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1.0, depth=2.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = f"{name}_Mesh"
    if applied_z_scale:
        obj.data.transform(Matrix.Diagonal((1.0, 1.0, 2.0, 1.0)))
        obj.scale = (1.0, 1.0, 1.0)
    else:
        obj.scale = (1.0, 1.0, 2.0)
    return obj


def add_mirror(obj, threshold: float):
    modifier = obj.modifiers.new("Mirror", "MIRROR")
    modifier.use_axis[0] = True
    modifier.use_mirror_merge = True
    modifier.merge_threshold = threshold
    return modifier


def add_subdivision(obj):
    modifier = obj.modifiers.new("Subdivision", "SUBSURF")
    modifier.subdivision_type = "CATMULL_CLARK"
    modifier.levels = 2
    modifier.render_levels = 2
    return modifier


def add_bevel(obj):
    modifier = obj.modifiers.new("Bevel", "BEVEL")
    modifier.affect = "EDGES"
    modifier.width = 0.1
    modifier.segments = 1
    modifier.limit_method = "ANGLE"
    modifier.angle_limit = math.radians(30)
    return modifier


def metrics(obj: bpy.types.Object) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            world = evaluated.matrix_world
            points = [world @ vertex.co for vertex in bm.verts]
            z_values = sorted({round(point.z, 6) for point in points}, reverse=True)
            top_band_depth = z_values[0] - z_values[1] if len(z_values) > 1 else 0.0
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
                    "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
                    "ngons": sum(len(face.verts) > 4 for face in bm.faces),
                    "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
                    "signed_world_volume": volume,
                    "seam_vertices_x0": sum(abs(point.x - obj.location.x) < 1e-5 for point in points),
                    "top_band_depth": top_band_depth,
                    "world_z_values": z_values,
                },
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def record(records, obj, question, settings):
    entry = {"object": obj.name, "question": question, "settings": settings, **metrics(obj)}
    records.append(entry)
    return entry


def main() -> None:
    output_dir = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    records = []

    exact_obj = half_cylinder("Mirror_Cylinder_ExactSeam", (-8, 3, 0), 0.0)
    add_mirror(exact_obj, 0.001)
    exact = record(records, exact_obj, "Does a curved exact seam merge cleanly?", {"seam_x": 0.0, "threshold": 0.001})

    gap_obj = half_cylinder("Mirror_Cylinder_Gap", (-4, 3, 0), 0.002)
    add_mirror(gap_obj, 0.001)
    gap = record(records, gap_obj, "Does a curved seam outside the threshold stay open?", {"seam_x": 0.002, "threshold": 0.001})

    repaired_obj = half_cylinder("Mirror_Cylinder_RepairedThreshold", (0, 3, 0), 0.002)
    add_mirror(repaired_obj, 0.01)
    repaired = record(records, repaired_obj, "Does a sufficient threshold close the curved seam?", {"seam_x": 0.002, "threshold": 0.01})

    mirror_then_subd_obj = half_cylinder("Mirror_Then_SubD_Cylinder", (4, 3, 0), 0.0)
    add_mirror(mirror_then_subd_obj, 0.001)
    add_subdivision(mirror_then_subd_obj)
    mirror_then_subd = record(records, mirror_then_subd_obj, "Does Mirror before SubD preserve a welded curved seam?", {"order": ["MIRROR", "SUBSURF"]})

    subd_then_mirror_obj = half_cylinder("SubD_Then_Mirror_Cylinder", (8, 3, 0), 0.0)
    add_subdivision(subd_then_mirror_obj)
    add_mirror(subd_then_mirror_obj, 0.001)
    subd_then_mirror = record(records, subd_then_mirror_obj, "Does SubD before Mirror pull the open boundary away from the seam?", {"order": ["SUBSURF", "MIRROR"]})

    bevel_applied_obj = cylinder("Bevel_Cylinder_AppliedScale", (-3, -3, 0), applied_z_scale=True)
    add_bevel(bevel_applied_obj)
    bevel_applied = record(records, bevel_applied_obj, "What is world bevel depth after applying Z scale?", {"width": 0.1, "segments": 1, "z_scale_applied": True})

    bevel_unapplied_obj = cylinder("Bevel_Cylinder_UnappliedScale", (3, -3, 0), applied_z_scale=False)
    add_bevel(bevel_unapplied_obj)
    bevel_unapplied = record(records, bevel_unapplied_obj, "Does unapplied Z scale distort world bevel depth?", {"width": 0.1, "segments": 1, "object_scale": [1, 1, 2], "z_scale_applied": False})

    hypotheses = {
        "mirror_before_subd_is_clean_on_open_half_cylinder": mirror_then_subd["evaluated"]["non_manifold_edges"] == 0,
        "subd_before_mirror_is_clean_on_open_half_cylinder": subd_then_mirror["evaluated"]["non_manifold_edges"] == 0,
    }
    assertions = {
        "exact_curved_seam_is_closed": exact["evaluated"]["non_manifold_edges"] == 0,
        "outside_threshold_curved_seam_is_open": gap["evaluated"]["boundary_edges"] > 0,
        "larger_threshold_repairs_curved_seam": repaired["evaluated"]["non_manifold_edges"] == 0,
        "both_stack_orders_were_evaluated": mirror_then_subd["evaluated"]["vertices"] > 0 and subd_then_mirror["evaluated"]["vertices"] > 0,
        "applied_bevel_is_closed": bevel_applied["evaluated"]["non_manifold_edges"] == 0,
        "unapplied_bevel_is_closed": bevel_unapplied["evaluated"]["non_manifold_edges"] == 0,
        "unapplied_z_scale_changes_bevel_band_depth": abs(bevel_unapplied["evaluated"]["top_band_depth"] - bevel_applied["evaluated"]["top_band_depth"]) > 0.05,
    }

    report = {
        "lab": "bevel_mirror_cylindrical_second_shape_transfer",
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode("utf-8"),
        "records": records,
        "hypotheses": hypotheses,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (output_dir / "bevel_mirror_transfer_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "bevel_mirror_transfer_lab.blend"))
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("one or more Bevel/Mirror transfer assertions failed")


if __name__ == "__main__":
    main()
