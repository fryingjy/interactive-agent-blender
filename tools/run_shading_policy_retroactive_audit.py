"""Retroactively audit already-published held-out production .blend files against the
hard-surface shading policy (get_hard_surface_shading_audit), which did not exist when
those files were built. This does not modify or re-save the source files; it opens each
one read-only, runs the audit on every mesh object, and records the honest result.
"""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))

import object_ops  # noqa: E402

TARGETS = {
    "heldout_cc0_camera_001": ROOT / "runs/2026-08-11_connected-camera-corrective/connected_camera_corrective.blend",
    "heldout_cc0_vintage_telephone_001": ROOT / "runs/2026-08-11_heldout-vintage-telephone/production/heldout_vintage_telephone_production.blend",
    "heldout_cc0_watering_can_001": ROOT / "runs/2026-08-11_heldout-watering-can/production/heldout_watering_can_production.blend",
}

OUT = ROOT / "runs" / "2026-08-12_shading-policy-retroactive-audit"


def audit_file(label, path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    results = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        try:
            results[obj.name] = object_ops.hard_surface_shading_audit(obj.name)
        except Exception as exc:  # noqa: BLE001 - record the failure, do not hide it
            results[obj.name] = {"name": obj.name, "status": "AUDIT_ERROR", "error": str(exc)}
    any_pass = any(r.get("status") == "PASS" for r in results.values())
    return {
        "label": label,
        "source_file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "mesh_object_count": len(results),
        "objects": results,
        "any_object_passes_policy": any_pass,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"blender_version": bpy.app.version_string, "targets": {}}
    for label, path in TARGETS.items():
        if not path.exists():
            report["targets"][label] = {"label": label, "status": "SOURCE_FILE_MISSING", "source_file": str(path)}
            continue
        report["targets"][label] = audit_file(label, path)
    (OUT / "retroactive_audit_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
