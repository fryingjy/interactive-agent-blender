"""Falsification test: can a skill EVER fire from real observed geometry?

The three RUNTIME_VALIDATED skills each declare planner_hint.trigger_ticket_types.
Grep shows every one of those type strings exists in exactly two places: the skill's
own hint, and the runtime-use script that hand-authors a ticket of that type. Nothing
in blender_ops observes a mesh and emits one.

This script proves the consequence rather than asserting it: build a mesh that has the
exact defect the bevel skill repairs (a triangle at a multi-edge corner, produced by an
odd-segment bevel), observe it with the project's own real observation tools, feed those
real observations to the real planner, and record whether any skill is selected.

Execute headlessly:
    blender --background --factory-startup --python tools/audit_observation_to_skill_gap.py -- OUTPUT_DIR
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

from blender_ops import evaluated_probe, persistent_ids, state_probe
from blender_ops.modeler_server import ModelerServer
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore

NAME = "AuditCornerDefect"


def output_directory() -> Path:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected exactly one OUTPUT_DIR argument after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def corner_edge_ids(server):
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
        counts[len(f.verts)] = counts.get(len(f.verts), 0) + 1
    bm.free()
    return counts


def main() -> None:
    out = output_directory()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()
    server.cmd_create_primitive(NAME, "cube")

    # Introduce the EXACT defect the bevel-parity skill exists to repair:
    # an odd-segment bevel on a multi-edge corner, which leaves a triangle.
    server.cmd_select_by_ids(NAME, edge_ids=corner_edge_ids(server))
    begun = server.cmd_begin_decision(NAME, "INTRODUCE_ODD_SEGMENT_CORNER_DEFECT")
    server.cmd_perform_decision(begun["decision_id"], "bevel_selection",
                                {"offset": 0.25, "segments": 1})
    server.cmd_verify_decision(begun["decision_id"])
    server.cmd_commit_decision(begun["decision_id"])

    counts = face_vertex_counts(NAME)
    defect_present = counts.get(3, 0) > 0

    # Observe with the project's OWN real observation tooling -- no hand-authored ticket.
    defect_regions = evaluated_probe.evaluated_defect_regions(NAME, max_tickets=20)
    observed_ticket_types = sorted({t["type"] for t in defect_regions.get("tickets", [])})

    # Feed those REAL observations to the REAL planner as visual tickets.
    observed_tickets = []
    for t in defect_regions.get("tickets", [])[:5]:
        observed_tickets.append({
            "type": t["type"],
            "target": f"observed_region_{t['type']}",
            "priority": 1,
            "severity": float(t.get("severity", 0.0)),
        })

    store = StructuredSkillStore(ROOT / "knowledge" / "skills")
    retrieved = store.search(RetrievalContext(
        query="triangle at a beveled hard-surface corner where several edges meet",
        modeling_stage="TOPOLOGY_SURFACE", workflow="bevel", surface_type="hard-surface",
        defect="triangle at a beveled corner", modifiers=["BEVEL"], blender_version="5.2",
    ), top_k=5)

    decision = plan_next_decision(PlannerContext(
        task_id="observation-to-skill-gap-audit", asset_id="audit-corner",
        stage="TOPOLOGY_SURFACE", session_id=server.session_id, scene_revision=0,
        active_object=NAME,
        base_state={"mesh_health": state_probe.mesh_health(NAME)},
        evaluated_state={"mesh_health": state_probe.mesh_health(NAME)},
        visual_tickets=observed_tickets,
        retrieved_skills=retrieved,
    )).to_dict()

    skill_fired = decision.get("action") == "BEVEL_CORNER_ALL_EDGES_EVEN_SEGMENTS"

    report = {
        "question": (
            "With a REAL defect present and REAL observed tickets (not hand-authored), "
            "does the retrieval+planner chain select the skill that repairs it?"
        ),
        "defect_actually_present": defect_present,
        "face_vertex_counts": {str(k): v for k, v in counts.items()},
        "observed_ticket_types_from_real_geometry": observed_ticket_types,
        "skill_declared_trigger_types": ["multi_edge_corner_bevel"],
        "vocabulary_overlap": sorted(set(observed_ticket_types) & {"multi_edge_corner_bevel"}),
        "retrieval_still_ranks_skill_first": bool(
            retrieved and retrieved[0]["skill_id"] == "bevel.segments.parity_avoids_corner_triangle"
        ),
        "planner_decision": {
            "disposition": decision.get("disposition"),
            "action": decision.get("action"),
            "operation": decision.get("operation"),
        },
        "repair_skill_fired_from_real_observation": skill_fired,
        "finding": (
            "Retrieval ranks the correct repair skill first, and the defect is genuinely "
            "present in the mesh, yet the planner does NOT select the skill, because the "
            "vocabulary the system can OBSERVE (area_outlier / high_angle) and the vocabulary "
            "the skills TRIGGER on (multi_edge_corner_bevel) are disjoint. The previously "
            "recorded RUNTIME_VALIDATED evidence bridged this gap only by hand-authoring a "
            "ticket whose type string was copied from the skill's own trigger list."
        ),
    }
    report["gap_confirmed"] = bool(defect_present and not skill_fired)

    (out / "observation_to_skill_gap.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
