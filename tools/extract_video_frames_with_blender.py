"""Extract exact video checkpoints with Blender's bundled decoder.

Run headlessly, for example::

    blender --background --python tools/extract_video_frames_with_blender.py -- \
        --input lesson.webm --output-dir frames --seconds 151 158 166 178

This deliberately keeps no copy of the source media.  It is useful when the
host Python runtime does not have a video decoder, while Blender is available.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import bpy


def parse_args() -> argparse.Namespace:
    argv = list(__import__("sys").argv)
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seconds", required=True, type=float, nargs="+")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    source = args.input.resolve()
    output_dir = args.output_dir.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    editor = scene.sequence_editor_create()
    strip = editor.strips.new_movie(name="source", filepath=str(source), channel=1, frame_start=1)

    # Blender resolves source dimensions/fps through its own FFmpeg build.
    scene.render.resolution_x = strip.elements[0].orig_width
    scene.render.resolution_y = strip.elements[0].orig_height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.use_sequencer = True

    fps = scene.render.fps / scene.render.fps_base
    checkpoints = []
    for seconds in args.seconds:
        frame = max(1, round(seconds * fps) + 1)
        scene.frame_set(frame)
        filename = f"frame_{seconds:08.3f}s.png"
        target = output_dir / filename
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        if not target.is_file():
            raise RuntimeError(f"Blender did not write {target}")
        checkpoints.append(
            {
                "requested_seconds": seconds,
                "frame": frame,
                "actual_seconds": (frame - 1) / fps,
                "path": str(target),
            }
        )

    report = {
        "decoder": "Blender Video Sequence Editor / bundled FFmpeg",
        "source_filename": source.name,
        "source_path": "temporary source path intentionally omitted from retained evidence",
        "fps": fps,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "checkpoints": checkpoints,
        "source_media_retained_by_tool": False,
    }
    (output_dir / "frame_extraction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
