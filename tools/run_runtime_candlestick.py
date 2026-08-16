"""Build the held-out candlestick through the typed modeler decision lifecycle.

Run inside a fresh Blender background process.  The script deliberately uses
ModelerServer directly (rather than raw mesh mutation) for every artistic edit.
Direct BMesh reads are used only to resolve persistent IDs and measure the cage.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from blender_ops.modeler_server import ModelerServer  # noqa: E402
from blender_ops import persistent_ids  # noqa: E402
from knowledge_engine.planner import PlannerContext, plan_next_decision  # noqa: E402
from knowledge_engine.profile_sampling import (  # noqa: E402
    adaptive_profile_positions,
    profile_width_at,
)
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore  # noqa: E402


OBJECT_NAME = "Heldout_Candlestick"
MODEL_HEIGHT = 10.0
SKILL_ID = "deformation.topology.uniform_rings_before_shaping"


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--measurement", type=Path, required=True)
    parser.add_argument(
        "--reference-evidence",
        type=Path,
        required=True,
        help="Structured REFERENCE_ANALYSIS stage evidence; never inferred from a silhouette file",
    )
    parser.add_argument("--object-name", default=OBJECT_NAME)
    parser.add_argument("--height", type=float, default=10.0)
    parser.add_argument("--max-width", type=float, default=4.1860465116)
    parser.add_argument("--radial-vertices", type=int, default=12)
    parser.add_argument("--rings", type=int, default=25)
    parser.add_argument("--blend-name", default="heldout_candlestick.blend")
    parser.add_argument("--smooth-shell", action="store_true")
    parser.add_argument(
        "--adaptive-profile",
        action="store_true",
        help="Redistribute the initially uniform rings toward measured profile curvature before scaling",
    )
    parser.add_argument("--profile-smoothing-window", type=int, default=21)
    parser.add_argument(
        "--compact-report",
        action="store_true",
        help="Store transaction IDs/counts instead of duplicating every full transaction payload",
    )
    parser.add_argument(
        "--production-variants",
        action="store_true",
        help="Save editable HIGH_POLY and LOW_POLY collection variants without applying modifiers",
    )
    return parser.parse_args(argv)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def bmesh_read():
    obj = bpy.data.objects[OBJECT_NAME]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm


def ids_for_caps() -> list[int]:
    maps = persistent_ids.get_id_maps(OBJECT_NAME)
    bm = bmesh_read()
    try:
        return sorted(
            maps["faces"]["index_to_id"][face.index]
            for face in bm.faces
            if abs(face.normal.z) > 0.9
        )
    finally:
        bm.free()


def ids_for_vertical_edges() -> list[int]:
    maps = persistent_ids.get_id_maps(OBJECT_NAME)
    bm = bmesh_read()
    try:
        return sorted(
            maps["edges"]["index_to_id"][edge.index]
            for edge in bm.edges
            if abs(edge.verts[0].co.z - edge.verts[1].co.z) > MODEL_HEIGHT * 0.9
        )
    finally:
        bm.free()


def ids_for_boundary_edges() -> list[int]:
    maps = persistent_ids.get_id_maps(OBJECT_NAME)
    bm = bmesh_read()
    try:
        return sorted(
            maps["edges"]["index_to_id"][edge.index]
            for edge in bm.edges
            if edge.is_boundary
        )
    finally:
        bm.free()


def ring_records() -> list[dict]:
    maps = persistent_ids.get_id_maps(OBJECT_NAME)
    bm = bmesh_read()
    try:
        grouped: list[list] = []
        for vert in sorted(bm.verts, key=lambda item: float(item.co.z)):
            if not grouped:
                grouped.append([vert])
                continue
            center_z = sum(float(item.co.z) for item in grouped[-1]) / len(grouped[-1])
            if abs(float(vert.co.z) - center_z) <= 1e-5:
                grouped[-1].append(vert)
            else:
                grouped.append([vert])
        records = []
        for verts in grouped:
            z = sum(float(vert.co.z) for vert in verts) / len(verts)
            records.append({
                "z": z,
                "vertex_ids": sorted(maps["verts"]["index_to_id"][vert.index] for vert in verts),
                "vertex_count": len(verts),
                "radius_mean": sum(math.hypot(vert.co.x, vert.co.y) for vert in verts) / len(verts),
            })
        return records
    finally:
        bm.free()


def cage_audit() -> dict:
    bm = bmesh_read()
    try:
        components = 0
        remaining = set(bm.verts)
        while remaining:
            components += 1
            stack = [remaining.pop()]
            while stack:
                vert = stack.pop()
                for edge in vert.link_edges:
                    other = edge.other_vert(vert)
                    if other in remaining:
                        remaining.remove(other)
                        stack.append(other)
        face_sizes = [len(face.verts) for face in bm.faces]
        return {
            "vertices": len(bm.verts),
            "edges": len(bm.edges),
            "faces": len(bm.faces),
            "quads": sum(size == 4 for size in face_sizes),
            "non_quad_faces": sum(size != 4 for size in face_sizes),
            "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
            "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
            "loose_vertices": sum(not vert.link_edges for vert in bm.verts),
            "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
            "connected_components": components,
        }
    finally:
        bm.free()


def transact(server: ModelerServer, action: str, operation: str, params: dict, log: list[dict]) -> dict:
    begun = server.cmd_begin_decision(OBJECT_NAME, action)
    performed = server.cmd_perform_decision(
        begun["decision_id"], operation, params,
        command_id=f"{action}-{begun['decision_id']}",
    )
    verified = server.cmd_verify_decision(begun["decision_id"])
    committed = server.cmd_commit_decision(begun["decision_id"])
    record = {
        "action": action,
        "operation": operation,
        "params": params,
        "begin": begun,
        "perform": performed,
        "verify": verified,
        "commit": committed,
    }
    log.append(record)
    return record


def target_radius(
    profile: list[dict],
    z: float,
    half_max_width: float,
    *,
    smoothing_window: int = 7,
) -> float:
    # Blender z=-5 is image bottom; z=+5 is image top.
    top_fraction = 1.0 - ((z + MODEL_HEIGHT * 0.5) / MODEL_HEIGHT)
    width_norm = profile_width_at(profile, top_fraction, smoothing_window=smoothing_window)
    return max(0.08, float(width_norm) * half_max_width)


def main() -> int:
    global OBJECT_NAME, MODEL_HEIGHT
    args = parse_args()
    OBJECT_NAME = args.object_name
    MODEL_HEIGHT = args.height
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    measurement = json.loads(args.measurement.read_text(encoding="utf-8"))
    reference_evidence = json.loads(args.reference_evidence.read_text(encoding="utf-8"))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()
    capabilities = server.cmd_get_capabilities()
    transactions: list[dict] = []
    server.cmd_create_primitive(
        OBJECT_NAME, "cylinder", vertices=args.radial_vertices, radius=args.max_width * 0.5, depth=args.height,
        end_fill_type="NGON", calc_uvs=False,
    )
    # get_full_state reports current ID coverage but intentionally does not
    # assign missing IDs.  The external-edit handshake is the server-owned
    # read-only path that ensures IDs and captures the first state baseline.
    id_handshake = server.cmd_check_external_edit(OBJECT_NAME)
    reference_stage = server.cmd_set_modeling_stage(
        OBJECT_NAME,
        "PRIMARY_BLOCKOUT",
        reference_evidence,
    )
    if not reference_stage.get("advanced"):
        raise RuntimeError(f"reference stage gate failed: {reference_stage}")
    blockout_stage = server.cmd_set_modeling_stage(
        OBJECT_NAME,
        "PROPORTION_SILHOUETTE",
        {
            "dimensions_checked": True,
            "primary_components_present": True,
            "component_coverage": server.cmd_check_scene_component_coverage({
                "object_name": "runtime candlestick",
                "components": [{
                    "name": "candlestick_body", "role": "primary", "manufacture": "structural",
                }],
            }),
            "representation": "one connected rotational quad shell",
        },
    )
    if not blockout_stage.get("advanced"):
        raise RuntimeError(f"primary blockout stage gate failed: {blockout_stage}")

    cap_ids = ids_for_caps()
    server.cmd_select_by_ids(OBJECT_NAME, face_ids=cap_ids)
    cap_delete = transact(server, "remove_intentional_open_shell_caps", "delete_selection", {}, transactions)
    intentional_boundary_edge_ids = ids_for_boundary_edges()

    vertical_edge_ids = ids_for_vertical_edges()
    store = StructuredSkillStore(ROOT / "knowledge" / "skills")
    query = RetrievalContext(
        query="blown glass candlestick smooth multi-lobed radial profile needs evenly distributed rings before shaping",
        modeling_stage="PROPORTION_SILHOUETTE",
        workflow="radial product modeling subdivision deformation",
        surface_type="smooth taper flared profile",
        defect="uneven deformation density",
        local_topology=["connected quad rings", "two endpoint rings"],
        modifiers=[],
        blender_version=capabilities["blender_version"],
    )
    retrieved = store.search(query, top_k=5)
    ticket = {
        "type": "uneven_deformation_density",
        "target": "Heldout_Candlestick full rotational profile",
        "priority": 1,
        "severity": 0.9,
        "operation_params": {"edge_ids": vertical_edge_ids, "cuts": args.rings - 2},
    }
    planner_context = PlannerContext(
        task_id="runtime-use-candlestick",
        asset_id="heldout-museum-candlestick",
        stage="PROPORTION_SILHOUETTE",
        session_id=capabilities["session_id"],
        scene_revision=server.cmd_get_full_state(OBJECT_NAME)["revision"],
        active_object=OBJECT_NAME,
        base_state=server.cmd_get_full_state(OBJECT_NAME),
        evaluated_state=server.cmd_get_evaluated_state(OBJECT_NAME),
        visual_tickets=[ticket],
        retrieved_skills=retrieved,
        intentional_non_manifold_edge_ids=tuple(intentional_boundary_edge_ids),
    )
    decision = plan_next_decision(planner_context).to_dict()
    planner_checks = {
        "skill_retrieved_rank_1": bool(retrieved and retrieved[0]["skill_id"] == SKILL_ID),
        "skill_transfer_validated_before_use": bool(retrieved and retrieved[0]["status"] == "TRANSFER_VALIDATED"),
        "planner_acts": decision["disposition"] == "ACT",
        "planner_selects_loop_cut": decision["operation"] == "loop_cut_selection",
        "planner_preserves_scene_parameters": decision["operation_params"] == ticket["operation_params"],
        "planner_carries_skill_provenance": SKILL_ID in decision["retrieved_skill_ids"],
    }
    write_json(output / "retrieval_and_planner.json", {
        "query": query.__dict__,
        "retrieved": retrieved,
        "ticket": ticket,
        "decision": decision,
        "checks": planner_checks,
        "pass": all(planner_checks.values()),
    })
    if not all(planner_checks.values()):
        raise RuntimeError(f"frozen retrieval/planner gate failed: {planner_checks}")

    server.cmd_select_by_ids(OBJECT_NAME, edge_ids=decision["operation_params"]["edge_ids"])
    loop_record = transact(
        server, decision["action"], decision["operation"],
        {"cuts": decision["operation_params"]["cuts"]}, transactions,
    )
    rings_before = ring_records()
    server.cmd_render_silhouette(
        OBJECT_NAME, str(output / "unshaped_cylinder_mask.png"),
        view="front", resolution=720, margin=1.12,
    )

    half_max_width = args.max_width * 0.5
    if args.adaptive_profile:
        image_positions = adaptive_profile_positions(
            measurement["row_profile"],
            len(rings_before),
            smoothing_window=args.profile_smoothing_window,
        )
        # ring_records is bottom-to-top; image positions are top-to-bottom.
        image_positions = list(reversed(image_positions))
    else:
        image_positions = [
            1.0 - ((ring["z"] + MODEL_HEIGHT * 0.5) / MODEL_HEIGHT)
            for ring in rings_before
        ]
    profile_targets = []
    for index, (ring, image_position) in enumerate(zip(rings_before, image_positions)):
        desired_z = (0.5 - image_position) * MODEL_HEIGHT
        redistribution_decision_id = None
        if abs(desired_z - ring["z"]) > 1e-8:
            server.cmd_select_by_ids(OBJECT_NAME, vertex_ids=ring["vertex_ids"])
            move_record = transact(
                server,
                f"redistribute_reference_ring_{index:02d}",
                "move_selection",
                {"delta": [0.0, 0.0, desired_z - ring["z"]]},
                transactions,
            )
            redistribution_decision_id = move_record["begin"]["decision_id"]
        desired = target_radius(
            measurement["row_profile"],
            desired_z,
            half_max_width,
            smoothing_window=args.profile_smoothing_window if args.adaptive_profile else 7,
        )
        factor = desired / ring["radius_mean"]
        server.cmd_select_by_ids(OBJECT_NAME, vertex_ids=ring["vertex_ids"])
        record = transact(
            server, f"shape_reference_ring_{index:02d}", "scale_selection",
            {"factor": [factor, factor, 1.0], "center": [0.0, 0.0, desired_z]}, transactions,
        )
        profile_targets.append({
            "ring_index_bottom_to_top": index,
            "z_before": ring["z"],
            "z": desired_z,
            "image_position_top_to_bottom": image_position,
            "vertex_ids": ring["vertex_ids"],
            "radius_before": ring["radius_mean"],
            "target_radius": desired,
            "scale_factor": factor,
            "redistribution_decision_id": redistribution_decision_id,
            "decision_id": record["begin"]["decision_id"],
        })

    modifier_decisions = []
    if args.smooth_shell:
        modifier_decisions.append(transact(
            server, "add_surface_subdivision", "add_modifier",
            {"modifier_type": "SUBSURF", "modifier_name": "Surface_Smoothing"}, transactions,
        ))
        for parameter, value in (("levels", 2), ("render_levels", 2), ("boundary_smooth", "PRESERVE_CORNERS")):
            modifier_decisions.append(transact(
                server, f"set_surface_subdivision_{parameter}", "set_modifier_parameter",
                {"modifier_name": "Surface_Smoothing", "parameter": parameter, "value": value}, transactions,
            ))
        modifier_decisions.append(transact(
            server, "add_hollow_glass_wall", "add_modifier",
            {"modifier_type": "SOLIDIFY", "modifier_name": "Glass_Wall"}, transactions,
        ))
        for parameter, value in (("thickness", args.max_width * 0.02), ("offset", -1.0), ("use_even_offset", True)):
            modifier_decisions.append(transact(
                server, f"set_glass_wall_{parameter}", "set_modifier_parameter",
                {"modifier_name": "Glass_Wall", "parameter": parameter, "value": value}, transactions,
            ))
    shading = transact(
        server, "smooth_rounded_glass_profile", "set_smooth_by_angle",
        {"angle": math.radians(30.0), "keep_sharp_edges": True}, transactions,
    )
    final_state = server.cmd_get_full_state(OBJECT_NAME)
    evaluated_state = server.cmd_get_evaluated_state(OBJECT_NAME)
    audit = cage_audit()
    renders = {
        "silhouette": server.cmd_render_silhouette(
            OBJECT_NAME, str(output / "final_candidate_mask.png"),
            view="front", resolution=720, margin=1.12,
        ),
        "solid": server.cmd_render_diagnostic_pass(
            OBJECT_NAME, str(output / "final_solid.png"), "solid",
            view="front", resolution=720, margin=1.12,
        ),
        "matcap": server.cmd_render_diagnostic_pass(
            OBJECT_NAME, str(output / "final_matcap.png"), "matcap",
            view="front", resolution=720, margin=1.12,
        ),
        "wireframe": server.cmd_render_diagnostic_pass(
            OBJECT_NAME, str(output / "final_wireframe.png"), "wireframe",
            view="front", resolution=720, margin=1.12,
        ),
    }
    modeling_scene_mesh_objects = sorted(obj.name for obj in bpy.data.objects if obj.type == "MESH")
    production_variants = None
    if args.production_variants:
        variant_base_name = OBJECT_NAME[:-5] if OBJECT_NAME.endswith("_HIGH") else OBJECT_NAME
        variant_record = transact(
            server,
            "package_editable_high_low_variants",
            "package_high_low_variants",
            {
                "low_object_name": f"{variant_base_name}_LOW",
                "high_collection_name": "HIGH_POLY",
                "low_collection_name": "LOW_POLY",
                "low_subd_levels": 0,
                "hide_low": True,
            },
            transactions,
        )
        production_variants = {
            **variant_record["perform"]["result"],
            "typed_decision_id": variant_record["begin"]["decision_id"],
        }
    blend_path = output / args.blend_name
    server.cmd_save_file(str(blend_path))
    report = {
        "blender": capabilities,
        "reference_measurement": str(args.measurement.resolve()),
        "object": OBJECT_NAME,
        "scene_mesh_objects": modeling_scene_mesh_objects,
        "modeling_scene_mesh_objects": modeling_scene_mesh_objects,
        "saved_scene_mesh_objects": sorted(obj.name for obj in bpy.data.objects if obj.type == "MESH"),
        "construction": {
            "starting_primitive": f"one {args.radial_vertices}-sided cylinder",
            "separate_primitives_added": 0,
            "cap_face_ids_deleted": cap_ids,
            "vertical_edge_ids_selected_for_planner_cut": vertical_edge_ids,
            "intentional_boundary_edge_ids": intentional_boundary_edge_ids,
            "ring_count": len(rings_before),
            "radial_vertices_per_ring": sorted({ring["vertex_count"] for ring in rings_before}),
            "requested_height": args.height,
            "requested_max_width": args.max_width,
            "smooth_shell_modifiers": args.smooth_shell,
            "adaptive_profile": args.adaptive_profile,
            "profile_smoothing_window": args.profile_smoothing_window,
            "profile_targets": profile_targets,
        },
        "initial_id_handshake": id_handshake,
        "stage_transitions": [reference_stage, blockout_stage],
        "loop_cut_decision_id": loop_record["begin"]["decision_id"],
        "cap_delete_decision_id": cap_delete["begin"]["decision_id"],
        "shading_decision_id": shading["begin"]["decision_id"],
        "modifier_decision_ids": [item["begin"]["decision_id"] for item in modifier_decisions],
        "transaction_count": len(transactions),
        "transaction_summary": {
            "operation_counts": dict(sorted(Counter(item["operation"] for item in transactions).items())),
            "report_compacted": args.compact_report,
        },
        "base_cage_audit": audit,
        "final_state": final_state,
        "evaluated_state": evaluated_state,
        "renders": renders,
        "production_variants": production_variants,
        "blend_path": str(blend_path),
        "boundary": "Rotational primary-form correction from a measured front profile. Material appearance and historically exact hidden construction remain outside this experiment; dimensions and top form require the independent saved-scene verifier.",
    }
    if not args.compact_report:
        report["transactions"] = transactions
    write_json(output / "blender_runtime_report.json", report)
    print(json.dumps({
        "output": str(output),
        "session_id": capabilities["session_id"],
        "planner_pass": all(planner_checks.values()),
        "transaction_count": len(transactions),
        "cage": audit,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
