"""Render base-cage wire evidence for a named profile-authored body."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from render_passes import render_diagnostic_pass


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("expected BLEND OBJECT OUTPUT_DIR after --")
    blend, object_name, output = Path(args[0]).resolve(), args[1], Path(args[2]).resolve()
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    output.mkdir(parents=True, exist_ok=True)
    records = [
        render_diagnostic_pass(object_name, str(output / f"body_{view}_wire.png"), "wireframe", view=view, resolution=720, margin=1.2)
        for view in ("front", "isometric")
    ]
    (output / "topology_render_report.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps(records, indent=2))


main()
