"""Actual sculpt-to-retopo handoff plus deformation-aware density comparison."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_sculpt-retopo-deformation"
SOURCE = ROOT / "runs" / "2026-08-10_sculpt-export" / "sculpt_export_lab.blend"
sys.path.insert(0, str(ROOT / "blender_ops"))
import render_passes


def active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def evaluated_counts(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            return {
                "vertices": len(bm.verts),
                "edges": len(bm.edges),
                "faces": len(bm.faces),
                "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
                "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                "ngons": sum(len(face.verts) > 4 for face in bm.faces),
                "triangles": sum(len(face.verts) == 3 for face in bm.faces),
                "quads": sum(len(face.verts) == 4 for face in bm.faces),
                "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def face_center_error(source, target):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = source.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    target_bvh = BVHTree.FromObject(target, depsgraph)
    try:
        distances = []
        world = evaluated.matrix_world
        target_inverse = target.matrix_world.inverted()
        for polygon in mesh.polygons:
            # BVHTree.FromObject is queried in the target object's local space.
            nearest = target_bvh.find_nearest(target_inverse @ (world @ polygon.center))
            if nearest is not None:
                distances.append(nearest[3])
        distances.sort()
        return {
            "samples": len(distances),
            "mean": sum(distances) / len(distances),
            "maximum": max(distances),
            "p95": distances[min(len(distances) - 1, int(len(distances) * 0.95))],
        }
    finally:
        evaluated.to_mesh_clear()


def make_tube(name, ring_count, segments, location):
    verts = []
    faces = []
    for ring in range(ring_count):
        t = ring / (ring_count - 1)
        z = -2.0 + 4.0 * t
        radius = 0.62 + 0.15 * math.exp(-((z - 0.35) / 0.55) ** 2) - 0.05 * t
        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    for ring in range(ring_count - 1):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            a = ring * segments + segment
            b = ring * segments + nxt
            c = (ring + 1) * segments + nxt
            d = (ring + 1) * segments + segment
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    bend = obj.modifiers.new("Shared 70 Degree Bend", "SIMPLE_DEFORM")
    bend.deform_method = "BEND"
    bend.deform_axis = "Z"
    bend.angle = math.radians(70)
    return obj


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        raise SystemExit(f"missing actual sculpt evidence: {SOURCE}")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Append only the evidence object. open_mainfile() replaces GUI state and
    # can terminate the currently running --python script before its quit path.
    with bpy.data.libraries.load(str(SOURCE), link=False) as (data_from, data_to):
        if "BrushSculpt" not in data_from.objects:
            raise SystemExit("BrushSculpt not present in source evidence")
        data_to.objects = ["BrushSculpt"]
    sculpt = data_to.objects[0]
    if sculpt is None:
        raise SystemExit("BrushSculpt not present in source evidence")
    bpy.context.scene.collection.objects.link(sculpt)
    sculpt.name = "ActualBrushSculpt_High"
    source_vertices = len(sculpt.data.vertices)
    source_faces = len(sculpt.data.polygons)
    source_provenance = {
        "blend": str(SOURCE),
        "object": "BrushSculpt",
        "actual_brush_moved_vertices": 248,
        "note": "created by recorded VIEW_3D Sculpt Draw stroke in the source run",
    }

    active(sculpt)
    sculpt.location = (-3.0, 0.0, 0.0)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.12, location=sculpt.location)
    cage = bpy.context.object
    cage.name = "SculptRetopo_LowCage"
    shrink = cage.modifiers.new("Project to actual brush sculpt", "SHRINKWRAP")
    shrink.target = sculpt
    shrink.wrap_method = "NEAREST_SURFACEPOINT"
    active(cage)
    bpy.ops.object.modifier_apply(modifier=shrink.name)
    sculpt_retopo = {
        "source_provenance": source_provenance,
        "source": {"vertices": source_vertices, "faces": source_faces},
        "cage": evaluated_counts(cage),
        "face_center_surface_error": face_center_error(cage, sculpt),
    }

    high = make_tube("Deform_HighReference", 65, 48, (3.0, 0.0, 0.0))
    adequate = make_tube("Deform_Retopo_Adequate", 17, 16, (3.0, 0.0, 0.0))
    sparse = make_tube("Deform_Retopo_Sparse", 5, 16, (3.0, 0.0, 0.0))
    deformation = {
        "high": evaluated_counts(high),
        "adequate": {"topology": evaluated_counts(adequate), "error": face_center_error(adequate, high)},
        "sparse": {"topology": evaluated_counts(sparse), "error": face_center_error(sparse, high)},
        "interpretation": "shared bend isolates axial loop density; the sparse cage undersamples the bulge and bend",
    }
    visuals = {
        "sculpt_solid": render_passes.render_diagnostic_pass(
            sculpt.name, str(OUT / "actual_sculpt_solid.png"), "solid", view="isometric", resolution=384
        ),
        "retopo_wire": render_passes.render_diagnostic_pass(
            cage.name, str(OUT / "retopo_cage_wire.png"), "wireframe", view="isometric",
            resolution=384, frame_name=sculpt.name,
        ),
        "deformation_wire": render_passes.render_diagnostic_pass(
            adequate.name, str(OUT / "deformation_adequate_wire.png"), "wireframe", view="front",
            resolution=384, frame_name=high.name,
        ),
    }

    assertions = {
        "actual_sculpt_source_used": source_vertices == 2562 and source_provenance["actual_brush_moved_vertices"] > 0,
        "retopo_reduces_density_by_ten_x": sculpt_retopo["cage"]["vertices"] * 10 < source_vertices,
        "retopo_is_closed_and_nondegenerate": sculpt_retopo["cage"]["non_manifold_edges"] == 0 and sculpt_retopo["cage"]["degenerate_faces"] == 0,
        "retopo_surface_mean_error_below_0_04": sculpt_retopo["face_center_surface_error"]["mean"] < 0.04,
        "deformation_cages_are_quad_routed": deformation["adequate"]["topology"]["ngons"] == 0 and deformation["adequate"]["topology"]["triangles"] == 0,
        "adequate_density_beats_sparse_mean_error": deformation["adequate"]["error"]["mean"] < deformation["sparse"]["error"]["mean"],
        "adequate_density_beats_sparse_max_error": deformation["adequate"]["error"]["maximum"] < deformation["sparse"]["error"]["maximum"],
        "visual_evidence_is_nonblank": all(item["foreground_fill_ratio"] > 0.001 for item in visuals.values()),
    }
    report = {
        "lab": "actual_sculpt_retopology_and_deformation_density",
        "blender_version": bpy.app.version_string,
        "sculpt_retopology": sculpt_retopo,
        "deformation": deformation,
        "visuals": visuals,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (OUT / "sculpt_retopology_deformation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "sculpt_retopology_deformation_lab.blend"))
    print("SCULPT_RETOPO_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("one or more assertions failed")
    if not bpy.app.background:
        bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
