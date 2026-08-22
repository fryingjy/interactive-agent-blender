"""Independently verify the saved Polygon Runway ramen-machine reproduction."""

from __future__ import annotations

import json
from pathlib import Path

import bmesh
import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = REPO_ROOT / "runs" / "2026-08-22_tutorial-polygon-runway-ramen-machine"
REPORT_PATH = RUN_DIR / "independent_verification.json"


def mesh_health(obj: bpy.types.Object) -> dict[str, int]:
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
        "nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "loose_vertices": sum(not vertex.link_edges for vertex in bm.verts),
    }
    bm.free()
    return result


def main() -> None:
    required_objects = {
        "ramen_machine_housing",
        "floor_platform",
        "front_sign_frame",
        "service_counter",
        "roof_ramen_bowl",
        "right_side_cable",
        "right_side_cable_secondary",
        "stool_base_left",
        "stool_base_right",
        "stool_seat_left",
        "stool_seat_right",
        "control_button_red",
        "control_button_yellow",
        "control_button_green",
        "front_ramen_text",
        "side_number_26",
    }
    required_collections = {
        "MODEL_PRIMARY",
        "MODEL_ASSEMBLIES",
        "MODEL_DETAILS",
        "SIGNAGE",
        "LIGHTING",
    }
    object_names = {obj.name for obj in bpy.data.objects}
    collection_names = {collection.name for collection in bpy.data.collections}
    missing_objects = sorted(required_objects - object_names)
    missing_collections = sorted(required_collections - collection_names)

    housing = bpy.data.objects.get("ramen_machine_housing")
    housing_health = mesh_health(housing) if housing and housing.type == "MESH" else None
    housing_components = 0
    if housing and housing.type == "MESH":
        bm = bmesh.new()
        bm.from_mesh(housing.data)
        remaining = set(bm.verts)
        while remaining:
            housing_components += 1
            stack = [remaining.pop()]
            while stack:
                vertex = stack.pop()
                linked = {edge.other_vert(vertex) for edge in vertex.link_edges}
                newly_found = linked & remaining
                remaining.difference_update(newly_found)
                stack.extend(newly_found)
        bm.free()

    text_bodies = {
        name: bpy.data.objects[name].data.body
        for name in ("front_ramen_text", "side_number_26")
        if name in bpy.data.objects and bpy.data.objects[name].type == "FONT"
    }
    live_bevel_objects = sorted(
        obj.name
        for obj in bpy.context.scene.objects
        if any(modifier.type == "BEVEL" for modifier in obj.modifiers)
    )
    applied_modifier_suspects = sorted(
        obj.name
        for obj in bpy.context.scene.objects
        if obj.get("modifiers_applied") is True
    )
    bowl = bpy.data.objects.get("roof_ramen_bowl")
    body = housing
    bowl_to_body_width = (
        bowl.dimensions.x / body.dimensions.x if bowl and body and body.dimensions.x else None
    )
    final_render = RUN_DIR / "ramen_machine_material_v4.png"

    checks = {
        "required_objects_present": not missing_objects,
        "required_collections_present": not missing_collections,
        "housing_is_single_connected_mesh": housing_components == 1,
        "housing_has_no_nonmanifold_edges": bool(housing_health) and housing_health["nonmanifold_edges"] == 0,
        "live_bevels_preserved": len(live_bevel_objects) >= 6,
        "no_declared_applied_modifiers": not applied_modifier_suspects,
        "front_text_is_japanese_ramen": text_bodies.get("front_ramen_text") == "ラーメン",
        "side_number_is_26": text_bodies.get("side_number_26") == "26",
        "two_stools_present": all(name in bpy.data.objects for name in ("stool_seat_left", "stool_seat_right")),
        "three_buttons_present": all(
            name in bpy.data.objects
            for name in ("control_button_red", "control_button_yellow", "control_button_green")
        ),
        "bowl_scale_is_plausible": bowl_to_body_width is not None and 0.45 <= bowl_to_body_width <= 0.80,
        "final_render_exists": final_render.exists() and final_render.stat().st_size > 0,
    }
    report = {
        "schema_version": 1,
        "record_type": "INDEPENDENT_TUTORIAL_REPRODUCTION_VERIFICATION",
        "blend_file": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "checks": checks,
        "passed": all(checks.values()),
        "missing_objects": missing_objects,
        "missing_collections": missing_collections,
        "housing_connected_components": housing_components,
        "housing_health": housing_health,
        "live_bevel_objects": live_bevel_objects,
        "applied_modifier_suspects": applied_modifier_suspects,
        "text_bodies": text_bodies,
        "bowl_to_body_width": bowl_to_body_width,
        "scope_note": (
            "This fresh-process verifier checks saved scene structure and technical invariants. "
            "It does not claim source-frame visual fidelity."
        ),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
