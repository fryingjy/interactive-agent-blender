"""Controlled Blender lab for Bisect clear/fill modes and typed-operation limits."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import bmesh
import bpy

from lab_common import add_repo_paths

ROOT, OPS = add_repo_paths(__file__)

import mesh_ops


def make_cube(name: str, x: float):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for sequence in (bm.verts, bm.edges, bm.faces):
        for item in sequence:
            item.select = True
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "boundary_edges": sum(1 for edge in bm.edges if edge.is_boundary),
        "non_manifold_edges": sum(1 for edge in bm.edges if not edge.is_manifold),
        "ngons": sum(1 for face in bm.faces if len(face.verts) > 4),
    }
    bm.free()
    return result


def main():
    out = ROOT / "runs" / "2026-08-10_bisect-foundation"
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    cases = []

    def run(case_id, clear_inner=False, clear_outer=False, fill=False, expected_boundary=None):
        obj = make_cube(case_id, len(cases) * 3.0)
        before = topology(obj)
        try:
            operation = mesh_ops.bisect_selection(
                obj.name,
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
                clear_inner=clear_inner,
                clear_outer=clear_outer,
                fill=fill,
            )
            after = topology(obj)
            if expected_boundary is not None and after["boundary_edges"] != expected_boundary:
                raise AssertionError(f"expected {expected_boundary} boundary edges, got {after['boundary_edges']}")
            if fill and operation["filled_faces"] < 1:
                raise AssertionError("fill requested but no cap face was reported")
            cases.append({"case_id": case_id, "pass": True, "before": before, "operation": operation, "after": after})
        except Exception as exc:
            cases.append({"case_id": case_id, "pass": False, "error": str(exc), "traceback": traceback.format_exc()})

    run("cut_only", expected_boundary=0)
    run("clear_inner_open", clear_inner=True, expected_boundary=4)
    run("clear_outer_open", clear_outer=True, expected_boundary=4)
    run("clear_inner_filled", clear_inner=True, fill=True, expected_boundary=0)
    run("clear_outer_filled", clear_outer=True, fill=True, expected_boundary=0)

    invalid_obj = make_cube("fill_without_clear_rejected", len(cases) * 3.0)
    try:
        mesh_ops.bisect_selection(invalid_obj.name, (0, 0, 0), (0, 0, 1), fill=True)
        cases.append({"case_id": "fill_without_clear_rejected", "pass": False, "error": "operation unexpectedly accepted"})
    except ValueError as exc:
        cases.append({"case_id": "fill_without_clear_rejected", "pass": "requires clear_inner or clear_outer" in str(exc), "error": str(exc)})

    report = {
        "lab": "bisect_foundation",
        "blender_version": bpy.app.version_string,
        "cases": cases,
        "passed": sum(bool(case["pass"]) for case in cases),
        "total": len(cases),
    }
    report["pass"] = report["passed"] == report["total"]
    (out / "bisect_foundation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "bisect_foundation_lab.blend"))
    print("BISECT_FOUNDATION_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
