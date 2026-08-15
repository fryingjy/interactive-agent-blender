"""Independent fresh-process verification for the bridge correspondence control lab."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def args():
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 2:
        raise SystemExit("expected BLEND_FILE OUTPUT_JSON after --")
    return Path(values[0]).resolve(), Path(values[1]).resolve()


def inspect_bridge(obj):
    lower = int(obj["lower_loop_count"])
    upper = int(obj["upper_loop_count"])
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    first = set(bm.verts[:lower])
    second = set(bm.verts[lower : lower + upper])
    connectors = [
        edge for edge in bm.edges
        if ((edge.verts[0] in first and edge.verts[1] in second)
            or (edge.verts[1] in first and edge.verts[0] in second))
    ]
    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "non_quad_faces": sum(len(face.verts) != 4 for face in bm.faces),
        "boundary_edges": sum(edge.is_boundary or edge.is_wire for edge in bm.edges),
        "connector_edges": len(connectors),
        "non_manifold_connector_edges": sum(not edge.is_manifold for edge in connectors),
        "connector_length_total": sum(edge.calc_length() for edge in connectors),
        "connector_length_max": max((edge.calc_length() for edge in connectors), default=0.0),
        "twist_offset": int(obj.get("applied_twist_offset", 0)),
    }
    bm.free()
    return result


def main():
    blend_file, output = args()
    bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    families = {}
    checks = {}
    for family, segments in (("circle", 8), ("rounded_rectangle", 12)):
        default = inspect_bridge(bpy.data.objects[f"{family}_default"])
        corrected = inspect_bridge(bpy.data.objects[f"{family}_corrected"])
        families[family] = {"default": default, "corrected": corrected}
        checks[f"{family}_complete_quad_tubes"] = all(
            case["faces"] == segments
            and case["quads"] == segments
            and case["non_quad_faces"] == 0
            and case["connector_edges"] == segments
            and case["non_manifold_connector_edges"] == 0
            and case["boundary_edges"] == segments * 2
            for case in (default, corrected)
        )
        checks[f"{family}_nonzero_error_was_corrected"] = (
            default["twist_offset"] != 0
            and corrected["twist_offset"] != default["twist_offset"]
        )
        checks[f"{family}_correction_reduces_connector_length"] = (
            corrected["connector_length_total"] < default["connector_length_total"] * 0.75
        )

    unequal = inspect_bridge(bpy.data.objects["unequal_10_12_guard"])
    partial = inspect_bridge(bpy.data.objects["partial_failure_rollback"])
    checks["unequal_guard_left_source_loops_unbridged"] = (
        unequal["faces"] == 0 and unequal["vertices"] == 22 and unequal["edges"] == 22
    )
    checks["partial_failure_left_source_loops_unbridged"] = (
        partial["faces"] == 0 and partial["vertices"] == 16 and partial["edges"] == 16
    )
    expected_renders = [
        blend_file.parent / f"{family}_{role}_{pass_type}.png"
        for family in ("circle", "rounded_rectangle")
        for role in ("default", "corrected")
        for pass_type in ("solid", "wireframe")
    ]
    checks["all_diagnostic_renders_nonempty"] = all(
        path.exists() and path.stat().st_size > 1000 for path in expected_renders
    )
    expected_meshes = {
        "circle_defaultMesh",
        "circle_correctedMesh",
        "rounded_rectangle_defaultMesh",
        "rounded_rectangle_correctedMesh",
        "unequal_10_12_guardMesh",
        "partial_failure_rollbackMesh",
    }
    checks["no_transaction_snapshot_or_orphan_meshes_saved"] = (
        set(bpy.data.meshes.keys()) == expected_meshes
    )
    report = {
        "verifier": "independent_bridge_correspondence",
        "blender_version": bpy.app.version_string,
        "blend_file": str(blend_file),
        "families": families,
        "unequal_guard": unequal,
        "partial_failure": partial,
        "checks": checks,
        "pass": all(checks.values()),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("BRIDGE_CORRESPONDENCE_VERIFY:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
