"""Generic read-only beauty render of a .blend file's visible mesh objects,
for studying professional reference files per docs/BLEND_FILE_STUDY_PROTOCOL.md.
Never saves the source file."""
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    blend_path, out_path = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    view = argv[2] if len(argv) > 2 else "iso"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    objs = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and not o.hide_get()]
    if not objs:
        raise SystemExit("no visible mesh objects")

    depsgraph = bpy.context.evaluated_depsgraph_get()
    points = []
    for obj in objs:
        ev = obj.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        points.extend(obj.matrix_world @ v.co for v in mesh.vertices)
        ev.to_mesh_clear()
    if not points:
        raise SystemExit("no evaluated geometry")
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (minimum + maximum) * 0.5
    diagonal = (maximum - minimum).length or 1.0

    directions = {
        "iso": Vector((1.0, -1.0, 0.8)).normalized(),
        "front": Vector((0.0, -1.0, 0.0)),
        "side": Vector((1.0, 0.0, 0.0)),
        "top": Vector((0.0, 0.0, 1.0)),
    }
    direction = directions.get(view, directions["iso"])

    bpy.ops.object.camera_add(location=center + direction * diagonal * 2.2)
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = diagonal * 1.15
    camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    scene = bpy.context.scene
    scene.camera = camera

    for o in bpy.data.objects:
        o.hide_render = o not in objs and o is not camera and o.type != "LIGHT"

    shading = scene.display.shading
    scene.render.engine = "BLENDER_WORKBENCH"
    shading.type = "SOLID"
    shading.light = "STUDIO"
    shading.color_type = "SINGLE"
    shading.single_color = (0.55, 0.55, 0.58)
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
