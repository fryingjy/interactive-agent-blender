"""Prove the typed Bridge Edge Loops twist control against Blender 5.2.

This is deliberately a matched-loop fixture.  It proves that the exposed
parameter changes the actual source-to-target pairing while keeping a clean
quad tube.  It does not claim that twist cures the teapot handle's unequal
10-versus-12 loop attachment; matching loop density remains the first repair.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "blender_ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

import mesh_ops

OUT = ROOT / "runs" / "2026-08-15_bridge-twist-control"
SEGMENTS = 8


def make_two_rings(name: str):
    vertices = []
    edges = []
    for z in (-0.75, 0.75):
        for index in range(SEGMENTS):
            angle = math.tau * index / SEGMENTS
            vertices.append((math.cos(angle), math.sin(angle), z))
        start = len(vertices) - SEGMENTS
        edges.extend((start + index, start + (index + 1) % SEGMENTS) for index in range(SEGMENTS))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for edge in obj.data.edges:
        edge.select = True
    return obj


def cross_loop_pairs(obj):
    pairs = []
    for edge in obj.data.edges:
        first, second = edge.vertices[:]
        if (first < SEGMENTS) != (second < SEGMENTS):
            lower, upper = (first, second) if first < SEGMENTS else (second, first)
            pairs.append((lower, upper - SEGMENTS))
    return sorted(pairs)


def bridge_edge_health(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bridge_edges = [
        edge
        for edge in bm.edges
        if (edge.verts[0].index < SEGMENTS) != (edge.verts[1].index < SEGMENTS)
    ]
    result = {
        "open_boundary_edges": sum(not edge.is_manifold for edge in bm.edges),
        "bridge_edges": len(bridge_edges),
        "non_manifold_bridge_edges": sum(not edge.is_manifold for edge in bridge_edges),
    }
    bm.free()
    return result


def inspect_case(twist: int):
    obj = make_two_rings(f"BridgeTwist_{twist}")
    result = mesh_ops.bridge_selection(obj.name, twist=twist)
    pairs = cross_loop_pairs(obj)
    return {
        "twist": twist,
        "operation": result,
        "faces": len(obj.data.polygons),
        "quad_faces": sum(len(face.vertices) == 4 for face in obj.data.polygons),
        **bridge_edge_health(obj),
        "cross_loop_pairs": pairs,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    base = inspect_case(0)
    offset = inspect_case(2)
    assertions = {
        "blender_api_exposes_twist_offset": "twist_offset" in bmesh.ops.bridge_loops.__doc__,
        "wrapper_reports_requested_zero_twist": base["operation"]["twist"] == 0,
        "wrapper_reports_requested_offset_twist": offset["operation"]["twist"] == 2,
        "matched_loops_make_complete_quad_tubes": all(case["faces"] == SEGMENTS and case["quad_faces"] == SEGMENTS for case in (base, offset)),
        "open_rims_are_expected_and_bridge_edges_are_manifold": all(
            case["open_boundary_edges"] == SEGMENTS * 2
            and case["bridge_edges"] == SEGMENTS
            and case["non_manifold_bridge_edges"] == 0
            for case in (base, offset)
        ),
        "twist_changes_target_pairing": base["cross_loop_pairs"] != offset["cross_loop_pairs"],
    }
    report = {
        "lab": "typed_bridge_twist_control",
        "blender_version": bpy.app.version_string,
        "fixture": "two equal eight-vertex wire loops bridged through mesh_ops.bridge_selection",
        "api_signature": "bmesh.ops.bridge_loops(..., twist_offset=0)",
        "cases": {"twist_0": base, "twist_2": offset},
        "assertions": assertions,
        "boundary": "This proves target-pairing control for equal loops. It does not validate bridging unequal loops or repair the prior teapot handle automatically.",
        "pass": all(assertions.values()),
    }
    (OUT / "bridge_twist_control_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "bridge_twist_control.blend"))
    print("BRIDGE_TWIST_CONTROL_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
