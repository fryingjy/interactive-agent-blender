"""Exercise Blender-native solid, wireframe, normal, depth, and component-mask passes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender_ops.render_passes import render_diagnostic_pass


def main():
    out = ROOT / "runs" / "2026-08-10_visual-passes"
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene["scene_revision"] = 314

    bpy.ops.mesh.primitive_cube_add(location=(-0.45, 0, 0))
    body = bpy.context.object
    body.name = "Pass_Body"
    body.scale = (1.3, 0.65, 0.85)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = body.modifiers.new("Body Bevel", "BEVEL")
    bevel.width = 0.18
    bevel.segments = 3

    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.16, major_segments=24, minor_segments=8, location=(1.25, 0, 0))
    ring = bpy.context.object
    ring.name = "Pass_Ring"
    ring.rotation_euler.x = 1.57079632679

    names = [body.name, ring.name]
    records = []
    for pass_type in ("solid", "matcap", "wireframe", "normal", "depth", "component_mask"):
        records.append(render_diagnostic_pass(names, str(out / f"{pass_type}_front.png"), pass_type, view="front", resolution=256, margin=1.2))
    by_type = {record["pass_type"]: record for record in records if "pass_type" in record}
    assertions = {
        "all_files_exist": all((out / f"{kind}_front.png").exists() for kind in by_type),
        "all_tied_to_revision": all(record["scene_revision"] == 314 for record in records),
        "all_have_camera_metadata": all(record["projection"] == "ORTHO" and len(record["camera_location"]) == 3 for record in records),
        "wireframe_has_visible_edges": by_type["wireframe"]["foreground_fill_ratio"] > 0.0,
        "wireframe_sparser_than_solid": by_type["wireframe"]["foreground_fill_ratio"] < by_type["solid"]["foreground_fill_ratio"],
        "matcap_has_surface_variation": by_type["matcap"]["foreground_unique_colors_5bit"] >= 3,
        "normal_has_direction_colors": by_type["normal"]["foreground_unique_colors_5bit"] >= 3,
        "depth_has_gradient": by_type["depth"]["foreground_unique_colors_5bit"] >= 3,
        "component_mask_has_multiple_colors": by_type["component_mask"]["foreground_unique_colors_5bit"] >= 2,
    }
    report = {"lab": "blender_native_diagnostic_visual_passes", "records": records, "assertions": assertions, "pass": all(assertions.values())}
    (out / "visual_pass_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "visual_pass_lab.blend"))
    print("VISUAL_PASS_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
