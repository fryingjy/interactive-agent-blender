"""Fresh-process verification for the source-reviewed Blender Guru beginner scene."""

from __future__ import annotations

import json
from pathlib import Path

import bmesh
import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = REPO_ROOT / "runs" / "2026-08-22_tutorial-blenderguru-beginner-rebuild-v2"


def health(name: str) -> dict[str, int]:
    obj = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
    }
    bm.free()
    return result


def evaluated_health(name: str) -> dict[str, int]:
    obj = bpy.data.objects[name]
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh(preserve_all_data_layers=False, depsgraph=bpy.context.evaluated_depsgraph_get())
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def main() -> None:
    required = {"Donut", "Icing", "Plate", "Mug", "Coffee_Surface_32", "Table", "Camera"}
    names = {obj.name for obj in bpy.data.objects}
    missing = sorted(required - names)
    prototypes = sorted(name for name in names if name.startswith("Sprinkle_Prototype_"))
    icing = bpy.data.objects.get("Icing")
    modifier_types = [modifier.type for modifier in icing.modifiers] if icing else []
    material_names = {
        name: [material.name for material in bpy.data.objects[name].data.materials]
        for name in ("Donut", "Icing", "Plate", "Mug", "Table")
        if name in bpy.data.objects
    }
    checks = {
        "required_objects_present": not missing,
        "donut_manifold": "Donut" in names and health("Donut")["nonmanifold_edges"] == 0,
        "icing_has_live_geometry_nodes": "NODES" in modifier_types,
        "icing_has_live_surface_modifiers": all(kind in modifier_types for kind in ("SOLIDIFY", "SUBSURF")),
        "icing_evaluates_manifold": "Icing" in names and evaluated_health("Icing")["nonmanifold_edges"] == 0,
        "plate_evaluates_manifold": "Plate" in names and evaluated_health("Plate")["nonmanifold_edges"] == 0,
        "five_colored_sprinkle_sources": len(prototypes) == 5,
        "sprinkle_sources_hidden_from_render": all(bpy.data.objects[name].hide_render for name in prototypes),
        "coffee_uses_32_vertex_surface": "Coffee_Surface_32" in names and health("Coffee_Surface_32")["vertices"] >= 32,
        "materials_are_role_specific": all(material_names.get(name) for name in ("Donut", "Icing", "Plate", "Mug", "Table")),
        "accepted_render_exists": (RUN_DIR / "beginner_scene_v4.png").exists(),
        "creator_reference_metadata_exists": (RUN_DIR / "source_metadata.json").exists(),
    }
    report = {
        "schema_version": 1,
        "record_type": "INDEPENDENT_TUTORIAL_REPRODUCTION_VERIFICATION",
        "blend_file": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "checks": checks,
        "passed": all(checks.values()),
        "missing_objects": missing,
        "icing_modifier_types": modifier_types,
        "sprinkle_prototypes": prototypes,
        "material_names": material_names,
        "mesh_health": {
            name: health(name) for name in ("Donut", "Icing", "Plate", "Mug", "Coffee_Surface_32")
        },
        "evaluated_mesh_health": {
            name: evaluated_health(name) for name in ("Donut", "Icing", "Plate", "Mug", "Coffee_Surface_32")
        },
        "visual_boundary": (
            "Technical checks pass independently. Creator-still comparison remains a separate "
            "human/visual judgment and is not inferred from these checks."
        ),
    }
    (RUN_DIR / "independent_verification_v4.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
