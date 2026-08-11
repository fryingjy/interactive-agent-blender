"""Controlled Blender 5.2 lab for bevel width semantics and overlap clamping."""

from __future__ import annotations

import json
import math
import traceback
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]


def bevel_cube(name: str, x: float, offset_type: str, amount: float, clamp_overlap: bool):
    mesh = bpy.data.meshes.new(name + "Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location.x = x
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    before = {"vertices": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces)}
    result = bmesh.ops.bevel(
        bm,
        geom=list(bm.edges),
        offset=amount,
        offset_type=offset_type,
        segments=2,
        profile=0.5,
        affect="EDGES",
        clamp_overlap=clamp_overlap,
    )
    bm.normal_update()
    face_areas = [face.calc_area() for face in bm.faces]
    state = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "volume": abs(bm.calc_volume(signed=True)),
        "surface_area": sum(face_areas),
        "minimum_face_area": min(face_areas),
        "non_manifold_edges": sum(1 for edge in bm.edges if not edge.is_manifold),
        "new_faces_returned": len(result.get("faces", [])),
    }
    bm.to_mesh(mesh)
    bm.free()
    return before, state


def main():
    out = ROOT / "runs" / "2026-08-10_bevel-parameters"
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    cases = []
    width_inputs = {
        "OFFSET": 0.2,
        "WIDTH": 0.2,
        "DEPTH": 0.2,
        "PERCENT": 20.0,
        "ABSOLUTE": 0.2,
    }
    for index, (offset_type, amount) in enumerate(width_inputs.items()):
        try:
            before, after = bevel_cube(f"Bevel_{offset_type}", index * 3.0, offset_type, amount, True)
            cases.append({
                "case_id": f"width_type_{offset_type.lower()}",
                "pass": after["non_manifold_edges"] == 0 and after["vertices"] > before["vertices"],
                "input": {"offset_type": offset_type, "amount": amount, "clamp_overlap": True},
                "before": before,
                "after": after,
            })
        except Exception as exc:
            cases.append({"case_id": f"width_type_{offset_type.lower()}", "pass": False, "error": str(exc), "traceback": traceback.format_exc()})

    for clamp_overlap in (False, True):
        try:
            before, after = bevel_cube(
                f"Bevel_Huge_{'Clamped' if clamp_overlap else 'Unclamped'}",
                (len(cases) + int(clamp_overlap)) * 3.0,
                "OFFSET",
                5.0,
                clamp_overlap,
            )
            cases.append({
                "case_id": f"huge_offset_clamp_{str(clamp_overlap).lower()}",
                "pass": after["vertices"] > before["vertices"],
                "input": {"offset_type": "OFFSET", "amount": 5.0, "clamp_overlap": clamp_overlap},
                "before": before,
                "after": after,
            })
        except Exception as exc:
            cases.append({"case_id": f"huge_offset_clamp_{str(clamp_overlap).lower()}", "pass": not clamp_overlap, "error": str(exc), "traceback": traceback.format_exc()})

    width_cases = [case for case in cases if case["case_id"].startswith("width_type_") and case["pass"]]
    distinct_volumes = {round(case["after"]["volume"], 6) for case in width_cases}
    clamped = next(case for case in cases if case["case_id"] == "huge_offset_clamp_true")
    unclamped = next(case for case in cases if case["case_id"] == "huge_offset_clamp_false")
    semantic_checks = {
        "all_five_width_types_executed_cleanly": len(width_cases) == 5,
        "width_types_are_not_numerically_interchangeable": len(distinct_volumes) >= 3,
        "clamp_changes_huge_offset_result": (
            clamped.get("after", {}).get("volume") != unclamped.get("after", {}).get("volume")
            or clamped.get("after", {}).get("vertices") != unclamped.get("after", {}).get("vertices")
            or "error" in unclamped
        ),
    }
    report = {
        "lab": "bevel_parameter_semantics",
        "blender_version": bpy.app.version_string,
        "cases": cases,
        "semantic_checks": semantic_checks,
    }
    report["pass"] = all(case["pass"] for case in cases) and all(semantic_checks.values())
    (out / "bevel_parameter_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "bevel_parameter_lab.blend"))
    print("BEVEL_PARAMETER_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
