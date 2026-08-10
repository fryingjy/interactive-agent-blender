"""Blender-native visual passes -- render_silhouette() so far.

This is new territory for the project: every prior tool reads mesh DATA
(vertices, edges, faces, custom attribute layers), never pixels. That was a
deliberate founding constraint while the closed-loop typed-decision runtime
was being proven out. The master directive (docs/MASTER_DIRECTIVE.md,
especially sections 11 and 12) requires Blender-native rendering for
actual image-reference modeling -- a real
reference photo cannot be compared against a mesh using vertex/face counts
alone, it needs a rendered projection to compare against.

"Blender-native" specifically means bpy.ops.render.render() through
Blender's own render engine (Workbench, chosen for speed and because it
supports flat/no-lighting shading directly via scene.display.shading,
without needing a full material/lighting setup) -- not a screenshot of the
GUI window, which this project has never done and still doesn't.

render_silhouette() renders a single orthographic view with a transparent
background and a flat, unlit fill color, so the alpha channel of the output
PNG directly IS the silhouette mask -- no thresholding or post-processing
of a lit/shaded image required.
"""

import math
import os

import bpy
import mathutils

_VIEW_VECTORS = {
    "front": mathutils.Vector((0.0, -1.0, 0.0)),
    "side": mathutils.Vector((1.0, 0.0, 0.0)),
    "top": mathutils.Vector((0.0, 0.0, 1.0)),
}


def _evaluated_bbox_world(obj):
    """World-space bounding box of the modifier-EVALUATED mesh, not the
    control cage -- the silhouette must reflect what a Subdivision Surface
    (or any other modifier) actually produces, matching evaluated_probe.py's
    same reasoning for mesh_health/surface_quality."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    coords = [obj.matrix_world @ v.co for v in mesh_eval.vertices]
    obj_eval.to_mesh_clear()
    if not coords:
        return None, None
    xs, ys, zs = (c.x for c in coords), (c.y for c in coords), (c.z for c in coords)
    bmin = mathutils.Vector((min(xs), min(ys), min(zs)))
    xs, ys, zs = (c.x for c in coords), (c.y for c in coords), (c.z for c in coords)
    bmax = mathutils.Vector((max(xs), max(ys), max(zs)))
    return bmin, bmax


def render_silhouette(name, output_path, view="front", resolution=512, margin=1.15, frame_name=None):
    """Render a flat, unlit, transparent-background orthographic silhouette
    of object(s) `name`'s evaluated mesh to `output_path` (PNG). `name` may
    be a single object name or a list of names -- a multi-component prop
    (e.g. a dome + band + buttons modeled as separate objects, which this
    project does for anything that isn't a single continuous mesh) renders
    as one combined silhouette across all of them, framed to their combined
    bounding box. Restores every scene/render/shading setting it touches
    and removes the temporary camera it creates -- callers should not find
    the scene altered by having called this."""
    names = [name] if isinstance(name, str) else list(name)
    objs = []
    for n in names:
        obj = bpy.data.objects.get(n)
        if obj is None or obj.type != "MESH":
            return {"error": f"'{n}' is not a mesh object"}
        objs.append(obj)
    if view not in _VIEW_VECTORS:
        return {"error": f"view must be one of {sorted(_VIEW_VECTORS)}"}

    frame_names = names if frame_name is None else ([frame_name] if isinstance(frame_name, str) else list(frame_name))
    frame_objs = []
    for frame_object_name in frame_names:
        frame_obj = bpy.data.objects.get(frame_object_name)
        if frame_obj is None or frame_obj.type != "MESH":
            return {"error": f"frame object '{frame_object_name}' is not a mesh object"}
        frame_objs.append(frame_obj)

    bmin = bmax = None
    for obj in frame_objs:
        obj_min, obj_max = _evaluated_bbox_world(obj)
        if obj_min is None:
            continue
        bmin = obj_min if bmin is None else mathutils.Vector(map(min, bmin, obj_min))
        bmax = obj_max if bmax is None else mathutils.Vector(map(max, bmax, obj_max))
    if bmin is None:
        return {"error": "no evaluated vertices across the given object(s)"}
    center = (bmin + bmax) / 2.0
    diag = (bmax - bmin).length
    if diag < 1e-6:
        return {"error": "combined evaluated bounding box is degenerate"}

    direction = _VIEW_VECTORS[view]
    cam_data = bpy.data.cameras.new(name="__silhouette_cam__")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = diag * margin
    cam_obj = bpy.data.objects.new("__silhouette_cam__", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = center + direction * diag * 2.0
    # Camera looks down its local -Z; aligning local +Z to `direction` means
    # local -Z (the view direction) points back toward the object.
    cam_obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()

    scene = bpy.context.scene
    prev_camera = scene.camera
    prev_engine = scene.render.engine
    prev_res_x, prev_res_y = scene.render.resolution_x, scene.render.resolution_y
    prev_film_transparent = scene.render.film_transparent
    prev_filepath = scene.render.filepath
    prev_file_format = scene.render.image_settings.file_format
    prev_color_mode = scene.render.image_settings.color_mode

    shading = scene.display.shading
    prev_color_type = shading.color_type
    prev_single_color = tuple(shading.single_color)
    prev_light = shading.light

    # CORRECTION (found live, first real test): an orthographic camera has
    # no perspective foreshortening, so every OTHER object in the scene
    # that merely falls within the camera's depth range along the view
    # axis -- true of this project's whole prop lineup, all laid out along
    # world Y at different offsets purely for organizational convenience --
    # renders into the same frame if its own X/Z footprint overlaps the
    # target's. The first real silhouette render silently included pieces
    # of Mug/SpeakerEnclosure alongside SoapDish because of exactly this;
    # framing the camera on the target alone does not exclude other scene
    # content from the render. Every other object must be temporarily
    # excluded via hide_render, not just left to the camera framing.
    other_objects = [o for o in bpy.data.objects if o not in objs and o is not cam_obj]
    prev_hide_render = {o.name: o.hide_render for o in other_objects}
    for o in other_objects:
        o.hide_render = True

    try:
        scene.camera = cam_obj
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.filepath = output_path

        shading.color_type = "SINGLE"
        shading.single_color = (0.0, 0.0, 0.0)
        shading.light = "FLAT"

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        bpy.ops.render.render(write_still=True)
    finally:
        scene.camera = prev_camera
        scene.render.engine = prev_engine
        scene.render.resolution_x, scene.render.resolution_y = prev_res_x, prev_res_y
        scene.render.film_transparent = prev_film_transparent
        scene.render.filepath = prev_filepath
        scene.render.image_settings.file_format = prev_file_format
        scene.render.image_settings.color_mode = prev_color_mode
        shading.color_type = prev_color_type
        shading.single_color = prev_single_color
        shading.light = prev_light
        for o in other_objects:
            o.hide_render = prev_hide_render[o.name]
        bpy.data.objects.remove(cam_obj, do_unlink=True)
        bpy.data.cameras.remove(cam_data)

    img = bpy.data.images.load(output_path)
    try:
        px = img.pixels[:]
        alpha = px[3::4]
        filled = sum(1 for a in alpha if a > 0.5)
        total = len(alpha)
    finally:
        bpy.data.images.remove(img)

    return {
        "output_path": output_path,
        "view": view,
        "resolution": resolution,
        "frame_objects": frame_names,
        "silhouette_fill_ratio": round(filled / total, 4) if total else None,
    }
