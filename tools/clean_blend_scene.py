"""Remove undeclared scene objects from a saved Blender file.

This is production cleanup, not a modeling generator. Run Blender with the
source file already open and pass an explicit allowlist plus output path:

    blender --background source.blend --python tools/clean_blend_scene.py -- \
        --keep AssetName --output cleaned.blend --report cleanup.json

The explicit keep list makes accidental broad deletion fail closed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    source_blend = bpy.data.filepath
    keep = set(args.keep)
    present = {obj.name for obj in bpy.data.objects}
    missing = sorted(keep - present)
    if missing:
        raise ValueError(f"refusing cleanup because keep objects are missing: {missing}")
    removed = []
    for obj in list(bpy.data.objects):
        if obj.name not in keep:
            removed.append({"name": obj.name, "type": obj.type})
            bpy.data.objects.remove(obj, do_unlink=True)
    remaining = sorted(obj.name for obj in bpy.data.objects)
    if set(remaining) != keep:
        raise RuntimeError(f"cleanup postcondition failed: remaining={remaining}, keep={sorted(keep)}")

    removed_datablocks = {}
    for label, collection in (
        ("meshes", bpy.data.meshes),
        ("cameras", bpy.data.cameras),
        ("lights", bpy.data.lights),
        ("materials", bpy.data.materials),
    ):
        names = [item.name for item in collection if item.users == 0]
        for item in list(collection):
            if item.users == 0:
                collection.remove(item)
        removed_datablocks[label] = sorted(names)
    viewer_images = [
        image for image in bpy.data.images
        if image.users == 0 or image.type in {"RENDER_RESULT", "COMPOSITING"}
    ]
    removed_datablocks["images"] = sorted(image.name for image in viewer_images)
    for image in viewer_images:
        bpy.data.images.remove(image)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    report = {
        "schema_version": 1,
        "record_type": "BLEND_SCENE_ALLOWLIST_CLEANUP",
        "source_blend": source_blend,
        "output_blend": str(output),
        "kept": remaining,
        "removed": removed,
        "removed_orphan_datablocks": removed_datablocks,
        "pass": True,
        "claim_boundary": "Scene-object allowlist cleanup; does not assess mesh or visual quality.",
    }
    destination = args.report.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("SCENE_CLEANUP_RESULT:" + json.dumps(report))


main()
