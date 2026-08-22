"""Fresh-process verification for the official Blender watering-can reproduction."""

from __future__ import annotations

import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-22_tutorial-blender-official-watering-can"


def mesh_record(mesh: bpy.types.Mesh) -> dict[str, object]:
    bm = bmesh.new()
    bm.from_mesh(mesh)
    remaining = set(bm.verts)
    components = []
    while remaining:
        size = 1
        stack = [remaining.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                neighbor = edge.other_vert(vertex)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    size += 1
        components.append(size)
    record = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "components": len(components),
        "component_vertex_counts": sorted(components, reverse=True),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
        "nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
    }
    bm.free()
    return record


def main() -> None:
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    obj = bpy.data.objects.get("GEO-watering_can")
    base = mesh_record(obj.data) if obj else None
    mirror = next((modifier for modifier in obj.modifiers if modifier.type == "MIRROR"), None) if obj else None
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph) if obj else None
    evaluated_mesh = evaluated.to_mesh(preserve_all_data_layers=False, depsgraph=depsgraph) if evaluated else None
    evaluated_record = mesh_record(evaluated_mesh) if evaluated_mesh else None
    bounds = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box] if evaluated else []
    dimensions = [
        max(point[axis] for point in bounds) - min(point[axis] for point in bounds)
        for axis in range(3)
    ] if bounds else [0.0, 0.0, 0.0]
    height_length_ratio = dimensions[2] / dimensions[1] if dimensions[1] else 0.0
    depth_length_ratio = dimensions[0] / dimensions[1] if dimensions[1] else 0.0
    checks = {
        "single_mesh_object": len(meshes) == 1 and bool(obj),
        "single_connected_base_cage": bool(base) and base["components"] == 1,
        "single_connected_evaluated_mesh": bool(evaluated_record) and evaluated_record["components"] == 1,
        "base_has_no_ngons_or_degenerates": bool(base) and base["ngons"] == 0 and base["degenerate_faces"] == 0,
        "base_is_quad_dominant": bool(base) and base["quads"] / base["faces"] > 0.95,
        "only_intentional_bottom_triangles": bool(base) and base["triangles"] == 16,
        "positive_x_half_cage": bool(obj) and min(vertex.co.x for vertex in obj.data.vertices) >= -1e-6,
        "live_unapplied_mirror": bool(mirror) and mirror.show_viewport and mirror.use_clip and mirror.use_mirror_merge,
        "official_height_length_ratio_matched": abs(height_length_ratio - (0.9418350459 / 1.4684081078)) < 0.025,
        "official_depth_length_ratio_close": abs(depth_length_ratio - (0.4125607908 / 1.4684081078)) < 0.035,
        "solid_and_wire_evidence_present": all((RUN / name).exists() for name in ("v5_side_solid.png", "v5_side_wire.png", "v5_isometric_solid.png")),
        "official_reference_audit_present": (RUN / "official_reference_asset_audit.json").exists(),
    }
    report = {
        "schema_version": 1,
        "record_type": "INDEPENDENT_TUTORIAL_REPRODUCTION_VERIFICATION",
        "blend_file": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "checks": checks,
        "passed": all(checks.values()),
        "base_mesh": base,
        "evaluated_mesh": evaluated_record,
        "evaluated_dimensions": dimensions,
        "evaluated_ratios": {
            "height_over_length": height_length_ratio,
            "depth_over_length": depth_length_ratio,
        },
        "official_reference_ratios": {
            "height_over_length": 0.9418350459 / 1.4684081078,
            "depth_over_length": 0.4125607908 / 1.4684081078,
        },
        "visual_boundary": "Technical and proportion checks do not replace the separate source-image visual review.",
    }
    if evaluated:
        evaluated.to_mesh_clear()
    (RUN / "independent_verification_v5.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
