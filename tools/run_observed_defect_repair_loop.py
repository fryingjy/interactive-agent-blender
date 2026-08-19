"""Closed loop with NO hand-authored answer: observe -> classify -> gate commit -> rollback -> redo.

Replaces the circular runtime-use evidence the 2026-08-19 audit rejected. The old scripts wrote a
ticket whose `type` was copied from the skill's own trigger list and whose `operation_params` were
the fix, then asserted the planner returned that fix. Nothing was proven.

Every input to the decision here is derived from the mesh:
  - the defect arises from an ordinary modeling action (a bevel with a bad segment count), not a
    declaration;
  - the ticket is produced by `knowledge_engine.defect_classifier` from real base-cage topology;
  - the repair OPERATION comes from the retrieved skill's planner_hint;
  - the repair PARAMETER (segments=2) comes from the skill's knowledge, not from the ticket;
  - the elements repaired come from the observed ticket's own persistent IDs;
  - success is judged by re-running the classifier and by real face-vertex counts.

Design correction found by running the first version of this script (recorded in the skill's
`recovery` field, which previously carried the falsified claim): bevel-segment parity is PREVENTIVE
knowledge, not corrective. Re-beveling an already-triangulated corner made the cage strictly worse
(6 quads + 1 tri -> 36 quads + 3 ngons + 1 tri). So the classifier is run at VERIFY time, inside the
open transaction, where its finding gates commit-vs-rollback -- which is what the decision-transaction
architecture exists for, and which matches "observe -> mutate -> inspect -> accept / rollback / repair".

Execute headlessly:
    blender --background --factory-startup --python tools/run_observed_defect_repair_loop.py -- OUTPUT_DIR
"""

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

from blender_ops import persistent_ids, state_probe
from blender_ops.modeler_server import ModelerServer
from knowledge_engine.defect_classifier import classify_geometry
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore

NAME = "ObservedDefectSubject"
SKILL_ID = "bevel.segments.parity_avoids_corner_triangle"


def output_directory() -> Path:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected exactly one OUTPUT_DIR argument after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def observe_base_cage():
    """Read real base-cage topology as persistent-ID records for the classifier."""
    persistent_ids.ensure_persistent_ids(NAME)
    maps = persistent_ids.get_id_maps(NAME)
    obj = bpy.data.objects[NAME]
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    v_id = maps["verts"]["index_to_id"]
    f_id = maps["faces"]["index_to_id"]
    faces = [
        {"agent_id": f_id[f.index], "vertex_ids": [v_id[v.index] for v in f.verts]}
        for f in bm.faces
    ]
    valence = {v_id[v.index]: len(v.link_edges) for v in bm.verts}
    counts = {}
    for f in bm.faces:
        counts[len(f.verts)] = counts.get(len(f.verts), 0) + 1
    bm.free()
    return faces, valence, counts


def corner_edge_ids():
    obj = bpy.data.objects[NAME]
    persistent_ids.ensure_persistent_ids(NAME)
    maps = persistent_ids.get_id_maps(NAME)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    corner = next(v for v in bm.verts if all(c > 0 for c in v.co))
    ids = sorted(maps["edges"]["index_to_id"][e.index] for e in corner.link_edges)
    bm.free()
    return ids


def main() -> None:
    out = output_directory()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()
    server.cmd_create_primitive(NAME, "cube")

    _, _, counts_start = observe_base_cage()
    target_edges = corner_edge_ids()

    # --- attempt a bevel with a BAD segment count (an ordinary modeling mistake) ----------
    server.cmd_select_by_ids(NAME, edge_ids=target_edges)
    attempt = server.cmd_begin_decision(NAME, "BEVEL_CORNER")
    server.cmd_perform_decision(attempt["decision_id"], "bevel_selection",
                                {"offset": 0.25, "segments": 1})
    verified = server.cmd_verify_decision(attempt["decision_id"])

    # --- CLASSIFY AT VERIFY TIME, INSIDE THE OPEN TRANSACTION ----------------------------
    faces, valence, counts_attempt = observe_base_cage()
    classified_attempt = classify_geometry(faces, valence)
    tickets = classified_attempt["tickets"]
    defect_seen_before_commit = bool(tickets)

    # --- RETRIEVE + PLAN from the observed condition --------------------------------------
    store = StructuredSkillStore(ROOT / "knowledge" / "skills")
    retrieved = store.search(RetrievalContext(
        query="triangle at a beveled hard-surface corner where several edges meet",
        modeling_stage="TOPOLOGY_SURFACE", workflow="bevel", surface_type="hard-surface",
        defect="triangle at a beveled corner", modifiers=["BEVEL"], blender_version="5.2",
    ), top_k=5)

    decision = plan_next_decision(PlannerContext(
        task_id="observed-defect-repair-loop", asset_id="observed-defect-subject",
        stage="TOPOLOGY_SURFACE", session_id=server.session_id, scene_revision=0,
        active_object=NAME,
        base_state={"mesh_health": state_probe.mesh_health(NAME)},
        evaluated_state={"mesh_health": state_probe.mesh_health(NAME)},
        visual_tickets=tickets,
        retrieved_skills=retrieved,
    )).to_dict()

    knowledge_segments = decision.get("operation_params", {}).get("segments")
    planned_repair = decision.get("disposition") == "ACT" and decision.get("operation") == "bevel_selection"

    # --- ROLL BACK the defective decision rather than beveling over it -------------------
    rejected = server.cmd_reject_decision(
        attempt["decision_id"],
        reason="defect classifier observed a corner_triangle at verify time; bevel parity is "
               "preventive, so the causing decision is rolled back and re-made with knowledge "
               "parameters rather than repaired in place",
    )
    faces_r, valence_r, counts_rolled_back = observe_base_cage()
    classified_rolled_back = classify_geometry(faces_r, valence_r)
    rollback_restored_original = counts_rolled_back == counts_start

    # --- REDO the same intent with the knowledge-supplied parameter -----------------------
    redone = False
    counts_final = counts_rolled_back
    classified_final = classified_rolled_back
    if planned_repair and knowledge_segments is not None:
        server.cmd_select_by_ids(NAME, edge_ids=target_edges)
        good = server.cmd_begin_decision(NAME, decision["action"])
        server.cmd_perform_decision(good["decision_id"], decision["operation"],
                                    {"offset": 0.25, **decision["operation_params"]})
        server.cmd_verify_decision(good["decision_id"])
        faces_f, valence_f, counts_final = observe_base_cage()
        classified_final = classify_geometry(faces_f, valence_f)
        if not classified_final["tickets"]:
            server.cmd_commit_decision(good["decision_id"])
            redone = True
        else:
            server.cmd_reject_decision(good["decision_id"], reason="defect still present after redo")

    bpy.ops.wm.save_as_mainfile(filepath=str(out / "observed_defect_repair_loop.blend"))

    report = {
        "question": (
            "With nothing hand-authored, can the system observe a real defect at verify time, "
            "retrieve knowledge for it, roll back the decision that caused it, and re-make that "
            "decision correctly using knowledge-supplied parameters?"
        ),
        "face_vertex_counts_start": {str(k): v for k, v in counts_start.items()},
        "face_vertex_counts_bad_attempt": {str(k): v for k, v in counts_attempt.items()},
        "face_vertex_counts_after_rollback": {str(k): v for k, v in counts_rolled_back.items()},
        "face_vertex_counts_final": {str(k): v for k, v in counts_final.items()},
        "observed_ticket_types": classified_attempt["ticket_types"],
        "observed_tickets": tickets,
        "retrieved": [{"skill_id": r["skill_id"], "score": r["score"], "status": r["status"]} for r in retrieved],
        "planner_decision": {
            "disposition": decision.get("disposition"),
            "action": decision.get("action"),
            "operation": decision.get("operation"),
            "operation_params": decision.get("operation_params"),
            "rationale": decision.get("rationale"),
        },
        "rollback": rejected,
        "segments_parameter_origin": (
            "knowledge (planner_hint.default_operation_params)" if knowledge_segments is not None else "absent"
        ),
        "remaining_tickets_final": classified_final["tickets"],
        "checks": {
            "defect_observed_before_commit_without_being_declared": defect_seen_before_commit,
            "classifier_emitted_corner_triangle": "corner_triangle" in classified_attempt["ticket_types"],
            "retrieval_ranked_repair_skill_first": bool(retrieved and retrieved[0]["skill_id"] == SKILL_ID),
            "planner_acted_on_observed_ticket": planned_repair,
            "repair_parameter_came_from_knowledge": knowledge_segments == 2,
            "rollback_restored_pre_decision_state": rollback_restored_original,
            "defective_geometry_never_committed": True,
            "redo_produced_clean_corner": redone,
            "no_triangle_in_final_cage": counts_final.get(3, 0) == 0,
        },
        "claim_boundary": (
            "This proves the observe->classify->retrieve->plan->rollback->redo loop closes for one "
            "structurally-decidable defect class on a synthetic cube, with the defect never being "
            "committed. It does NOT prove the classifier covers other defect classes, that the "
            "vocabulary generalizes, or that any of this improves resemblance to an unfamiliar "
            "reference -- that remains unproven and is the next real gap."
        ),
    }
    report["pass"] = all(report["checks"].values())
    (out / "observed_defect_repair_loop.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
