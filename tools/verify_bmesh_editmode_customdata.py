"""Fresh-process verifier for the Edit Mode BMesh custom-data fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bmesh
import bpy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("blend", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    obj = bpy.data.objects.get("BMesh_EditMode_CustomData")
    mesh = obj.data if obj and obj.type == "MESH" else None
    attributes = mesh.attributes if mesh else {}

    check_bm = bmesh.new()
    if mesh:
        check_bm.from_mesh(mesh)
    non_manifold = sum(not edge.is_manifold for edge in check_bm.edges)
    degenerate_faces = sum(face.calc_area() <= 1e-12 for face in check_bm.faces)
    face_sizes = sorted({len(face.verts) for face in check_bm.faces})
    check_bm.free()

    def nonzero(name: str) -> int:
        attribute = attributes.get(name) if mesh else None
        return sum(abs(getattr(item, "value", 0)) > 1e-8 for item in attribute.data) if attribute else 0

    actual = {
        "vertices": len(mesh.vertices) if mesh else 0,
        "edges": len(mesh.edges) if mesh else 0,
        "faces": len(mesh.polygons) if mesh else 0,
        "weighted_edges": nonzero("bevel_weight_edge"),
        "creased_edges": nonzero("crease_edge"),
        "semantic_faces": nonzero("semantic_region"),
        "uv_layers": list(mesh.uv_layers.keys()) if mesh else [],
        "non_manifold_edges": non_manifold,
        "degenerate_faces": degenerate_faces,
        "face_sizes": face_sizes,
    }
    expected_weighted = int(obj.get("expected_weighted_edge_count", 0)) if obj else 0
    expected_creased = int(obj.get("expected_creased_edge_count", 0)) if obj else 0
    expected_semantic = int(obj.get("expected_semantic_face_count", 0)) if obj else 0
    assertions = {
        "single_expected_mesh_object": obj is not None and len([item for item in bpy.data.objects if item.type == "MESH"]) == 1,
        "fixture_purpose_recorded": obj is not None and obj.get("fixture_purpose") == "edit_mode_bmesh_customdata_api_validation",
        "topology_is_subdivided_cube": actual["vertices"] == 26 and actual["edges"] == 48 and actual["faces"] == 24,
        "bevel_weights_match_record": actual["weighted_edges"] == expected_weighted > 0,
        "creases_match_record": actual["creased_edges"] == expected_creased > 0,
        "semantic_faces_match_record": actual["semantic_faces"] == expected_semantic > 0,
        "uv_layer_present": actual["uv_layers"] == ["UVMap"],
        "closed_non_degenerate_all_quad": non_manifold == 0 and degenerate_faces == 0 and face_sizes == [4],
    }
    result = {
        "blender_version": bpy.app.version_string,
        "blend": str(args.blend),
        "actual": actual,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "claim_boundary": "Independent saved-file verification of the bounded fixture; no modeling code from the builder is imported.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    raise SystemExit(0 if result["pass"] else 2)


main()
