"""Temporary Workbench inspection scene; the source scene is not restyled."""
from pathlib import Path

import bpy

from modeler.runtime import mesh_object, vector


def render(request):
    if set(request) != {'action', 'object', 'eye', 'target', 'scale', 'path'}:
        raise ValueError('Unexpected render fields')
    path = Path(request['path']).resolve()
    if path.exists() or path.suffix.lower() != '.png':
        raise ValueError('Render needs a new PNG path')
    eye, target = vector(request['eye']), vector(request['target'])
    scale = request['scale']
    if type(scale) not in (int, float) or not 0 < scale < 1e6 or (eye-target).length < 1e-6:
        raise ValueError('Invalid camera')
    obj = mesh_object(request['object'])
    scene = bpy.data.scenes.new('TemporaryInspection')
    camera_data = bpy.data.cameras.new('TemporaryInspection')
    camera = bpy.data.objects.new('TemporaryInspection', camera_data)
    try:
        scene.collection.objects.link(obj)
        scene.collection.objects.link(camera)
        camera.location = eye
        camera.rotation_euler = (target-eye).to_track_quat('-Z', 'Y').to_euler()
        camera_data.type = 'ORTHO'
        camera_data.ortho_scale = scale
        scene.camera = camera
        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.render.resolution_x = scene.render.resolution_y = 512
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        shading = scene.display.shading
        shading.light = 'STUDIO'
        shading.color_type = 'SINGLE'
        shading.single_color = (.65, .65, .65)
        shading.show_shadows = False
        shading.show_cavity = False
        path.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, scene=scene.name)
    finally:
        bpy.data.scenes.remove(scene)
        bpy.data.objects.remove(camera, do_unlink=True)
        bpy.data.cameras.remove(camera_data)
    return {'path': str(path), 'projection': 'ORTHO', 'quality_accepted': False}
