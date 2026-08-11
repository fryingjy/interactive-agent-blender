"""Independent fresh-process verification for the one-object camera correction."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def arguments():
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 2:
        raise SystemExit("expected BLEND_FILE OUTPUT_REPORT after --")
    return Path(values[0]).resolve(), Path(values[1]).resolve()


def health(obj, evaluated=False):
    owner = None
    mesh = obj.data
    if evaluated:
        owner = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = owner.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    components = 0
    unseen = set(bm.verts)
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "components": components,
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "loose_vertices": sum(not vertex.link_edges for vertex in bm.verts),
    }
    bm.free()
    if owner:
        owner.to_mesh_clear()
    return result


def main():
    blend_file, output = arguments()
    bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    obj = meshes[0] if len(meshes) == 1 else None
    base = health(obj) if obj else {}
    evaluated = health(obj, True) if obj else {}
    run_dir = blend_file.parent
    generator = json.loads((run_dir / "connected_camera_report.json").read_text(encoding="utf-8"))
    silhouette = json.loads((run_dir / "normalized_silhouette_report.json").read_text(encoding="utf-8"))
    assertions = {
        "generator_report_passes": generator.get("pass") is True,
        "silhouette_report_passes": silhouette.get("pass") is True,
        "exactly_one_mesh_object": len(meshes) == 1,
        "one_connected_component_base": bool(obj) and base["components"] == 1,
        "one_connected_component_evaluated": bool(obj) and evaluated["components"] == 1,
        "all_quads_base": bool(obj) and base["faces"] == base["quads"],
        "all_quads_evaluated": bool(obj) and evaluated["faces"] == evaluated["quads"],
        "closed_manifold_base": bool(obj) and base["non_manifold_edges"] == 0,
        "closed_manifold_evaluated": bool(obj) and evaluated["non_manifold_edges"] == 0,
        "clean_geometry": bool(obj) and base["degenerate_faces"] == 0 and base["loose_vertices"] == 0,
        "subdivision_is_present": bool(obj) and any(modifier.type == "SUBSURF" for modifier in obj.modifiers),
        "weighted_bevel_precedes_subdivision": bool(obj) and [modifier.type for modifier in obj.modifiers][:2] == ["BEVEL", "SUBSURF"],
        "weighted_bevel_scope_matches_accepted_probe": bool(obj) and obj.get("weighted_bevel_edges") == 144,
        "radial_control_density_is_12_to_16": bool(obj) and 12 <= obj.get("authored_radial_vertices", 0) <= 16,
        "construction_intent_is_recorded": bool(obj) and "routed loops" in obj.get("construction_intent", ""),
        "disconnected_islands_are_forbidden": bool(obj) and obj.get("disconnected_mesh_islands_allowed") is False,
        "populated_uv_layer": bool(obj) and bool(obj.data.uv_layers) and len(obj.data.uv_layers.active.data) == len(obj.data.loops),
        "four_integrated_material_regions": bool(obj) and len(obj.data.materials) == 4 and len({face.material_index for face in obj.data.polygons}) == 4,
        "solid_review_set_exists": all((run_dir / f"connected_{view}_solid.png").is_file() for view in ("front", "side", "top", "isometric")),
    }
    report = {
        "lab": "connected_camera_corrective_independent_verification",
        "blend_file": str(blend_file),
        "base_health": base,
        "evaluated_health": evaluated,
        "silhouette_mean_iou": silhouette.get("mean_iou"),
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CONNECTED_CAMERA_VERIFY:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


main()
