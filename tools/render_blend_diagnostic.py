"""Render a Blender-native diagnostic pass from a saved .blend without saving it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from blender_ops.render_passes import render_diagnostic_pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blend", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("pass_type", choices=("solid", "matcap", "wireframe", "normal", "depth", "component_mask"))
    parser.add_argument("view", choices=("front", "back", "side", "left", "top", "bottom", "isometric"))
    parser.add_argument("objects", nargs="+")
    parser.add_argument("--frame-objects", nargs="+")
    parser.add_argument("--resolution", type=int, default=1000)
    parser.add_argument("--margin", type=float, default=1.15)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = render_diagnostic_pass(
        args.objects,
        str(args.output.resolve()),
        args.pass_type,
        view=args.view,
        resolution=args.resolution,
        margin=args.margin,
        frame_name=args.frame_objects or args.objects,
    )
    if result.get("error"):
        raise SystemExit(result["error"])
    report_path = args.output.with_suffix(".json")
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
