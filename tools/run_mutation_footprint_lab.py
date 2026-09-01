"""Controlled Blender proof for persistent-ID localized mutation enforcement."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import decision_state
import persistent_ids
from decision_transaction import DecisionTransaction, TransactionError

OUT = ROOT / "runs" / "2026-09-01_mutation-footprint-lab"
NAME = "MutationFootprintFixture"


def create_fixture():
    mesh = bpy.data.meshes.new(NAME + "Mesh")
    mesh.from_pydata(
        [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
         (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
        [],
        [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
         (2, 6, 7, 3), (4, 0, 3, 7)],
    )
    mesh.update()
    obj = bpy.data.objects.new(NAME, mesh)
    bpy.context.scene.collection.objects.link(obj)
    persistent_ids.ensure_persistent_ids(NAME)
    return obj


def move_vertex_by_id(vertex_id, delta_x):
    obj = bpy.data.objects[NAME]
    index = persistent_ids.get_id_maps(NAME)["verts"]["id_to_index"][int(vertex_id)]
    obj.data.vertices[index].co.x += float(delta_x)
    obj.data.update()
    return {"vertex_id": int(vertex_id), "delta_x": float(delta_x)}


def position(vertex_id):
    return persistent_ids.vertex_positions_by_id(NAME)[int(vertex_id)]


def delete_vertex_by_id(vertex_id):
    obj = bpy.data.objects[NAME]
    index = persistent_ids.get_id_maps(NAME)["verts"]["id_to_index"][int(vertex_id)]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[index]], context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return {"vertex_id": int(vertex_id)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    create_fixture()
    vertex_ids = sorted(persistent_ids.get_id_maps(NAME)["verts"]["id_to_index"])
    allowed_id, protected_id = vertex_ids[:2]

    with DecisionTransaction(
        decision_state.current_revision(), "allowed_local_move", NAME, [allowed_id]
    ) as tx:
        tx.perform(move_vertex_by_id, allowed_id, 0.25)
        allowed_verify = tx.verify()
        allowed_revision = tx.commit()

    protected_before = position(protected_id)
    blocked = False
    with DecisionTransaction(
        decision_state.current_revision(), "blocked_protected_move", NAME, [allowed_id]
    ) as tx:
        tx.perform(move_vertex_by_id, protected_id, 0.5)
        blocked_verify = tx.verify()
        try:
            tx.commit()
        except TransactionError:
            blocked = True
            tx.reject("controlled protected-region violation")
    protected_after = position(protected_id)

    delete_before = position(protected_id)
    delete_blocked = False
    with DecisionTransaction(
        decision_state.current_revision(), "blocked_protected_delete", NAME, [allowed_id]
    ) as tx:
        tx.perform(delete_vertex_by_id, protected_id)
        delete_verify = tx.verify()
        try:
            tx.commit()
        except TransactionError:
            delete_blocked = True
            tx.reject("controlled protected-vertex deletion")
    delete_after = position(protected_id)

    checks = {
        "allowed_move_passed": allowed_verify["mutation_footprint"]["pass"],
        "allowed_move_committed": allowed_revision == 1,
        "protected_move_detected": blocked_verify["mutation_footprint"]["unexpected_moved_vertex_ids"] == [protected_id],
        "protected_commit_blocked": blocked,
        "protected_move_rolled_back": protected_after == protected_before,
        "protected_delete_detected": delete_verify["mutation_footprint"]["unexpected_removed_vertex_ids"] == [protected_id],
        "protected_delete_commit_blocked": delete_blocked,
        "protected_delete_rolled_back": delete_after == delete_before,
        "blocked_commit_did_not_advance_revision": decision_state.current_revision() == 1,
    }
    report = {
        "schema_version": 1,
        "record_type": "MUTATION_FOOTPRINT_LAB",
        "scope": "SYSTEM_VALIDATION_FIXTURE",
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": "Proves commit blocking and rollback for moved or deleted protected persistent vertices. It does not prove visual quality or topology strategy.",
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
