"""Run reproducible standalone Bevel and Mirror modifier experiments.

Execute with Blender in background mode:

    blender --background --factory-startup --python tools/run_modifier_foundation_lab.py -- OUTPUT_DIR

The lab writes a viewable .blend plus a JSON report with base/evaluated mesh
measurements and assertions. It intentionally uses Blender's evaluated mesh as
the result authority instead of assuming modifier settings had the intended
effect.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy


def output_directory() -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected exactly one OUTPUT_DIR argument after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def link_mesh_object(name: str, vertices, faces, location) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def triangulated_cube(name: str, location) -> bpy.types.Object:
    vertices = [
        (-1, -1, -1),
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),
        (-1, -1, 1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, 1, 1),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]
    return link_mesh_object(name, vertices, faces, location)


def cube(name: str, location) -> bpy.types.Object:
    vertices = [
        (-1, -1, -1),
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),
        (-1, -1, 1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, 1, 1),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    return link_mesh_object(name, vertices, faces, location)


def open_half_box(name: str, seam_x: float, location) -> bpy.types.Object:
    """Create the +X half of a box with its mirror-plane face intentionally open."""
    vertices = [
        (seam_x, -1, -1),
        (1, -1, -1),
        (1, 1, -1),
        (seam_x, 1, -1),
        (seam_x, -1, 1),
        (1, -1, 1),
        (1, 1, 1),
        (seam_x, 1, 1),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
    ]
    return link_mesh_object(name, vertices, faces, location)


def add_bevel(obj, *, width: float, segments: int, limit_method: str, clamp: bool = True):
    modifier = obj.modifiers.new("Bevel", "BEVEL")
    modifier.affect = "EDGES"
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = limit_method
    modifier.angle_limit = math.radians(30)
    modifier.use_clamp_overlap = clamp
    return modifier


def add_mirror(obj, *, threshold: float, bisect: bool = False):
    modifier = obj.modifiers.new("Mirror", "MIRROR")
    modifier.use_axis[0] = True
    modifier.use_mirror_merge = True
    modifier.merge_threshold = threshold
    modifier.use_bisect_axis[0] = bisect
    return modifier


def mesh_metrics(obj: bpy.types.Object) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            edge_lengths = [edge.calc_length() for edge in bm.edges]
            xs = [vertex.co.x for vertex in bm.verts]
            ys = [vertex.co.y for vertex in bm.verts]
            zs = [vertex.co.z for vertex in bm.verts]
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
                    "min_edge_length": min(edge_lengths, default=0.0),
                    "max_edge_length": max(edge_lengths, default=0.0),
                    "bounds": {
                        "x": [min(xs, default=0.0), max(xs, default=0.0)],
                        "y": [min(ys, default=0.0), max(ys, default=0.0)],
                        "z": [min(zs, default=0.0), max(zs, default=0.0)],
                    },
                },
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def record(records: list[dict], obj: bpy.types.Object, question: str, settings: dict) -> dict:
    entry = {
        "object": obj.name,
        "question": question,
        "settings": settings,
        **mesh_metrics(obj),
    }
    records.append(entry)
    return entry


def main() -> None:
    output_dir = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    records: list[dict] = []

    bevel_none = triangulated_cube("Bevel_AllEdges_Triangulated", (-9, 3, 0))
    add_bevel(bevel_none, width=0.2, segments=2, limit_method="NONE")
    all_edges = record(
        records,
        bevel_none,
        "Does an unrestricted bevel affect coplanar triangulation edges?",
        {"width": 0.2, "segments": 2, "limit_method": "NONE"},
    )

    bevel_angle = triangulated_cube("Bevel_AngleLimit_Triangulated", (-6, 3, 0))
    add_bevel(bevel_angle, width=0.2, segments=2, limit_method="ANGLE")
    angle_edges = record(
        records,
        bevel_angle,
        "Does Angle limiting exclude coplanar triangulation edges?",
        {"width": 0.2, "segments": 2, "limit_method": "ANGLE", "angle_degrees": 30},
    )

    bevel_segment_1 = cube("Bevel_Segments_1", (-3, 3, 0))
    add_bevel(bevel_segment_1, width=0.2, segments=1, limit_method="ANGLE")
    segment_1 = record(
        records,
        bevel_segment_1,
        "How does segment count change evaluated topology?",
        {"width": 0.2, "segments": 1, "limit_method": "ANGLE"},
    )

    bevel_segment_3 = cube("Bevel_Segments_3", (0, 3, 0))
    add_bevel(bevel_segment_3, width=0.2, segments=3, limit_method="ANGLE")
    segment_3 = record(
        records,
        bevel_segment_3,
        "How does segment count change evaluated topology?",
        {"width": 0.2, "segments": 3, "limit_method": "ANGLE"},
    )

    bevel_clamped = cube("Bevel_Clamp_On", (3, 3, 0))
    add_bevel(bevel_clamped, width=2.0, segments=3, limit_method="ANGLE", clamp=True)
    clamped = record(
        records,
        bevel_clamped,
        "Does Clamp Overlap constrain an excessive width?",
        {"width": 2.0, "segments": 3, "limit_method": "ANGLE", "clamp_overlap": True},
    )

    bevel_unclamped = cube("Bevel_Clamp_Off", (6, 3, 0))
    add_bevel(bevel_unclamped, width=2.0, segments=3, limit_method="ANGLE", clamp=False)
    unclamped = record(
        records,
        bevel_unclamped,
        "What does the same excessive width produce without Clamp Overlap?",
        {"width": 2.0, "segments": 3, "limit_method": "ANGLE", "clamp_overlap": False},
    )

    mirror_exact = open_half_box("Mirror_ExactSeam", 0.0, (-6, -3, 0))
    add_mirror(mirror_exact, threshold=0.001)
    exact = record(
        records,
        mirror_exact,
        "Does an exact open seam merge into a closed evaluated mesh?",
        {"seam_x": 0.0, "merge_threshold": 0.001},
    )

    mirror_gap = open_half_box("Mirror_GapBelowThreshold", 0.002, (-3, -3, 0))
    add_mirror(mirror_gap, threshold=0.001)
    gap = record(
        records,
        mirror_gap,
        "Does a seam outside the merge threshold remain open?",
        {"seam_x": 0.002, "merge_threshold": 0.001},
    )

    mirror_merged = open_half_box("Mirror_GapWithinThreshold", 0.002, (0, -3, 0))
    add_mirror(mirror_merged, threshold=0.01)
    merged = record(
        records,
        mirror_merged,
        "Does a sufficient merge threshold close the same seam?",
        {"seam_x": 0.002, "merge_threshold": 0.01},
    )

    mirror_bisect = cube("Mirror_BisectCrossPlane", (3, -3, 0))
    add_mirror(mirror_bisect, threshold=0.001, bisect=True)
    bisected = record(
        records,
        mirror_bisect,
        "Does Bisect discard one side before mirroring a cross-plane mesh?",
        {"merge_threshold": 0.001, "bisect_x": True},
    )

    assertions = {
        "angle_limit_excludes_coplanar_edges": (
            angle_edges["evaluated"]["vertices"] < all_edges["evaluated"]["vertices"]
        ),
        "more_segments_add_topology": (
            segment_3["evaluated"]["vertices"] > segment_1["evaluated"]["vertices"]
        ),
        "clamp_changes_excessive_width_result": (
            clamped["evaluated"]["min_edge_length"]
            != unclamped["evaluated"]["min_edge_length"]
        ),
        "exact_mirror_seam_is_manifold": exact["evaluated"]["non_manifold_edges"] == 0,
        "outside_threshold_seam_stays_open": gap["evaluated"]["boundary_edges"] > 0,
        "larger_threshold_closes_same_seam": merged["evaluated"]["non_manifold_edges"] == 0,
        "bisected_mirror_is_manifold": bisected["evaluated"]["non_manifold_edges"] == 0,
    }

    report = {
        "lab": "standalone_bevel_mirror",
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode("utf-8"),
        "records": records,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }

    report_path = output_dir / "modifier_foundation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "modifier_foundation_lab.blend"))
    print(json.dumps(report, indent=2))

    if not report["pass"]:
        raise SystemExit("one or more modifier-foundation assertions failed")


if __name__ == "__main__":
    main()
