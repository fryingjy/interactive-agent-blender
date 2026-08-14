"""Structural check for whether a hard-surface object's weighted bevel edges form
discrete-angle rings (a real stepped seam -- the mechanical-plate/Opening_Rim
pattern) or a continuously drifting line (the sword/Rose_Head pattern this
session mistook for noise and had to revert). See the "What correct selection
actually looks like" section of knowledge/foundation/operator_cards/smooth_by_angle.md
for the live-artist-scene evidence this check is derived from.

This does not decide whether an object *should* have been corrected -- it only
reports the angle distribution so a human or a later pass can judge intent.
Read-only: opens files directly, never saves.

Known limitation, confirmed by running this against Connected_Vessel and
Main_Housing (the project's original, deliberately hand-refined WEIGHT-bevel
examples, not automated corrections): both trip CONTINUOUS_DRIFT_PATTERN
despite being correct. A lathed/revolved body's shoulder-to-neck profile is a
*legitimate* continuous design line, and it produces a wide, many-bucket angle
spread for the same structural reason the sword's tapering facet edge does.
Bucket count alone cannot distinguish "one correct continuous profile line"
from "many separately-wrong edges that happen to span a wide angle range" --
that still requires tracing whether the flagged edges form one connected path
or scattered noise, i.e. a human/reference check. Treat
CONTINUOUS_DRIFT_PATTERN as "look at this," never as "this is wrong."
"""
import json
import math
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]

TARGETS = {
    "heldout_cc0_watering_can_001": {
        "path": ROOT / "runs/2026-08-12_watering-can-final-bevel-corrective/heldout_watering_can_production_fully_corrected.blend",
        "objects": ["Opening_Rim", "Opening_Shadow", "Connected_Vessel"],
    },
    "heldout_cc0_vintage_telephone_001": {
        "path": ROOT / "runs/2026-08-12_telephone-trim-bevel-corrective/heldout_vintage_telephone_production_trim_corrected.blend",
        "objects": ["Clock_Face", "Lower_Panel_Trim", "Upper_Face_Trim", "Dial_Aperture", "Main_Housing"],
    },
}

DISCRETE_BUCKET_THRESHOLD = 5  # more distinct angle buckets than this suggests a continuous drift, not discrete rings


def weighted_edge_angles(obj):
    attr = obj.data.attributes.get("bevel_weight_edge")
    if attr is None:
        return []
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    angles = []
    for i, item in enumerate(attr.data):
        if item.value > 0.999 and i < len(bm.edges):
            e = bm.edges[i]
            if len(e.link_faces) == 2:
                try:
                    angles.append(round(math.degrees(e.calc_face_angle())))
                except Exception:
                    pass
    bm.free()
    return angles


def main():
    report = {}
    for label, spec in TARGETS.items():
        bpy.ops.wm.open_mainfile(filepath=str(spec["path"]))
        objects_report = {}
        for name in spec["objects"]:
            obj = bpy.data.objects.get(name)
            if obj is None:
                objects_report[name] = {"status": "OBJECT_NOT_FOUND"}
                continue
            angles = weighted_edge_angles(obj)
            distinct_buckets = sorted(set(angles))
            classification = "NO_WEIGHTED_EDGES" if not angles else (
                "DISCRETE_RING_PATTERN" if len(distinct_buckets) <= DISCRETE_BUCKET_THRESHOLD
                else "CONTINUOUS_DRIFT_PATTERN_REVIEW_NEEDED"
            )
            objects_report[name] = {
                "weighted_edge_count": len(angles),
                "distinct_angle_buckets_deg": distinct_buckets,
                "classification": classification,
            }
        report[label] = objects_report
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
