"""Fresh Blender audit of source pairs and fail-closed production controls."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_production-high-low-audit"
BLENDER_OPS = ROOT / "blender_ops"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BLENDER_OPS) not in sys.path:
    sys.path.insert(0, str(BLENDER_OPS))

import object_ops
from knowledge_engine.high_low_audit import HighLowEvidence, audit_production_high_low


def evidence_from_result(result: dict) -> HighLowEvidence:
    item = result["evidence"]
    uv = item["low_uv"]
    return HighLowEvidence(
        high_object=item["high_object"],
        low_object=item["low_object"],
        separate_collections=result["checks"]["separate_collections"],
        independent_mesh_datablocks=item["independent_mesh_datablocks"],
        high_base_faces=item["high_base_faces"],
        low_base_faces=item["low_base_faces"],
        high_connected_components=item["high_connected_components"],
        low_connected_components=item["low_connected_components"],
        high_live_modifiers=tuple(item["high_live_modifiers"]),
        low_live_modifiers=tuple(item["low_live_modifiers"]),
        low_uv_layer=uv["layer"],
        low_uv_loop_count=uv["loop_count"],
        low_degenerate_uv_faces=uv["degenerate_faces"],
        low_uv_inside_unit_tile=uv["inside_unit_tile"],
        silhouette_iou_by_view=item["silhouette_iou_by_view"],
    )


def main() -> None:
    contract = json.loads((OUT / "experiment_contract.json").read_text(encoding="utf-8"))
    scores = json.loads((OUT / "silhouette_scores.json").read_text(encoding="utf-8"))["scores"]
    build = json.loads((OUT / "build_report.json").read_text(encoding="utf-8"))
    audits = {
        family: object_ops.production_high_low_audit(
            pair["high"],
            pair["low"],
            scores[family],
            max_low_to_high_face_ratio=contract["frozen_gates"]["max_low_to_high_base_face_ratio"],
            minimum_silhouette_iou=contract["frozen_gates"]["minimum_silhouette_iou"],
            minimum_view_count=contract["frozen_gates"]["minimum_view_count"],
            require_live_modifiers=True,
        )
        for family, pair in build["pairs"].items()
    }
    equal = object_ops.production_high_low_audit(
        build["equal_cage_control"]["high"],
        build["equal_cage_control"]["low"],
        {"front": 1.0, "side": 1.0, "top": 1.0},
        high_collection_name="EQUAL_HIGH",
        low_collection_name="EQUAL_LOW",
        require_live_modifiers=True,
    )
    baseline = evidence_from_result(audits["box"])
    controls = {
        "one_view_only": audit_production_high_low(
            replace(baseline, silhouette_iou_by_view={"front": 0.99})
        ),
        "missing_uv": audit_production_high_low(
            replace(baseline, low_uv_layer=None, low_uv_loop_count=0)
        ),
        "missing_live_low_modifier": audit_production_high_low(
            replace(baseline, low_live_modifiers=())
        ),
        "disconnected_low_shells": audit_production_high_low(
            replace(baseline, low_connected_components=2)
        ),
    }
    image_checks = {}
    for family, bake in build["bakes"].items():
        image = bpy.data.images.get(f"{family}_Tangent_Normal")
        low = bpy.data.objects[build["pairs"][family]["low"]]
        material = low.data.materials[0] if low.data.materials else None
        normal_nodes = [node for node in material.node_tree.nodes if node.type == "NORMAL_MAP"] if material else []
        image_checks[family] = {
            "packed": bool(image and image.packed_file),
            "non_color": bool(image and image.colorspace_settings.name == "Non-Color"),
            "normal_node_connected": bool(
                normal_nodes and normal_nodes[0].outputs["Normal"].is_linked
            ),
            "non_neutral_pixels": bake["metrics"]["non_neutral_pixels"],
        }
    build_script = (ROOT / "tools" / "run_production_high_low_audit_lab.py").read_text(
        encoding="utf-8"
    )
    checks = {
        "build_script_has_no_modifier_apply_call": "modifier_apply(" not in build_script,
        "export_explicitly_preserves_modifier_stack": "export_apply=False" in build_script,
        "scene_declares_no_pipeline_modifier_application": (
            bpy.context.scene.get("pipeline_applied_modifiers") is False
        ),
        "box_production_audit_passes": audits["box"]["pass"] is True,
        "radial_production_audit_passes": audits["radial"]["pass"] is True,
        "equal_cage_is_not_retopology": (
            equal["disposition"] == contract["frozen_gates"]["equal_cage_control_disposition"]
        ),
        "one_view_control_fails": not controls["one_view_only"]["pass"],
        "missing_uv_control_fails": not controls["missing_uv"]["pass"],
        "missing_modifier_control_fails": not controls["missing_live_low_modifier"]["pass"],
        "disconnected_shell_control_fails": not controls["disconnected_low_shells"]["pass"],
        "both_bakes_packed_non_color_and_connected": all(
            item["packed"] and item["non_color"] and item["normal_node_connected"]
            and item["non_neutral_pixels"] >= contract["frozen_gates"]["normal_bake_non_neutral_pixels_min"]
            for item in image_checks.values()
        ),
        "all_source_objects_keep_live_modifiers": all(
            len(bpy.data.objects[name].modifiers) >= 1
            for pair in build["pairs"].values() for name in pair.values()
        ),
        "all_source_objects_mark_manual_application_policy": all(
            bpy.data.objects[name].get("modifier_application_policy") == "LEAVE_UNAPPLIED_FOR_USER"
            for pair in build["pairs"].values() for name in pair.values()
        ),
    }
    report = {
        "blender_version": bpy.app.version_string,
        "blend_file": bpy.data.filepath,
        "audits": audits,
        "equal_cage_control": equal,
        "negative_controls": controls,
        "image_checks": image_checks,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": contract["claim_boundary"],
    }
    (OUT / "fresh_source_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"checks": checks, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
