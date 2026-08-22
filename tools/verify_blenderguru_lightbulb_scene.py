"""Fresh-process technical verification for the Blender Guru lightbulb lesson."""

from __future__ import annotations

import json
from pathlib import Path

import bmesh
import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = REPO_ROOT / "runs" / "2026-08-22_tutorial-blenderguru-lightbulb"


def mesh_health(name: str) -> dict[str, int]:
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


def main() -> None:
    names = {obj.name for obj in bpy.data.objects}
    required_collections = {"BULB_MASTER", "BULB_INSTANCES", "ENVIRONMENT", "LIGHTING"}
    master_names = {
        "Bulb_Glass_Envelope",
        "Bulb_Metal_Shell",
        "Bulb_Contact_Tip",
        "Bulb_Internal_Stem",
        "Bulb_Lead_Left",
        "Bulb_Lead_Right",
        "Bulb_Tungsten_Coil",
        "Bulb_Screw_Thread",
    }
    assembly_roots = sorted(
        obj.name
        for obj in bpy.data.objects
        if obj.type == "EMPTY"
        and (obj.name == "Master_Bulb_Root" or obj.name.startswith("Bulb_Copy_") or obj.name == "Hero_Glowing_Bulb")
    )
    glass = bpy.data.objects.get("Bulb_Glass_Envelope")
    thread = bpy.data.objects.get("Bulb_Screw_Thread")
    hero_glass = bpy.data.objects.get("Hero_Glowing_Bulb_Bulb_Glass_Envelope")
    compositor = bpy.context.scene.compositing_node_group
    thread_points = 0
    if thread and thread.type == "CURVE":
        thread_points = sum(len(spline.bezier_points) + len(spline.points) for spline in thread.data.splines)
    hero_materials = [material.name for material in hero_glass.data.materials] if hero_glass else []
    checks = {
        "required_collections_present": required_collections <= set(bpy.data.collections.keys()),
        "master_components_present": master_names <= names,
        "eighteen_bulb_assemblies_present": len(assembly_roots) == 18,
        "glass_is_connected_and_manifold": bool(glass) and mesh_health(glass.name)["nonmanifold_edges"] == 0,
        "glass_keeps_live_subdivision": bool(glass) and any(modifier.type == "SUBSURF" for modifier in glass.modifiers),
        "thread_is_live_bezier_curve": bool(thread)
        and thread.type == "CURVE"
        and any(spline.type == "BEZIER" for spline in thread.data.splines),
        "thread_is_fine_enough": bool(thread)
        and abs(thread.data.bevel_depth - 0.05) < 0.001
        and thread_points >= 37,
        "hero_uses_separate_glow_glass": "Hero_Glow_Glass" in hero_materials,
        "compositor_glare_is_live": bool(compositor)
        and any(node.bl_idname == "CompositorNodeGlare" for node in compositor.nodes),
        "accepted_render_exists": (RUN_DIR / "lightbulb_scene_v4.png").exists(),
        "creator_source_record_exists": (RUN_DIR / "source_metadata.json").exists(),
    }
    report = {
        "schema_version": 1,
        "record_type": "INDEPENDENT_TUTORIAL_REPRODUCTION_VERIFICATION",
        "blend_file": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "checks": checks,
        "passed": all(checks.values()),
        "assembly_roots": assembly_roots,
        "thread_point_count": thread_points,
        "thread_bevel_depth": thread.data.bevel_depth if thread else None,
        "glass_base_health": mesh_health(glass.name) if glass else None,
        "hero_glass_materials": hero_materials,
        "visual_boundary": (
            "This verifier establishes saved-file structure and technical health only. The v4 "
            "scene remains a failed visual-fidelity gate after direct comparison with the creator result."
        ),
    }
    output = RUN_DIR / "independent_verification_v4.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
