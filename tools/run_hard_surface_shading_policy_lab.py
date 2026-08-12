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
    }
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"blender_version": bpy.app.version_string, "shading": shading, "weights": weights, "transactions": {"weight": {"begin": weight_decision, "verify": weight_verify, "commit": weight_commit}, "shading": {"begin": shade_decision, "verify": shade_verify, "commit": shade_commit}}, "modifier_types": types, "weighted_edges": weighted, "assertions": assertions, "pass": all(assertions.values())}
    (OUT / "hard_surface_shading_policy_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "hard_surface_shading_policy.blend"))
    print(json.dumps(report))
    raise SystemExit(0 if report["pass"] else 2)

main()
