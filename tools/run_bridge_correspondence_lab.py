"""Exercise typed bridge correspondence control, transfer, and failure rollback in Blender 5.2."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


from lab_common import add_repo_paths

ROOT, OPS = add_repo_paths(__file__)

import decision_state
import decision_transaction
import mesh_ops
import modeler_server
import persistent_ids
import render_passes
import state_fingerprint
import state_probe


OUT = ROOT / "runs" / "2026-08-15_bridge-correspondence-control"


def json_safe(value):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def shape_point(family: str, index: int, segments: int, z: float):
    angle = math.tau * index / segments
    if family == "circle":
        return (math.cos(angle), math.sin(angle), z)
    if family == "rounded_rectangle":
        cosine = math.cos(angle)
        sine = math.sin(angle)
        exponent = 0.42
        x = math.copysign(abs(cosine) ** exponent, cosine) * 1.35
        y = math.copysign(abs(sine) ** exponent, sine) * 0.72
        return (x, y, z)
    raise ValueError(f"unknown fixture family: {family}")


def make_fixture(name: str, family: str, lower_count: int, upper_count: int):
    vertices = []
    edges = []
    for index in range(lower_count):
        vertices.append(shape_point(family, index, lower_count, -0.8))
    for index in range(upper_count):
        vertices.append(shape_point(family, index, upper_count, 0.8))
    edges.extend((index, (index + 1) % lower_count) for index in range(lower_count))
    start = lower_count
    edges.extend(
        (start + index, start + (index + 1) % upper_count)
        for index in range(upper_count)
    )
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for edge in mesh.edges:
        edge.select = True
    obj["fixture_family"] = family
    obj["lower_loop_count"] = lower_count
    obj["upper_loop_count"] = upper_count
    return obj


def typed_bridge(server, obj, twist_offset):
    begun = server.cmd_begin_decision(obj.name, "BRIDGE_EDGE_LOOPS_WITH_MEASURED_CORRESPONDENCE")
    performed = server.cmd_perform_decision(
        begun["decision_id"],
        "bridge_selection",
        {"twist_offset": twist_offset},
        command_id=f"bridge-{obj.name}-{twist_offset}",
    )
    verified = server.cmd_verify_decision(begun["decision_id"])
    committed = server.cmd_commit_decision(begun["decision_id"])
    obj["applied_twist_offset"] = twist_offset
    return {"begin": begun, "perform": performed, "verify": verified, "commit": committed}


def run_family(server, family, segments, erroneous_twist):
    default = make_fixture(f"{family}_default", family, segments, segments)
    corrected = make_fixture(f"{family}_corrected", family, segments, segments)
    default_analysis = server.cmd_analyze_bridge_selection(default.name)
    corrected_analysis = server.cmd_analyze_bridge_selection(corrected.name)
    suggestion = corrected_analysis["suggested_twist_offset"]
    # Reproduce the correspondence failure deliberately, then apply the analyzer's
    # measured correction to an identical second fixture.
    default_tx = typed_bridge(server, default, erroneous_twist)
    corrected_tx = typed_bridge(server, corrected, suggestion)
    default["case_role"] = "default"
    corrected["case_role"] = "corrected"
    default["suggested_twist_offset"] = suggestion
    corrected["suggested_twist_offset"] = suggestion
    return {
        "family": family,
        "segments": segments,
        "erroneous_twist_offset": erroneous_twist,
        "default_analysis": default_analysis,
        "corrected_analysis": corrected_analysis,
        "suggested_twist_offset": suggestion,
        "default_transaction": default_tx,
        "corrected_transaction": corrected_tx,
    }


def unequal_guard(server):
    obj = make_fixture("unequal_10_12_guard", "circle", 10, 12)
    persistent_ids.ensure_persistent_ids(obj.name)
    before = {
        "health": state_probe.mesh_health(obj.name),
        "fingerprint": state_fingerprint.compute(obj.name),
        "mesh_datablocks": sorted(bpy.data.meshes.keys()),
        "revision": decision_state.current_revision(),
    }
    analysis_error = None
    try:
        server.cmd_analyze_bridge_selection(obj.name)
    except ValueError as exc:
        analysis_error = str(exc)
    begun = server.cmd_begin_decision(obj.name, "REJECT_UNEQUAL_BRIDGE_DENSITY")
    operation_error = None
    try:
        server.cmd_perform_decision(
            begun["decision_id"],
            "bridge_selection",
            {"twist_offset": 0},
            command_id="bridge-unequal-guard",
        )
    except ValueError as exc:
        operation_error = str(exc)
    abandoned = server.cmd_abandon_decision(
        begun["decision_id"], reason="unequal bridge loops require density correction"
    )
    after = {
        "health": state_probe.mesh_health(obj.name),
        "fingerprint": state_fingerprint.compute(obj.name),
        "mesh_datablocks": sorted(bpy.data.meshes.keys()),
        "revision": decision_state.current_revision(),
    }
    obj["case_role"] = "unequal_guard"
    return {
        "analysis_error": analysis_error,
        "operation_error": operation_error,
        "begin": begun,
        "abandon": abandoned,
        "before": before,
        "after": after,
    }


def partial_failure_rollback():
    obj = make_fixture("partial_failure_rollback", "circle", 8, 8)
    persistent_ids.ensure_persistent_ids(obj.name)
    before = {
        "fingerprint": state_fingerprint.compute(obj.name),
        "mesh_datablocks": sorted(bpy.data.meshes.keys()),
        "revision": decision_state.current_revision(),
    }

    def mutate_then_raise(name):
        target, bm = mesh_ops._bm_from_object(name)
        bm.verts.ensure_lookup_table()
        bm.verts[0].co.x += 4.0
        mesh_ops._write_back(target, bm)
        raise RuntimeError("deliberate failure after a real vertex mutation")

    tx = decision_transaction.decision_transaction(
        decision_state.current_revision(), "CONTROLLED_PARTIAL_FAILURE", target_object=obj.name
    )
    tx.__enter__()
    error = None
    try:
        tx.perform(mutate_then_raise, obj.name)
    except RuntimeError as exc:
        error = str(exc)
    after = {
        "fingerprint": state_fingerprint.compute(obj.name),
        "mesh_datablocks": sorted(bpy.data.meshes.keys()),
        "revision": decision_state.current_revision(),
    }
    obj["case_role"] = "partial_failure_rollback"
    return {
        "error": error,
        "failure_rolled_back": tx._failure_rolled_back,
        "before": before,
        "after": after,
    }


def render_evidence(families):
    artifacts = []
    for family in families:
        for role in ("default", "corrected"):
            name = f"{family['family']}_{role}"
            for pass_type in ("solid", "wireframe"):
                path = OUT / f"{name}_{pass_type}.png"
                result = render_passes.render_diagnostic_pass(
                    [name], str(path), pass_type=pass_type, view="isometric", resolution=512
                )
                artifacts.append({"object": name, "pass_type": pass_type, "path": str(path), "result": result})
    return artifacts


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = modeler_server.ModelerServer()
    capabilities = server.cmd_get_capabilities()

    families = [
        run_family(server, "circle", 8, 2),
        run_family(server, "rounded_rectangle", 12, 3),
    ]
    unequal = unequal_guard(server)
    partial = partial_failure_rollback()
    artifacts = render_evidence(families)

    assertions = {
        "protocol_bumped": capabilities["protocol_version"] == "0.3",
        "correspondence_capability_reported": "bridge_correspondence_analysis" in capabilities["capabilities"],
        "bridge_operation_registered": "bridge_selection" in capabilities["available_operations"],
        "both_families_correct_nonzero_error": all(
            item["erroneous_twist_offset"] != item["suggested_twist_offset"]
            and item["erroneous_twist_offset"] != 0
            for item in families
        ),
        "analysis_is_read_only": all(
            item["default_analysis"]["selection_mutated"] is False
            and item["corrected_analysis"]["selection_mutated"] is False
            for item in families
        ),
        "typed_transactions_created_expected_faces": all(
            item[f"{role}_transaction"]["perform"]["result"]["created_faces"] == item["segments"]
            for item in families for role in ("default", "corrected")
        ),
        "unequal_analysis_rejected": unequal["analysis_error"] is not None,
        "unequal_mutation_rejected": unequal["operation_error"] is not None,
        "failed_operation_auto_rollback_reported": unequal["abandon"]["failed_operation_rolled_back"] is True,
        "unequal_guard_preserved_state": unequal["before"] == unequal["after"],
        "partial_mutation_rolled_back": partial["failure_rolled_back"] is True,
        "partial_failure_preserved_state": partial["before"] == partial["after"],
        "diagnostic_renders_written": all(Path(item["path"]).exists() for item in artifacts),
    }
    report = {
        "lab": "typed_bridge_correspondence_control",
        "blender_version": bpy.app.version_string,
        "capabilities": capabilities,
        "families": families,
        "unequal_loop_guard": unequal,
        "partial_failure_rollback": partial,
        "artifacts": artifacts,
        "assertions": assertions,
        "limitations": [
            "Minimum connector length ranks correspondence candidates but does not prove an artistically correct surface.",
            "The transfer fixtures are controlled wire-loop shapes, not a held-out production prop.",
            "Unequal loop bridging remains available only through an explicit allow_unequal override and still requires topology review.",
        ],
        "pass": all(assertions.values()),
    }
    serialized = json_safe(report)
    (OUT / "bridge_correspondence_report.json").write_text(
        json.dumps(serialized, indent=2), encoding="utf-8"
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "bridge_correspondence.blend"))
    print("BRIDGE_CORRESPONDENCE_RESULT:" + json.dumps(serialized))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
