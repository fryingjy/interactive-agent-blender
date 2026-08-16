"""Generic read-only beauty render of a .blend file's visible mesh/curve objects,
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
    color_mode = argv[3].lower() if len(argv) > 3 else "single"
    if color_mode not in {"single", "material", "silhouette"}:
        raise SystemExit("color_mode must be 'single', 'material', or 'silhouette'")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    # Curves are legitimate editable construction geometry (wire handles,
    # straps, trims). Their evaluated meshes can be framed and rendered just
    # like meshes; excluding them made valid curve assemblies disappear from
    # diagnostic renders and encouraged incorrect placement repairs.
    objs = [
        o for o in bpy.data.objects
        if o.type in {"MESH", "CURVE"} and not o.hide_render and not o.hide_get()
    ]
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

    # Some source files leave scene.render.image_settings.file_format stuck
    # on a movie format (FFMPEG) in a state that rejects direct reassignment
    # outright ("enum 'PNG' not found in ('FFMPEG')") even though PNG is a
    # normally-valid option -- found live on batarang.blend, not assumed.
    # Rendering through a brand new scene (linking only the objects and
    # camera actually needed) sidesteps whatever causes that instead of
    # fighting the source file's own scene state. bpy.ops.render.render's
    # own `scene` parameter targets it directly, no window/context switch
    # needed (there is no window at all in --background mode).
    render_scene = bpy.data.scenes.new("StudyRenderScene")
    for obj in objs:
        render_scene.collection.objects.link(obj)

    camera_data = bpy.data.cameras.new("StudyCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = diagonal * 1.15
    camera = bpy.data.objects.new("StudyCamera", camera_data)
    camera.location = center + direction * diagonal * 2.2
    camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    render_scene.collection.objects.link(camera)
    render_scene.camera = camera

    shading = render_scene.display.shading
    render_scene.render.engine = "BLENDER_WORKBENCH"
    shading.type = "SOLID"
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL" if color_mode == "material" else "SINGLE"
    if color_mode in {"single", "silhouette"}:
        shading.single_color = (0.55, 0.55, 0.58)
    if color_mode == "silhouette":
        # The alpha channel is the exact Workbench object silhouette. This
        # supports reference comparison without thresholding a shaded render.
        shading.single_color = (0.0, 0.0, 0.0)
        shading.light = "FLAT"
        shading.show_shadows = False
        shading.show_cavity = False
        render_scene.render.film_transparent = True
        render_scene.render.image_settings.color_mode = "RGBA"
    else:
        shading.show_shadows = True
        shading.show_cavity = True
    shading.cavity_type = "BOTH"
    render_scene.render.resolution_x = 1000
    render_scene.render.resolution_y = 1000
    render_scene.render.image_settings.file_format = "PNG"
    render_scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True, scene=render_scene.name)
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
