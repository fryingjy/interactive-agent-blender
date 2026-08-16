"""Fresh-process verification for the reference-image alignment transfer scene."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-16_reference-image-alignment-transfer"
if str(ROOT / "blender_ops") not in sys.path:
    sys.path.insert(0, str(ROOT / "blender_ops"))

import object_ops


def main():
    report = json.loads((OUT / "reference_image_alignment_transfer_report.json").read_text(encoding="utf-8"))
    audits = {
        "perspective_failure": object_ops.audit_reference_images("PERSPECTIVE_FAILURE_CONTROL"),
        "orthographic_reproduction": object_ops.audit_reference_images("ORTHOGRAPHIC_REPRODUCTION"),
        "multiview_transfer": object_ops.audit_reference_images(
            "MULTIVIEW_TRANSFER", require_distinct_sources=True
        ),
        "duplicated_single_image_control": object_ops.audit_reference_images(
            "DUPLICATED_SINGLE_IMAGE_CONTROL", require_distinct_sources=True
        ),
    }
    reference_objects = [obj for obj in bpy.data.objects if "reference_view_axis" in obj]
    checks = {
        "saved_report_passed": report.get("pass") is True,
        "six_reference_empties_present": len(reference_objects) == 6,
        "all_images_loaded_from_existing_paths": all(
            obj.data is not None and Path(obj["reference_source_path"]).is_file()
            for obj in reference_objects
        ),
        "perspective_control_still_rejected": not audits["perspective_failure"]["pass"],
        "orthographic_reproduction_still_passes": audits["orthographic_reproduction"]["pass"],
        "multiview_transfer_still_passes": audits["multiview_transfer"]["pass"],
        "duplicate_source_control_still_rejected": not audits["duplicated_single_image_control"]["pass"],
        "front_and_right_transfer_sources_are_distinct": len(
            {obj["reference_source_path"] for obj in reference_objects if obj.name.startswith("Transfer_")}
        ) == 2,
        "all_principal_transfer_errors_zero": all(
            abs(record["angular_error_degrees"]) < 1e-7
            for key in ("orthographic_reproduction", "multiview_transfer")
            for record in audits[key]["records"]
        ),
    }
    result = {
        "blend_file": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "checks": checks,
        "audits": audits,
        "pass": all(checks.values()),
        "claim_boundary": report["claim_boundary"],
    }
    (OUT / "fresh_verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
