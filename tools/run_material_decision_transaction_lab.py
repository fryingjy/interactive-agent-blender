"""Prove selected-face material assignment is contained by a decision rollback."""

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


OUT = ROOT / "runs" / "2026-08-16_material-decision-transaction"
NAME = "MaterialRollbackPanel"
MATERIAL = "Lab_Fascia_Red"


def first_face_id(server: ModelerServer) -> int:
    geometry = server.cmd_get_mesh_geometry(NAME)
    return int(geometry["faces"][0]["agent_id"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()
    server.cmd_create_primitive(NAME, "cube")
    face_id = first_face_id(server)
    server.cmd_select_by_ids(NAME, face_ids=[face_id])

    rejected_decision = server.cmd_begin_decision(NAME, "material_rollback_test")
    rejected_perform = server.cmd_perform_decision(
        rejected_decision["decision_id"],
        "assign_selected_material",
        {"material_name": MATERIAL, "color": [0.55, 0.01, 0.02, 1.0], "metallic": 0.0, "roughness": 0.27},
        command_id="material-lab-reject",
    )
    rejected_verify = server.cmd_verify_decision(rejected_decision["decision_id"])
    rejected = server.cmd_reject_decision(rejected_decision["decision_id"], "controlled material rollback")
    object_after_reject = bpy.data.objects[NAME]
    reject_restored_slots = len(object_after_reject.data.materials) == 0
    reject_removed_material = MATERIAL in rejected["removed_created_materials"] and MATERIAL not in bpy.data.materials

    server.cmd_select_by_ids(NAME, face_ids=[face_id])
    committed_decision = server.cmd_begin_decision(NAME, "material_commit_test")
    committed_perform = server.cmd_perform_decision(
        committed_decision["decision_id"],
        "assign_selected_material",
        {"material_name": MATERIAL, "color": [0.55, 0.01, 0.02, 1.0], "metallic": 0.0, "roughness": 0.27},
        command_id="material-lab-commit",
    )
    committed_verify = server.cmd_verify_decision(committed_decision["decision_id"])
    committed_revision = server.cmd_commit_decision(committed_decision["decision_id"])
    object_after_commit = bpy.data.objects[NAME]

    checks = {
        "rejected_assignment_was_performed": rejected_perform["performed"],
        "reject_restored_material_slots": reject_restored_slots,
        "reject_removed_created_material": reject_removed_material,
        "commit_assignment_was_performed": committed_perform["performed"],
        "commit_persists_one_material_slot": len(object_after_commit.data.materials) == 1 and object_after_commit.data.materials[0].name == MATERIAL,
        "commit_advanced_revision_once": committed_revision["result_revision"] == 1,
        "verification_retains_mesh_health": rejected_verify["after"]["non_manifold_edges"] == 0 and committed_verify["after"]["non_manifold_edges"] == 0,
    }
    report = {
        "record_type": "MATERIAL_DECISION_TRANSACTION_LAB",
        "checks": checks,
        "rejected": rejected,
        "committed_revision": committed_revision,
        "pass": all(checks.values()),
        "claim_boundary": "This proves selected-face material assignment creates no leftover material on rejection and persists on commit. It does not prove color matching or artistic material quality.",
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
