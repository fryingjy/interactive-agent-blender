"""Prove typed assembly translation commits and rolls back object transforms."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from blender_ops.modeler_server import ModelerServer


OUT = ROOT / "runs" / "2026-08-16_object-transform-decision"
NAME = "TransformRollbackAssembly"


def location() -> list[float]:
    return [float(value) for value in bpy.data.objects[NAME].location]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()
    server.cmd_create_primitive(NAME, "cube", location=[1.0, 2.0, 3.0])
    before = location()

    rejected_decision = server.cmd_begin_decision(NAME, "transform_rollback_test")
    rejected_perform = server.cmd_perform_decision(
        rejected_decision["decision_id"], "translate_object", {"delta": [0.5, -1.0, 2.0]}, command_id="transform-lab-reject"
    )
    rejected_verify = server.cmd_verify_decision(rejected_decision["decision_id"])
    moved_location = location()
    rejected = server.cmd_reject_decision(rejected_decision["decision_id"], "controlled transform rollback")
    after_reject = location()

    committed_decision = server.cmd_begin_decision(NAME, "transform_commit_test")
    committed_perform = server.cmd_perform_decision(
        committed_decision["decision_id"], "translate_object", {"delta": [-0.25, 0.5, 0.0]}, command_id="transform-lab-commit"
    )
    committed_verify = server.cmd_verify_decision(committed_decision["decision_id"])
    committed = server.cmd_commit_decision(committed_decision["decision_id"])
    after_commit = location()

    checks = {
        "rejected_translation_performed": rejected_perform["performed"],
        "rejected_translation_changed_transform": moved_location != before,
        "reject_restored_exact_location": after_reject == before,
        "rejected_revision_unchanged": rejected["restored_revision"] == 0,
        "commit_translation_performed": committed_perform["performed"],
        "commit_advanced_revision_once": committed["result_revision"] == 1,
        "commit_persisted_location": after_commit == [0.75, 2.5, 3.0],
        "verification_preserves_mesh_health": rejected_verify["after"]["non_manifold_edges"] == 0 and committed_verify["after"]["non_manifold_edges"] == 0,
    }
    report = {
        "record_type": "OBJECT_TRANSFORM_DECISION_LAB",
        "checks": checks,
        "rejected": rejected,
        "committed": committed,
        "pass": all(checks.values()),
        "claim_boundary": "This validates transaction-owned object translation for independently manufactured assemblies. It does not prescribe object transforms for a connected primary cage.",
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
