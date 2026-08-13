"""One-off beauty render of the saved wrench candidate, matching the same
Workbench SOLID/STUDIO/cavity style used for every reference beauty render
in this project (see render_multiview_reference.py's render_beauty()), for
visual consistency in reporting."""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    blend_path, out_path = argv[0], Path(argv[1])
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    obj = bpy.data.objects["Wrench_Body"]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [obj.matrix_world @ v.co for v in mesh.vertices]
    evaluated.to_mesh_clear()
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (minimum + maximum) * 0.5
    diagonal = (maximum - minimum).length

    direction = Vector((1.0, -1.0, 0.8)).normalized()
    bpy.ops.object.camera_add(location=center + direction * diagonal * 2.2)
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = diagonal * 1.12
    camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    scene = bpy.context.scene
    scene.camera = camera
    for o in bpy.data.objects:
        o.hide_render = o not in (obj,) and o is not camera and o.type != "LIGHT"
    shading = scene.display.shading
    scene.render.engine = "BLENDER_WORKBENCH"
    shading.type = "SOLID"
    shading.light = "STUDIO"
    shading.color_type = "SINGLE"
    shading.single_color = (0.32, 0.36, 0.42)
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
