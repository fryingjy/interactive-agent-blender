"""Use the verified inset-before-extrude-containment skill through retrieval, planning, and
one typed runtime decision, following the exact established pattern
(run_loopcut_skill_runtime_use.py, run_bevel_parity_skill_runtime_use.py) -- headless,
ModelerServer in-process, not dependent on the live socket bridge.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path: sys.path.insert(0, str(path))

from blender_ops import persistent_ids, state_probe
from blender_ops.modeler_server import ModelerServer
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore

RUN = ROOT / "runs" / "2026-08-18_inset-containment-skill-runtime-use"
SKILL_ID = "extrude.inset_first.local_containment"
NAME = "RuntimeCoarseBody"


def build_coarse_cylinder(name, *, radius=1.0, far=-2.5, near=1.3, segments=16, bands=3):
    bm = bmesh.new()
    rings = []
    for row in range(bands + 1):
        t = row / bands
        z = far + (near - far) * t
        ring = [bm.verts.new((radius * math.cos(2.0 * math.pi * s / segments),
                               radius * math.sin(2.0 * math.pi * s / segments), z))
                for s in range(segments)]
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for row in range(bands):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            bm.faces.new((rings[row][segment], rings[row][nxt], rings[row + 1][nxt], rings[row + 1][segment]))
    bm.faces.new(reversed(rings[0]))
    bm.normal_update()
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh); bm.free(); mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def mid_band_front_face_id():
    obj = bpy.data.objects[NAME]
    persistent_ids.ensure_persistent_ids(NAME)
    maps = persistent_ids.get_id_maps(NAME)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
    mid_faces = [f for f in bm.faces if len(f.verts) == 4 and -1.0 < f.calc_center_median().z < 0.6]
    target = max(mid_faces, key=lambda f: f.calc_center_median().x)
    face_id = maps["faces"]["index_to_id"][target.index]
    bm.free()
    return face_id


def open_collar_boundary_edge_ids():
    """The near-collar ring is deliberately open (matching the live-validated spout
    construction, a body awaiting a later join) -- these boundary edges are intentional,
    not a defect, and must be declared to the planner as such."""
    obj = bpy.data.objects[NAME]
    maps = persistent_ids.get_id_maps(NAME)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.edges.ensure_lookup_table()
    ids = tuple(sorted(maps["edges"]["index_to_id"][e.index] for e in bm.edges if e.is_boundary))
    bm.free()
    return ids


def mesh_metrics(obj_name):
    obj = bpy.data.objects[obj_name]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new(); bm.from_mesh(mesh)
        try:
            face_sizes = [len(f.verts) for f in bm.faces]
            return {
                "faces": len(bm.faces),
                "triangles": sum(1 for s in face_sizes if s == 3),
                "non_manifold_edges": sum(not e.is_manifold for e in bm.edges),
            }
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()
    body = build_coarse_cylinder(NAME)
    face_id = mid_band_front_face_id()
    intentional_boundary_ids = open_collar_boundary_edge_ids()

    store = StructuredSkillStore(ROOT / "knowledge" / "skills")
    query = RetrievalContext(
        query="extruding a local bump on a coarse curved body without it drooping into the surrounding surface",
        modeling_stage="SECONDARY_FORMS",
        workflow="extrude",
        surface_type="hard-surface",
        defect="feature spreads unevenly into surrounding surface",
        local_topology=["single-or-few-face-region-becoming-a-raised-or-attached-feature"],
        modifiers=["SUBSURF"],
        blender_version="5.2",
    )
    retrieved = store.search(query, top_k=5)

    ticket = {
        "type": "local_feature_extrusion_on_coarse_surface",
        "target": "body_front_boss",
        "priority": 1,
        "severity": 0.6,
        "operation_params": {"thickness": 0.12, "depth": 0.0},
    }

    decision = plan_next_decision(
        PlannerContext(
            task_id="inset-containment-skill-runtime-use",
            asset_id="runtime-coarse-body",
            stage="SECONDARY_FORMS",
            session_id=server.session_id,
            scene_revision=0,
            active_object=NAME,
            base_state={"mesh_health": state_probe.mesh_health(NAME)},
            evaluated_state={"mesh_health": state_probe.mesh_health(NAME)},
            visual_tickets=[ticket],
            retrieved_skills=retrieved,
            intentional_non_manifold_edge_ids=intentional_boundary_ids,
        )
    ).to_dict()

    server.cmd_select_by_ids(NAME, face_ids=[face_id])
    begun = server.cmd_begin_decision(NAME, decision["action"])
    performed = server.cmd_perform_decision(
        begun["decision_id"], decision["operation"], decision["operation_params"],
        command_id="coarse-body-inset-1",
    )
    verified = server.cmd_verify_decision(begun["decision_id"])
    committed = server.cmd_commit_decision(begun["decision_id"])

    # follow-up extrude of the (still-selected, per this project's own inset_selection
    # docstring) inset face -- a second decision, matching one-operation-per-decision
    begun2 = server.cmd_begin_decision(NAME, "EXTRUDE_INSET_FEATURE")
    performed2 = server.cmd_perform_decision(begun2["decision_id"], "extrude_selection", {"offset": 0.8}, command_id="coarse-body-extrude-1")
    verified2 = server.cmd_verify_decision(begun2["decision_id"])
    committed2 = server.cmd_commit_decision(begun2["decision_id"])

    bpy.ops.wm.save_as_mainfile(filepath=str(RUN / "inset_containment_skill_runtime_use.blend"))

    report = {
        "skill_id": SKILL_ID,
        "retrieved": [
            {"skill_id": item["skill_id"], "score": item["score"], "status": item["status"]}
            for item in retrieved
        ],
        "planner_decision": decision,
        "face_id_selected": face_id,
        "typed_transaction_inset": {
            "begin": begun, "performed": performed, "verified": verified, "committed": committed,
        },
        "typed_transaction_extrude": {
            "begin": begun2, "performed": performed2, "verified": verified2, "committed": committed2,
        },
        "after_metrics": mesh_metrics(NAME),
        "checks": {
            "skill_retrieved": bool(retrieved and retrieved[0]["skill_id"] == SKILL_ID),
            "planner_selected_skill_operation": decision["operation"] == "inset_selection",
            "planner_preserved_ticket_params": decision["operation_params"] == ticket["operation_params"],
            "typed_inset_performed": performed["performed"],
            "typed_extrude_performed": performed2["performed"],
            "base_mesh_remains_manifold": mesh_metrics(NAME)["non_manifold_edges"] <= 16,
        },
        "claim_boundary": (
            "One fresh typed runtime use of this skill on a planned local-feature-extrusion "
            "ticket on a coarse curved body; it validates that retrieval->planner->typed-"
            "execution actually connects for this narrow skill (inset before extruding a "
            "feature on a coarse surface), not general asset autonomy. Visual containment "
            "quality was already established in the validation run, not re-judged here."
        ),
    }
    report["pass"] = all(report["checks"].values())
    (RUN / "inset_containment_skill_runtime_use.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
