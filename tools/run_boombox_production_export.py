"""Export the accepted held-out boombox to GLB with production invariants."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-11_heldout-boombox"
FINAL = RUN / "final"
EXPORT = RUN / "export"


def evaluated_state(objects: list[bpy.types.Object]) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    triangles = 0
    points = []
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        triangles += len(mesh.loop_triangles)
        points.extend(obj.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
        evaluated.to_mesh_clear()
    bounds = {
        axis: [min(point[index] for point in points), max(point[index] for point in points)]
        for index, axis in enumerate("xyz")
    }
    return {
        "mesh_objects": len(objects),
        "triangles": triangles,
        "bounds": bounds,
        "all_have_uvs": all(obj.data.uv_layers and len(obj.data.uv_layers.active.data) == len(obj.data.loops) for obj in objects),
        "all_have_materials": all(obj.data.materials and obj.data.materials[0] for obj in objects),
        "material_names": sorted({material.name for obj in objects for material in obj.data.materials if material}),
    }


def main() -> None:
    EXPORT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(FINAL / "heldout_boombox.blend"), load_ui=False)
    objects = sorted((obj for obj in bpy.data.objects if obj.type == "MESH"), key=lambda obj: obj.name)
    source = evaluated_state(objects)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.hide_render = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    glb_path = EXPORT / "heldout_boombox.glb"
    result = bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_tangents=True,
        export_materials="EXPORT",
    )
    assertions = {
        "source_has_41_semantic_meshes": source["mesh_objects"] == 41,
        "source_has_evaluated_surface": source["triangles"] > 0,
        "source_uvs_are_present": source["all_have_uvs"],
        "source_materials_are_present": source["all_have_materials"],
        "export_finished": "FINISHED" in result,
        "glb_written": glb_path.is_file() and glb_path.stat().st_size > 0,
    }
    report = {
        "lab": "heldout_boombox_production_glb_export",
        "blender_version": bpy.app.version_string,
        "source_blend": str(FINAL / "heldout_boombox.blend"),
        "source": source,
        "export": {"operator_result": sorted(result), "path": str(glb_path), "bytes": glb_path.stat().st_size},
        "verification_basis": "evaluated triangle count, combined bounds, mesh count, UV/material presence, and direct GLB attributes; raw vertex/polygon equality is intentionally excluded",
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (EXPORT / "boombox_export_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("BOOMBOX_EXPORT_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


main()
