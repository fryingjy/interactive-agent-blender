"""Prove that editable curve decisions have the same scoped rollback boundary as meshes.

This is a runtime-infrastructure test, not a modeling-quality claim.  It uses a
Bezier U-path because a curve is the appropriate editable representation for
handles, shackles, and cables; all path changes are made through one-decision
transactions and checked against direct curve-control state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "blender_ops") not in sys.path:
    sys.path.insert(0, str(ROOT / "blender_ops"))

import curve_ops
import decision_state
import modeler_server
import state_probe
from decision_transaction import DecisionTransaction


OUT = ROOT / "runs" / "2026-08-16_curve-decision-transaction"


def controls(name: str) -> list[list[float]]:
    return state_probe.get_curve_state(name)["curve"]["splines"][0]["points"]


def changing_then_raising(name: str, points: list[list[float]]):
    curve_ops.set_curve_points(name, points)
    raise RuntimeError("intentional post-mutation failure")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    name = "EditableCurvePath"
    original = [[-2.0, 0.0, 0.0], [-2.0, 0.0, 3.0], [2.0, 0.0, 3.0], [2.0, 0.0, 0.0]]
    narrowed = [[-2.0, 0.0, 0.0], [-1.0, 0.0, 3.0], [1.0, 0.0, 3.0], [2.0, 0.0, 0.0]]
    curve_ops.create_curve_from_points(name, original, bevel_depth=0.15, curve_type="BEZIER")
    before = controls(name)
    revision = decision_state.current_revision()

    with DecisionTransaction(revision, "test_curve_reject", target_object=name) as tx:
        tx.perform(curve_ops.set_curve_points, name, narrowed)
        rejected_verification = tx.verify()
        rejected = tx.reject("narrower arch rejected by controlled test")
    after_reject = controls(name)

    revision = decision_state.current_revision()
    exception_rolled_back = False
    try:
        with DecisionTransaction(revision, "test_curve_failure_rollback", target_object=name) as tx:
            tx.perform(changing_then_raising, name, narrowed)
    except RuntimeError:
        exception_rolled_back = controls(name) == before

    with DecisionTransaction(revision, "test_curve_commit", target_object=name) as tx:
        tx.perform(curve_ops.set_curve_points, name, narrowed)
        committed_verification = tx.verify()
        committed_revision = tx.commit()
    after_commit = controls(name)

    # Exercise the actual typed server lifecycle too.  This is the path an
    # agent uses remotely; direct DecisionTransaction coverage alone would
    # not prove that the server's external-edit fingerprint accepts curves.
    server = modeler_server.ModelerServer()
    server_decision = server.cmd_begin_decision(name, "typed_curve_reject")
    server.cmd_perform_decision(
        server_decision["decision_id"], "set_curve_points", {"points": original},
        command_id="curve-lab-typed-reject",
    )
    server_verify = server.cmd_verify_decision(server_decision["decision_id"])
    server_reject = server.cmd_reject_decision(server_decision["decision_id"], "typed path rollback")
    after_server_reject = controls(name)

    checks = {
        "rejected_change_observed": rejected_verification["before"] != rejected_verification["after"],
        "curve_verification_has_no_mesh_ids": rejected_verification["id_delta"] is None,
        "reject_restored_control_points": after_reject == before,
        "exception_after_mutation_restored_control_points": exception_rolled_back,
        "commit_persists_control_points": after_commit == narrowed,
        "commit_advanced_revision_once": committed_revision == revision + 1,
        "curve_state_is_directly_reported": committed_verification["after"]["curve"]["splines"][0]["point_count"] == 4,
        "typed_server_accepts_curve_decision": server_verify["id_delta"] is None and server_reject["rejected"],
        "typed_server_reject_restores_controls": after_server_reject == narrowed,
    }
    report = {
        "record_type": "CURVE_DECISION_TRANSACTION_LAB",
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": "This proves transaction-owned curve-control rollback and verification. It does not prove a curve matches a reference or that its evaluated surface is artistically correct.",
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
