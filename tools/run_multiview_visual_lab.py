"""Render fixed-frame reference and candidate silhouettes from three views."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[1]
BLENDER_OPS = REPO_ROOT / "blender_ops"
if str(BLENDER_OPS) not in sys.path:
    sys.path.insert(0, str(BLENDER_OPS))

from render_passes import render_silhouette


def output_directory():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected one OUTPUT_DIR after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def rounded_box(name, dimensions, bevel_width):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("Edge Softening", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = 3
    return obj


def main():
    output = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    rounded_box("Visual_Reference", (4.0, 2.0, 2.0), 0.25)
    rounded_box("Visual_Initial", (4.6, 1.6, 2.3), 0.12)
    rounded_box("Visual_Corrected", (4.05, 1.98, 2.02), 0.24)

    manifests = {"initial": {}, "corrected": {}}
    render_records = []
    for view in ("front", "side", "top"):
        reference_path = output / f"reference_{view}.png"
        if not reference_path.exists():
            render_records.append(render_silhouette("Visual_Reference", str(reference_path), view=view, resolution=256, margin=1.2, frame_name="Visual_Reference"))
        for label, object_name in (("initial", "Visual_Initial"), ("corrected", "Visual_Corrected")):
            candidate_path = output / f"{label}_{view}.png"
            render_records.append(render_silhouette(object_name, str(candidate_path), view=view, resolution=256, margin=1.2, frame_name="Visual_Reference"))
            manifests[label][view] = {"reference": str(reference_path), "candidate": str(candidate_path)}
    for label, manifest in manifests.items():
        (output / f"manifest_{label}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "render_report.json").write_text(json.dumps(render_records, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "multiview_visual_lab.blend"))
    print(json.dumps({"manifests": manifests, "renders": render_records}, indent=2))


if __name__ == "__main__":
    main()
