"""Set up front/side/top Image Empties for a modeling reference, per
docs/REFERENCE_PROTOCOL.md's "Blender reference setup" section --
axis-aligned, orthographic-facing, locked against accidental selection/move.

Run as:
    blender --background --python tools/build_reference_empties.py -- \
        <front_png> <side_png> <top_png> <out_blend> <ortho_scale_meters>
"""
import math
import sys
from pathlib import Path

import bpy


def make_ref_empty(name, image_path, rotation_euler, scale):
    img = bpy.data.images.load(image_path)
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "IMAGE"
    empty.data = img
    empty.empty_display_size = scale
    empty.rotation_euler = rotation_euler
    empty.use_empty_image_alpha = True
    empty.color[3] = 0.9
    # Prevent the exact accident the protocol calls out: nudging a reference
    # plane out of alignment mid-session without noticing.
    empty.lock_location = (True, True, True)
    empty.lock_rotation = (True, True, True)
    empty.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(empty)
    return empty


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    front_png, side_png, top_png, out_blend, ortho_scale = argv
    ortho_scale = float(ortho_scale)

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    # Front: faces -Y, lies in the X-Z plane.
    make_ref_empty("Ref_Front", front_png, (math.radians(90), 0, 0), ortho_scale)
    # Side: faces -X (or +X depending on handedness), lies in the Y-Z plane.
    make_ref_empty("Ref_Side", side_png, (math.radians(90), 0, math.radians(90)), ortho_scale)
    # Top: faces +Z (looking down), lies in the X-Y plane.
    make_ref_empty("Ref_Top", top_png, (0, 0, 0), ortho_scale)

    Path(out_blend).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print("SAVED:", out_blend)


if __name__ == "__main__":
    main()
