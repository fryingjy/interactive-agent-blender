"""Verify semantic weighted bevel + Smooth by Angle in Blender 5.2."""
from __future__ import annotations
import json, sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
import persistent_ids
from modeler_server import _OPS
from modeler_server import ModelerServer
from object_ops import hard_surface_shading_audit

OUT = ROOT / "runs" / "2026-08-12_hard-surface-shading-policy"

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=2)
    obj = bpy.context.object
    obj.name = "Semantic_Hard_Surface_Box"
    # Four vertical corner rails are semantically sharp; coplanar/internal
    # edges are intentionally not treated as bevel targets.
    persistent_ids.ensure_persistent_ids(obj.name)
    edge_map = persistent_ids.get_id_maps(obj.name)["edges"]["index_to_id"]
    weighted = []
    for edge in obj.data.edges:
        vertices = [obj.data.vertices[index].co for index in edge.vertices]
        if abs(vertices[0].z - vertices[1].z) > 1.9:
            weighted.append(edge_map[edge.index])
    # Fixture setup is complete before the runtime first observes the object.
    # Adding modifiers after a committed decision would rightly be treated as
    # an external edit unless it too ran through its own typed decision.
    bevel = obj.modifiers.new("Semantic weighted edge radius", "BEVEL")
    bevel.limit_method = "WEIGHT"; bevel.width = 0.08; bevel.segments = 2
    subd = obj.modifiers.new("Curvature only where required", "SUBSURF")
    subd.levels = subd.render_levels = 1
    # Exercise the real typed decision route rather than only the helper:
    # one semantic weighting decision, then a separate normal-policy decision.
    server = ModelerServer()
    weight_decision = server.cmd_begin_decision(obj.name, "semantic_bevel_weight")
    weight_perform = server.cmd_perform_decision(
        weight_decision["decision_id"], "set_bevel_weight_by_ids",
        {"edge_ids": weighted, "weight": 1.0, "clear_others": True},
        command_id="hard_surface_weight_001",
    )
    weight_verify = server.cmd_verify_decision(weight_decision["decision_id"])
    weight_commit = server.cmd_commit_decision(weight_decision["decision_id"])
    weights = weight_perform["result"]
    shade_decision = server.cmd_begin_decision(obj.name, "smooth_by_angle")
    shade_perform = server.cmd_perform_decision(
        shade_decision["decision_id"], "set_smooth_by_angle",
        {"angle": 0.5235987756, "keep_sharp_edges": True},
        command_id="hard_surface_shading_001",
    )
    shade_verify = server.cmd_verify_decision(shade_decision["decision_id"])
    shade_commit = server.cmd_commit_decision(shade_decision["decision_id"])
    shading = shade_perform["result"]
    audit = hard_surface_shading_audit(obj.name)
    bpy.ops.mesh.primitive_cube_add(location=(4.0, 0.0, 0.0))
    rejected = bpy.context.object
    rejected.name = "Unannotated_Blanket_Smooth_Box"
    rejected.scale = (1.0, 1.0, 1.5)
    for polygon in rejected.data.polygons:
        polygon.use_smooth = True
    rejected_audit = hard_surface_shading_audit(rejected.name)
    # A third fixture reproducing the retroactively-audited boombox pattern: a real,
    # named ANGLE-limited Bevel (not absent, not blanket-smooth) with no recorded
    # semantic edge-ID intent. The audit must distinguish this from "no bevel at all".
    bpy.ops.mesh.primitive_cube_add(location=(-4.0, 0.0, 0.0))
    angle_scoped = bpy.context.object
    angle_scoped.name = "Angle_Scoped_No_Semantic_Intent_Box"
    angle_bevel = angle_scoped.modifiers.new("Purposeful edge radius", "BEVEL")
    angle_bevel.limit_method = "ANGLE"; angle_bevel.angle_limit = 0.5235987756; angle_bevel.width = 0.05
    angle_scoped_audit = hard_surface_shading_audit(angle_scoped.name)
    # A fourth fixture proves the new ANGLE intent-recording path (set_bevel_scoping)
    # reaches PASS through the real typed decision lifecycle, while the third
    # fixture above (raw bpy modifier assignment, no set_bevel_scoping call) must
    # keep failing -- this mechanism never retroactively grants intent.
    bpy.ops.mesh.primitive_cube_add(location=(8.0, 0.0, 0.0))
    angle_intent = bpy.context.object
    angle_intent.name = "Angle_Scoped_With_Recorded_Intent_Box"
    angle_intent_decision = server.cmd_begin_decision(angle_intent.name, "record_angle_bevel_scoping")
    server.cmd_perform_decision(
        angle_intent_decision["decision_id"], "set_bevel_scoping",
        {"method": "ANGLE", "angle_deg": 45.0, "width": 0.05, "segments": 2},
        command_id="hard_surface_angle_scoping_001",
    )
    angle_intent_verify = server.cmd_verify_decision(angle_intent_decision["decision_id"])
    angle_intent_commit = server.cmd_commit_decision(angle_intent_decision["decision_id"])
    shade_intent_decision = server.cmd_begin_decision(angle_intent.name, "smooth_by_angle")
    server.cmd_perform_decision(
        shade_intent_decision["decision_id"], "set_smooth_by_angle",
        {"angle": 0.5235987756, "keep_sharp_edges": True},
        command_id="hard_surface_angle_scoping_shading_001",
    )
    server.cmd_verify_decision(shade_intent_decision["decision_id"])
    server.cmd_commit_decision(shade_intent_decision["decision_id"])
    angle_intent_audit = hard_surface_shading_audit(angle_intent.name)
    # Current UI path: Shade Auto Smooth must create a live Smooth by Angle node
    # modifier, not merely set blanket polygon smoothing. Keep this fixture separate
    # from the typed `shade_smooth_by_angle` path above because both are legitimate
    # Blender 5.2 entry points with different sharp-edge preservation controls.
    bpy.ops.mesh.primitive_cube_add(location=(12.0, 0.0, 0.0))
    auto_smooth = bpy.context.object
    auto_smooth.name = "Shade_Auto_Smooth_Current_UI_Box"
    bpy.ops.object.shade_auto_smooth(use_auto_smooth=True, angle=0.5235987756)
    auto_smooth_modifiers = list(auto_smooth.modifiers)
    types = [modifier.type for modifier in obj.modifiers]
    assertions = {
        "smooth_by_angle_operator_finished": shading["shading"] == "SMOOTH_BY_ANGLE",
        "semantic_weight_count_is_four": len(weighted) == 4,
        "typed_semantic_weight_assignment": weights["assigned_edge_ids"] == weighted and not weights["missing_edge_ids"],
        "typed_operations_registered": all(key in _OPS for key in ("set_bevel_weight_by_ids", "set_smooth_by_angle")),
        "weight_decision_committed": weight_commit["result_revision"] == weight_decision["observed_revision"] + 1,
        "shading_decision_committed": shade_commit["result_revision"] == shade_decision["observed_revision"] + 1,
        "transaction_verification_observed": weight_verify["after"] is not None and shade_verify["after"] is not None,
        "weighted_bevel_precedes_subd": types[:2] == ["BEVEL", "SUBSURF"],
        "shading_policy_recorded": obj.get("shading_policy") == "SMOOTH_BY_ANGLE",
        "blanket_smooth_not_used_as_policy": obj.get("shading_policy") != "BLANKET_SMOOTH",
        "hard_surface_policy_audit_passes": audit["status"] == "PASS",
        "audit_rejects_unannotated_blanket_smooth": (
            rejected_audit["status"] == "REVIEW_REQUIRED"
            and not rejected_audit["checks"]["semantic_intent_recorded"]
            and not rejected_audit["checks"]["uniform_object_scale"]
            and not rejected_audit["checks"]["not_unannotated_blanket_smooth"]
        ),
        "audit_distinguishes_angle_scoping_from_no_bevel": (
            angle_scoped_audit["status"] == "REVIEW_REQUIRED"
            and angle_scoped_audit["bevel_limit_methods_present"] == ["ANGLE"]
            and not angle_scoped_audit["checks"]["semantic_intent_recorded"]
            and "ANGLE-limited Bevel" in " ".join(angle_scoped_audit["warnings"])
        ),
        "unrecorded_angle_bevel_still_review_required": (
            not angle_scoped_audit["checks"]["angle_or_vgroup_intent_recorded"]
        ),
        "recorded_angle_intent_reaches_pass": angle_intent_audit["status"] == "PASS",
        "recorded_angle_intent_matches_actual_modifier": angle_intent_audit["checks"]["angle_or_vgroup_intent_matches_actual"],
        "angle_intent_decision_committed": angle_intent_commit["result_revision"] == angle_intent_decision["observed_revision"] + 1,
        "angle_intent_transaction_verified": angle_intent_verify["after"] is not None,
        "shade_auto_smooth_creates_live_smooth_by_angle_modifier": (
            bool(auto_smooth_modifiers)
            and auto_smooth_modifiers[-1].type == "NODES"
            and auto_smooth_modifiers[-1].show_viewport
            and auto_smooth_modifiers[-1].show_render
            and "smooth by angle" in auto_smooth_modifiers[-1].name.casefold()
        ),
        "shade_auto_smooth_marks_faces_smooth": all(poly.use_smooth for poly in auto_smooth.data.polygons),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"blender_version": bpy.app.version_string, "shading": shading, "weights": weights, "hard_surface_audit": audit, "rejected_fixture_audit": rejected_audit, "angle_scoped_fixture_audit": angle_scoped_audit, "angle_intent_fixture_audit": angle_intent_audit, "auto_smooth_ui_fixture": {"object": auto_smooth.name, "modifiers": [{"name": modifier.name, "type": modifier.type, "show_viewport": modifier.show_viewport, "show_render": modifier.show_render} for modifier in auto_smooth_modifiers], "all_faces_smooth": all(poly.use_smooth for poly in auto_smooth.data.polygons)}, "transactions": {"weight": {"begin": weight_decision, "verify": weight_verify, "commit": weight_commit}, "shading": {"begin": shade_decision, "verify": shade_verify, "commit": shade_commit}, "angle_scoping": {"begin": angle_intent_decision, "verify": angle_intent_verify, "commit": angle_intent_commit}}, "modifier_types": types, "weighted_edges": weighted, "assertions": assertions, "pass": all(assertions.values())}
    (OUT / "hard_surface_shading_policy_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "hard_surface_shading_policy.blend"))
    print(json.dumps(report))
    raise SystemExit(0 if report["pass"] else 2)

main()
