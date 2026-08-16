"""Use the verified loop-cut skill through retrieval, planning, and one typed runtime decision."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path: sys.path.insert(0, str(path))

from blender_ops import persistent_ids, state_probe
from blender_ops.modeler_server import ModelerServer
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore

RUN = ROOT / "runs" / "2026-08-16_real-video-loopcut-review"
SKILL_ID = "topology.loop_cuts.reserve_functional_regions"
NAME = "RuntimePlannedPanel"


def vertical_edge_ids():
    obj = bpy.data.objects[NAME]; persistent_ids.ensure_persistent_ids(NAME)
    maps = persistent_ids.get_id_maps(NAME); bm = bmesh.new(); bm.from_mesh(obj.data); bm.edges.ensure_lookup_table()
    ids = [maps["edges"]["index_to_id"][edge.index] for edge in bm.edges if abs((edge.verts[1].co-edge.verts[0].co).normalized().dot(Vector((0, 1, 0)))) > .999]
    bm.free(); return sorted(ids)


def main():
    RUN.mkdir(parents=True, exist_ok=True); bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer(); created = server.cmd_create_primitive(NAME, "cube")
    obj = bpy.data.objects[NAME]; obj.scale = (2.5, 1.5, .35); bpy.context.view_layer.objects.active = obj; obj.select_set(True); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    edge_ids = vertical_edge_ids()
    store = StructuredSkillStore(ROOT / "knowledge" / "skills")
    query = RetrievalContext(query="reserve functional face regions on a continuous quad control panel with loop cuts", modeling_stage="PRIMARY_BLOCKOUT", workflow="box modeling", surface_type="planar mechanical", defect="missing functional face regions", local_topology=["continuous quad shell", "traversable quad edge ring"], modifiers=["BEVEL"], blender_version="5.2")
    retrieved = store.search(query, top_k=5)
    ticket = {"type": "reserve_functional_face_regions", "target": "control_panel_center_region", "priority": 1, "severity": .8, "operation_params": {"cuts": 2}}
    decision = plan_next_decision(PlannerContext(task_id="loopcut-runtime-use", asset_id="runtime-panel", stage="PRIMARY_BLOCKOUT", session_id=server.session_id, scene_revision=0, active_object=NAME, base_state={"mesh_health": state_probe.mesh_health(NAME)}, evaluated_state={"mesh_health": state_probe.mesh_health(NAME)}, visual_tickets=[ticket], retrieved_skills=retrieved)).to_dict()
    server.cmd_select_by_ids(NAME, edge_ids=edge_ids)
    begun = server.cmd_begin_decision(NAME, decision["action"])
    performed = server.cmd_perform_decision(begun["decision_id"], decision["operation"], decision["operation_params"], command_id="runtime-panel-loopcut-1")
    verified = server.cmd_verify_decision(begun["decision_id"]); committed = server.cmd_commit_decision(begun["decision_id"])
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN / "loopcut_skill_runtime_use.blend"))
    report = {"skill_id": SKILL_ID, "retrieved": [{"skill_id": item["skill_id"], "score": item["score"], "status": item["status"]} for item in retrieved], "planner_decision": decision, "edge_ids_selected": edge_ids, "typed_transaction": {"begin": begun, "performed": performed, "verified": verified, "committed": committed}, "after_health": state_probe.mesh_health(NAME), "checks": {"skill_retrieved": bool(retrieved and retrieved[0]["skill_id"] == SKILL_ID), "planner_selected_skill_operation": decision["operation"] == "loop_cut_selection", "planner_preserved_ticket_params": decision["operation_params"] == ticket["operation_params"], "typed_operation_performed": performed["performed"], "base_mesh_remains_manifold": state_probe.mesh_health(NAME)["non_manifold_edges"] == 0}, "claim_boundary": "One fresh typed runtime use on a planned box-panel region; it validates runtime integration of this narrow skill, not general asset autonomy."}
    report["pass"] = all(report["checks"].values()); (RUN / "loopcut_skill_runtime_use.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2)); raise SystemExit(0 if report["pass"] else 2)

if __name__ == "__main__": main()
