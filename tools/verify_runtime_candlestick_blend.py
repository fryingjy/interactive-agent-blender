"""Fresh-process saved-scene audit for the runtime candlestick.

This verifier intentionally does not import the generator.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import bpy
import bmesh


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from blender_ops import evaluated_probe, render_passes  # noqa: E402


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="runs/2026-08-15_runtime-use-candlestick")
    parser.add_argument("--object-name", default="Heldout_Candlestick")
    return parser.parse_args(argv)


def radial_cv(verts) -> float:
    radii = [(vert.co.x ** 2 + vert.co.y ** 2) ** 0.5 for vert in verts]
    mean = statistics.fmean(radii)
    return statistics.pstdev(radii) / mean if mean else 0.0


def main() -> int:
    args = parse_args()
    run = (ROOT / args.run_dir).resolve()
    generator = json.loads((run / "blender_runtime_report.json").read_text(encoding="utf-8"))
    contract = json.loads((run / "experiment_contract.json").read_text(encoding="utf-8"))
    objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    obj = bpy.data.objects.get(args.object_name)
    if obj is None:
        raise RuntimeError(f"{args.object_name} missing from saved scene")
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    edge_layer = bm.edges.layers.int.get("agent_edge_id")
    boundary_ids = sorted(edge[edge_layer] for edge in bm.edges if edge.is_boundary) if edge_layer else []
    ring_verts: dict[float, list] = {}
    for vert in bm.verts:
        ring_verts.setdefault(round(float(vert.co.z), 6), []).append(vert)
    ordered_rings = [ring_verts[key] for key in sorted(ring_verts)]
    components = 0
    remaining = set(bm.verts)
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            vert = stack.pop()
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    audit = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "non_quad_faces": sum(len(face.verts) != 4 for face in bm.faces),
        "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "loose_vertices": sum(not vert.link_edges for vert in bm.verts),
        "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
        "connected_components": components,
        "ring_count": len(ring_verts),
        "vertices_per_ring": sorted({len(verts) for verts in ring_verts.values()}),
        "bottom_ring_radial_cv": radial_cv(ordered_rings[0]),
        "top_ring_radial_cv": radial_cv(ordered_rings[-1]),
        "boundary_edge_ids": boundary_ids,
    }
    bm.free()
    evaluated = evaluated_probe.evaluated_mesh_health(obj.name)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()
    try:
        coords = [vertex.co.copy() for vertex in eval_mesh.vertices]
        max_z = max(co.z for co in coords)
        # Solidify's inward wall can put the inner rim slightly below the
        # absolute highest outer rim. Sample the top 1% of total height so
        # the annular cross-section is tested instead of one z-slice only.
        total_height = max(co.z for co in coords) - min(co.z for co in coords)
        top_coords = [co for co in coords if max_z - co.z <= total_height * 0.01]
        top_radii = sorted((co.x ** 2 + co.y ** 2) ** 0.5 for co in top_coords)
        xs, ys, zs = [co.x for co in coords], [co.y for co in coords], [co.z for co in coords]
        evaluated_form = {
            "width": max(xs) - min(xs),
            "depth": max(ys) - min(ys),
            "height": max(zs) - min(zs),
            "width_depth_ratio": (max(xs) - min(xs)) / (max(ys) - min(ys)),
            "width_height_ratio": (max(xs) - min(xs)) / (max(zs) - min(zs)),
            "top_max_z_vertex_count": len(top_coords),
            "top_radius_min": min(top_radii),
            "top_radius_max": max(top_radii),
            "top_annular_wall_detected": len(top_radii) >= 24 and min(top_radii) > 0.05 and max(top_radii) - min(top_radii) > 0.01,
        }
    finally:
        eval_obj.to_mesh_clear()
    render = render_passes.render_silhouette(
        obj.name, str(run / "independent_candidate_mask.png"),
        view="front", resolution=720, margin=1.12,
    )
    top_silhouette = render_passes.render_silhouette(
        obj.name, str(run / "independent_top_mask.png"),
        view="top", resolution=720, margin=1.12,
    )
    top_solid = render_passes.render_diagnostic_pass(
        obj.name, str(run / "independent_top_solid.png"), "solid",
        view="top", resolution=720, margin=1.12,
    )
    expected = contract["frozen_acceptance_gates"]["base_mesh"]
    expected_evaluated = contract["frozen_acceptance_gates"].get("evaluated_mesh", {})
    expected_rings = contract["strategy"]["axial_rings_after_cut"]
    expected_radial = contract["strategy"]["radial_vertices"]
    modifier_types = [modifier.type for modifier in obj.modifiers]
    relevant_modifier_order = [kind for kind in modifier_types if kind in {"SUBSURF", "SOLIDIFY"}]
    published = contract["reference"].get("published_dimensions_cm")
    ratio_error = None
    if published:
        ratio_error = abs(evaluated_form["width_height_ratio"] - published["width"] / published["height"])
    cross_view = contract["frozen_acceptance_gates"].get("cross_view_form", {})
    checks = {
        "one_mesh_object": len(objects) == 1,
        "expected_object_name": objects[0].name == args.object_name if len(objects) == 1 else False,
        "base_counts_match_contract": (
            audit["vertices"] == expected["vertices"] and audit["edges"] == expected.get("edges", audit["edges"])
            and audit["faces"] == expected["faces"] and audit["quads"] == expected["quads"]
            and audit["non_quad_faces"] == expected["non_quad_faces"]
            and audit["boundary_edges"] == expected["intentional_boundary_edges"]
            and audit["loose_vertices"] == expected["loose_vertices"]
            and audit["degenerate_faces"] == expected["degenerate_faces"]
            and audit["connected_components"] == expected["connected_components"]
        ),
        "all_quad_cage": audit["faces"] == audit["quads"] and audit["non_quad_faces"] == 0,
        "declared_sparse_ring_cage": audit["ring_count"] == expected_rings and audit["vertices_per_ring"] == [expected_radial],
        "boundary_ids_match_declared_allowlist": boundary_ids == generator["construction"]["intentional_boundary_edge_ids"],
        "smooth_by_angle_persisted": obj.get("shading_policy") == "SMOOTH_BY_ANGLE",
        "evaluated_non_manifold_gate": evaluated["non_manifold_edges"] == expected_evaluated.get("non_manifold_edges", expected["intentional_boundary_edges"]),
        "evaluated_loose_gate": evaluated["loose_verts"] == expected_evaluated.get("loose_vertices", 0),
        "evaluated_degenerate_gate": evaluated["degenerate_faces"] == expected_evaluated.get("degenerate_faces", 0),
        "modifier_order": relevant_modifier_order == expected_evaluated.get("modifier_order", relevant_modifier_order),
        "bottom_ring_circular": audit["bottom_ring_radial_cv"] <= cross_view.get("base_ring_radial_cv_max", 1.0),
        "top_ring_circular": audit["top_ring_radial_cv"] <= cross_view.get("top_ring_radial_cv_max", 1.0),
        "circular_width_depth": abs(evaluated_form["width_depth_ratio"] - 1.0) <= cross_view.get("circular_width_depth_ratio_error_max", 1.0),
        "published_dimension_ratio": ratio_error is None or ratio_error <= contract["frozen_acceptance_gates"].get("reference", {}).get("dimension_ratio_absolute_error_max", 1.0),
        "hollow_socket": not cross_view.get("hollow_socket_required", False) or evaluated_form["top_annular_wall_detected"],
        "fresh_silhouette_rendered": "error" not in render and Path(render["output_path"]).exists(),
        "fresh_top_evidence_rendered": "error" not in top_silhouette and "error" not in top_solid,
    }
    report = {
        "method": "fresh Blender 5.2 factory process loaded the saved blend; no generator import",
        "blend_filepath": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "mesh_objects": [item.name for item in objects],
        "base_audit": audit,
        "evaluated_health": evaluated,
        "evaluated_form": evaluated_form,
        "modifier_types": modifier_types,
        "render": render,
        "top_silhouette_render": top_silhouette,
        "top_solid_render": top_solid,
        "checks": checks,
        "pass_geometry_and_render": all(checks.values()),
    }
    (run / "independent_blend_verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass_geometry_and_render"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
