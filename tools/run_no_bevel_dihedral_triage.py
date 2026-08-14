"""Classify every mesh object with no Bevel modifier in the four passed held-out production
files as either legitimately flat (no edge above a low dihedral threshold, so a bevel would
be meaningless) or a genuine untreated sharp-edge gap. Read-only: opens each file, measures,
does not modify or re-save anything.
"""
import json
import math
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-12_shading-policy-retroactive-audit"

TARGETS = {
    "heldout_cc0_vintage_telephone_001": ROOT / "runs/2026-08-11_heldout-vintage-telephone/production/heldout_vintage_telephone_production.blend",
    "heldout_cc0_watering_can_001": ROOT / "runs/2026-08-11_heldout-watering-can/production/heldout_watering_can_production.blend",
}

FLAT_THRESHOLD_DEG = 1.0


def dihedral_stats(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.edges.ensure_lookup_table()
    max_angle = 0.0
    sharp_25 = 0
    total = 0
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        total += 1
        try:
            angle_deg = math.degrees(edge.calc_face_angle())
        except Exception:
            continue
        max_angle = max(max_angle, angle_deg)
        if angle_deg > 25:
            sharp_25 += 1
    bm.free()
    return {"edges_with_two_faces": total, "max_dihedral_deg": round(max_angle, 2), "edges_over_25deg": sharp_25}


def main():
    report = {}
    for label, path in TARGETS.items():
        bpy.ops.wm.open_mainfile(filepath=str(path))
        no_bevel_objs = []
        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue
            if any(modifier.type == "BEVEL" for modifier in obj.modifiers):
                continue
            stats = dihedral_stats(obj)
            stats["name"] = obj.name
            stats["vertex_count"] = len(obj.data.vertices)
            stats["classification"] = "LEGITIMATELY_FLAT" if stats["max_dihedral_deg"] < FLAT_THRESHOLD_DEG else "UNTREATED_SHARP_EDGE_GAP"
            no_bevel_objs.append(stats)
        report[label] = no_bevel_objs
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "no_bevel_triage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
