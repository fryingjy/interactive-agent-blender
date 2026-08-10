"""Compare surface diagnostics on clean, locally pinched, and oscillating shapes."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender_ops.evaluated_probe import evaluated_surface_diagnostics


def sphere_pair():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(-2, 0, 0))
    clean = bpy.context.object
    clean.name = "Surface_CleanSphere"
    pinched = clean.copy()
    pinched.data = clean.data.copy()
    pinched.name = "Surface_PinchedSphere"
    pinched.location.x = 0
    bpy.context.scene.collection.objects.link(pinched)
    candidates = [v for v in pinched.data.vertices if abs(v.co.z) < 0.15]
    target = max(candidates, key=lambda v: v.co.x)
    target.co *= 1.4
    for obj in (clean, pinched):
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return clean, pinched


def ring_surface(name, location_x, amplitude):
    segments, rings = 24, 11
    verts = []
    faces = []
    for ring in range(rings):
        z = -1.5 + 3.0 * ring / (rings - 1)
        radius = 1.0 + amplitude * ((-1) ** ring)
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    for ring in range(rings - 1):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            a = ring * segments + segment
            b = ring * segments + nxt
            c = (ring + 1) * segments + nxt
            d = (ring + 1) * segments + segment
            faces.append((a, b, c, d))
    bottom = len(verts); verts.append((0, 0, -1.5))
    top = len(verts); verts.append((0, 0, 1.5))
    for segment in range(segments):
        nxt = (segment + 1) % segments
        faces.append((bottom, nxt, segment))
        a = (rings - 1) * segments + segment
        b = (rings - 1) * segments + nxt
        faces.append((top, a, b))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location.x = location_x
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def main():
    out = ROOT / "runs" / "2026-08-10_surface-diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    clean, pinched = sphere_pair()
    uniform = ring_surface("Surface_UniformCylinder", 2.0, 0.0)
    wavy = ring_surface("Surface_WavyCylinder", 4.5, 0.10)
    results = {obj.name: evaluated_surface_diagnostics(obj.name) for obj in (clean, pinched, uniform, wavy)}
    assertions = {
        "pinch_outlier_stronger_than_clean": results[pinched.name]["max_robust_outlier_z"] > results[clean.name]["max_robust_outlier_z"] * 1.5,
        "pinch_candidate_count_increases": results[pinched.name]["pinch_candidate_count"] > results[clean.name]["pinch_candidate_count"],
        "wavy_sign_changes_exceed_uniform": results[wavy.name]["laplacian_sign_change_ratio"] > results[uniform.name]["laplacian_sign_change_ratio"] + 0.2,
        "all_labeled_candidate_only": all(item["classification"] == "CANDIDATE_EVIDENCE_ONLY" for item in results.values()),
    }
    report = {"lab": "evaluated_surface_concentration_and_oscillation", "results": results, "assertions": assertions, "pass": all(assertions.values())}
    (out / "surface_diagnostics_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "surface_diagnostics_lab.blend"))
    print("SURFACE_DIAGNOSTICS_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
