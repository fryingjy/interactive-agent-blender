"""Use the verified bevel-segment-parity skill through retrieval, planning, and one typed
runtime decision -- the RUNTIME_VALIDATED gate the skill's own status_note names as its
next step, following the exact established pattern in run_loopcut_skill_runtime_use.py.
"""

from __future__ import annotations

import json
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

RUN = ROOT / "runs" / "2026-08-17_bevel-skill-runtime-use"
SKILL_ID = "bevel.segments.parity_avoids_corner_triangle"
NAME = "RuntimeBracketCorner"


def corner_edge_ids():
    """The 3 edges meeting at vertex (1,1,1) on a fresh default cube -- a genuine multi-edge
    hard-surface corner, matching the skill's own validated preconditions."""
    obj = bpy.data.objects[NAME]
    persistent_ids.ensure_persistent_ids(NAME)
    maps = persistent_ids.get_id_maps(NAME)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    corner = next(v for v in bm.verts if all(c > 0 for c in v.co))
    ids = sorted(maps["edges"]["index_to_id"][e.index] for e in corner.link_edges)
    bm.free()
    return ids


def face_vertex_counts(obj_name):
    obj = bpy.data.objects[obj_name]
    bm = bmesh.new(); bm.from_mesh(obj.data)
    counts = {}
    for f in bm.faces:
        n = len(f.verts)
        counts[n] = counts.get(n, 0) + 1
    bm.free()
    return counts


def main():
    RUN.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()
    server.cmd_create_primitive(NAME, "cube")
    edge_ids = corner_edge_ids()

    store = StructuredSkillStore(ROOT / "knowledge" / "skills")
    query = RetrievalContext(
        query="beveling a hard-surface corner where several edges meet without leaving a triangle",
        modeling_stage="TOPOLOGY_SURFACE",
        workflow="bevel",
        surface_type="hard-surface",
        defect="triangle at a beveled corner",
        local_topology=["three-or-more-edges-meeting-at-a-corner"],
        modifiers=["BEVEL"],
        blender_version="5.2",
    )
    retrieved = store.search(query, top_k=5)

    ticket = {
        "type": "multi_edge_corner_bevel",
        "target": "bracket_top_corner",
        "priority": 1,
        "severity": 0.6,
        "operation_params": {"offset": 0.25, "segments": 2},
    }

    decision = plan_next_decision(
        PlannerContext(
            task_id="bevel-skill-runtime-use",
            asset_id="runtime-bracket",
            stage="TOPOLOGY_SURFACE",
            session_id=server.session_id,
            scene_revision=0,
            active_object=NAME,
            base_state={"mesh_health": state_probe.mesh_health(NAME)},
            evaluated_state={"mesh_health": state_probe.mesh_health(NAME)},
            visual_tickets=[ticket],
            retrieved_skills=retrieved,
        )
    ).to_dict()

    before_faces = face_vertex_counts(NAME)
    server.cmd_select_by_ids(NAME, edge_ids=edge_ids)
    begun = server.cmd_begin_decision(NAME, decision["action"])
    performed = server.cmd_perform_decision(
        begun["decision_id"], decision["operation"], decision["operation_params"],
        command_id="bracket-corner-bevel-1",
    )
    verified = server.cmd_verify_decision(begun["decision_id"])
    committed = server.cmd_commit_decision(begun["decision_id"])
    after_faces = face_vertex_counts(NAME)

    bpy.ops.wm.save_as_mainfile(filepath=str(RUN / "bevel_skill_runtime_use.blend"))

    report = {
        "skill_id": SKILL_ID,
        "retrieved": [
            {"skill_id": item["skill_id"], "score": item["score"], "status": item["status"]}
            for item in retrieved
        ],
        "planner_decision": decision,
        "edge_ids_selected": edge_ids,
        "typed_transaction": {
            "begin": begun, "performed": performed, "verified": verified, "committed": committed,
        },
        "face_vertex_counts_before": before_faces,
        "face_vertex_counts_after": after_faces,
        "after_health": state_probe.mesh_health(NAME),
        "checks": {
            "skill_retrieved": bool(retrieved and retrieved[0]["skill_id"] == SKILL_ID),
            "planner_selected_skill_operation": decision["operation"] == "bevel_selection",
            "planner_preserved_ticket_params": decision["operation_params"] == ticket["operation_params"],
            "typed_operation_performed": performed["performed"],
            "no_triangle_at_corner": 3 not in after_faces,
            "base_mesh_remains_manifold": state_probe.mesh_health(NAME)["non_manifold_edges"] == 0,
        },
        "claim_boundary": (
            "One fresh typed runtime use of this skill on a planned multi-edge corner bevel "
            "ticket; it validates that retrieval->planner->typed-execution actually connects "
            "for this narrow skill, not general asset autonomy or that every future corner "
            "bevel will be planner-routed without a matching ticket."
        ),
    }
    report["pass"] = all(report["checks"].values())
    (RUN / "bevel_skill_runtime_use.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
