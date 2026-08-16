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

import json
import os

import bmesh
import bpy
import mathutils

_VIEW_VECTORS = {
    "front": mathutils.Vector((0.0, -1.0, 0.0)),
    "back": mathutils.Vector((0.0, 1.0, 0.0)),
    "side": mathutils.Vector((1.0, 0.0, 0.0)),
    "left": mathutils.Vector((-1.0, 0.0, 0.0)),
    "top": mathutils.Vector((0.0, 0.0, 1.0)),
    "bottom": mathutils.Vector((0.0, 0.0, -1.0)),
    "isometric": mathutils.Vector((1.0, -1.0, 1.0)).normalized(),
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
        if obj is None or obj.type not in {"MESH", "CURVE"}:
            return {"error": f"'{n}' is not renderable evaluated geometry"}
        objs.append(obj)
    if view not in _VIEW_VECTORS:
        return {"error": f"view must be one of {sorted(_VIEW_VECTORS)}"}

    frame_names = names if frame_name is None else ([frame_name] if isinstance(frame_name, str) else list(frame_name))
    frame_objs = []
    for frame_object_name in frame_names:
        frame_obj = bpy.data.objects.get(frame_object_name)
        if frame_obj is None or frame_obj.type not in {"MESH", "CURVE"}:
            return {"error": f"frame object '{frame_object_name}' is not renderable evaluated geometry"}
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


def _diagnostic_mesh_copy(obj, pass_type, direction, depth_range):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    evaluated = obj_eval.to_mesh()
    mesh = evaluated.copy()
    obj_eval.to_mesh_clear()
    temp = bpy.data.objects.new(f"__visual_{pass_type}_{obj.name}", mesh)
    bpy.context.scene.collection.objects.link(temp)
    temp.matrix_world = obj.matrix_world.copy()
    if pass_type == "wireframe":
        local_diag = mathutils.Vector(mesh.bounds_max - mesh.bounds_min).length if hasattr(mesh, "bounds_max") else max(obj.dimensions.length, 1.0)
        wire = temp.modifiers.new("Diagnostic Wire", "WIREFRAME")
        wire.thickness = max(local_diag * 0.004, 0.002)
        wire.use_replace = True
        return temp
    attribute = mesh.color_attributes.new(name="visual_pass_color", type="BYTE_COLOR", domain="CORNER")
    mesh.color_attributes.active_color = attribute
    if pass_type == "normal":
        normal_matrix = obj.matrix_world.to_3x3().inverted().transposed()
        for polygon in mesh.polygons:
            normal = (normal_matrix @ polygon.normal).normalized()
            color = (normal.x * 0.5 + 0.5, normal.y * 0.5 + 0.5, normal.z * 0.5 + 0.5, 1.0)
            for loop_index in polygon.loop_indices:
                attribute.data[loop_index].color = color
    else:
        depth_min, depth_max = depth_range
        span = max(depth_max - depth_min, 1e-8)
        for loop in mesh.loops:
            world = obj.matrix_world @ mesh.vertices[loop.vertex_index].co
            value = (world.dot(direction) - depth_min) / span
            attribute.data[loop.index].color = (value, value, value, 1.0)
    return temp


def render_diagnostic_pass(name, output_path, pass_type, view="front", resolution=512, margin=1.15, frame_name=None):
    """Render a controlled Blender-native diagnostic pass.

    Supported passes are `solid`, `matcap`, `wireframe`, `normal`, `depth`, and `component_mask`. Normal and
    depth colors are generated on temporary copies of the modifier-evaluated meshes; source objects
    and scene settings are restored. Camera/projection metadata and scene revision are returned so
    an image cannot become detached from the state that produced it.
    """
    valid_passes = {"solid", "matcap", "wireframe", "normal", "depth", "component_mask"}
    if pass_type not in valid_passes:
        return {"error": f"pass_type must be one of {sorted(valid_passes)}"}
    names = [name] if isinstance(name, str) else list(name)
    objs = []
    for object_name in names:
        obj = bpy.data.objects.get(object_name)
        if obj is None or obj.type not in {"MESH", "CURVE"}:
            return {"error": f"'{object_name}' is not renderable evaluated geometry"}
        objs.append(obj)
    if view not in _VIEW_VECTORS:
        return {"error": f"view must be one of {sorted(_VIEW_VECTORS)}"}
    frame_names = names if frame_name is None else ([frame_name] if isinstance(frame_name, str) else list(frame_name))
    frame_objs = []
    for object_name in frame_names:
        obj = bpy.data.objects.get(object_name)
        if obj is None or obj.type not in {"MESH", "CURVE"}:
            return {"error": f"frame object '{object_name}' is not renderable evaluated geometry"}
        frame_objs.append(obj)
    bmin = bmax = None
    all_frame_coords = []
    for obj in frame_objs:
        obj_min, obj_max = _evaluated_bbox_world(obj)
        if obj_min is None:
            continue
        bmin = obj_min if bmin is None else mathutils.Vector(map(min, bmin, obj_min))
        bmax = obj_max if bmax is None else mathutils.Vector(map(max, bmax, obj_max))
        all_frame_coords.extend([obj_min, obj_max])
    if bmin is None:
        return {"error": "no evaluated vertices across the frame objects"}
    center = (bmin + bmax) / 2.0
    diag = (bmax - bmin).length
    if diag < 1e-6:
        return {"error": "combined evaluated bounding box is degenerate"}
    direction = _VIEW_VECTORS[view]
    depth_values = [point.dot(direction) for point in all_frame_coords]
    depth_range = (min(depth_values), max(depth_values))

    temp_objects = []
    render_objects = objs
    if pass_type in {"wireframe", "normal", "depth"}:
        temp_objects = [_diagnostic_mesh_copy(obj, pass_type, direction, depth_range) for obj in objs]
        render_objects = temp_objects

    cam_data = bpy.data.cameras.new(name="__diagnostic_cam__")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = diag * margin
    cam_obj = bpy.data.objects.new("__diagnostic_cam__", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = center + direction * diag * 2.0
    cam_obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    camera_location = list(cam_obj.location)

    scene = bpy.context.scene
    shading = scene.display.shading
    state = {
        "camera": scene.camera,
        "engine": scene.render.engine,
        "resolution": (scene.render.resolution_x, scene.render.resolution_y),
        "film_transparent": scene.render.film_transparent,
        "filepath": scene.render.filepath,
        "file_format": scene.render.image_settings.file_format,
        "color_mode": scene.render.image_settings.color_mode,
        "shading_type": shading.type,
        "color_type": shading.color_type,
        "single_color": tuple(shading.single_color),
        "light": shading.light,
        "show_shadows": shading.show_shadows,
        "show_cavity": shading.show_cavity,
    }
    other_objects = [item for item in bpy.data.objects if item not in render_objects and item is not cam_obj]
    hidden = {item.name: item.hide_render for item in other_objects}
    object_colors = {obj.name: tuple(obj.color) for obj in objs}
    for item in other_objects:
        item.hide_render = True
    if pass_type == "component_mask":
        palette = ((1.0, 0.1, 0.1, 1.0), (0.1, 1.0, 0.1, 1.0), (0.1, 0.1, 1.0, 1.0), (1.0, 1.0, 0.1, 1.0))
        for index, obj in enumerate(objs):
            obj.color = palette[index % len(palette)]
    try:
        scene.camera = cam_obj
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.filepath = output_path
        shading.type = "SOLID"
        # MatCap is intentionally a fast Solid-mode review pass: useful for
        # highlight continuity, missing bevels, faceting, and soft corners
        # without a material/light/render-engine setup. It is visual evidence,
        # not a substitute for evaluated topology or a beauty render.
        shading.light = "MATCAP" if pass_type == "matcap" else ("STUDIO" if pass_type == "solid" else "FLAT")
        shading.show_shadows = pass_type in {"solid", "matcap"}
        shading.show_cavity = pass_type in {"solid", "matcap"}
        if pass_type in {"normal", "depth"}:
            shading.color_type = "VERTEX"
        elif pass_type == "component_mask":
            shading.color_type = "OBJECT"
        else:
            shading.color_type = "SINGLE"
            shading.single_color = (0.55, 0.55, 0.55) if pass_type in {"solid", "matcap"} else (0.9, 0.9, 0.9)
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        bpy.ops.render.render(write_still=True)
    finally:
        scene.camera = state["camera"]
        scene.render.engine = state["engine"]
        scene.render.resolution_x, scene.render.resolution_y = state["resolution"]
        scene.render.film_transparent = state["film_transparent"]
        scene.render.filepath = state["filepath"]
        scene.render.image_settings.file_format = state["file_format"]
        scene.render.image_settings.color_mode = state["color_mode"]
        shading.type = state["shading_type"]
        shading.color_type = state["color_type"]
        shading.single_color = state["single_color"]
        shading.light = state["light"]
        shading.show_shadows = state["show_shadows"]
        shading.show_cavity = state["show_cavity"]
        for item in other_objects:
            item.hide_render = hidden[item.name]
        for obj in objs:
            obj.color = object_colors[obj.name]
        for temp in temp_objects:
            mesh = temp.data
            bpy.data.objects.remove(temp, do_unlink=True)
            bpy.data.meshes.remove(mesh)
        bpy.data.objects.remove(cam_obj, do_unlink=True)
        bpy.data.cameras.remove(cam_data)

    image = bpy.data.images.load(output_path)
    try:
        pixels = image.pixels[:]
        alpha = pixels[3::4]
        rgb = list(zip(pixels[0::4], pixels[1::4], pixels[2::4]))
        foreground = [color for color, a in zip(rgb, alpha) if a > 0.5]
        unique_quantized = len({tuple(round(channel * 31) for channel in color) for color in foreground})
        fill_ratio = sum(a > 0.5 for a in alpha) / len(alpha) if alpha else 0.0
        dominant = {
            "red": sum(r > g * 1.2 and r > b * 1.2 for r, g, b in foreground),
            "green": sum(g > r * 1.2 and g > b * 1.2 for r, g, b in foreground),
            "blue": sum(b > r * 1.2 and b > g * 1.2 for r, g, b in foreground),
        }
    finally:
        bpy.data.images.remove(image)
    return {
        "output_path": output_path,
        "pass_type": pass_type,
        "view": view,
        "projection": "ORTHO",
        "resolution": [resolution, resolution],
        "target_objects": names,
        "frame_objects": frame_names,
        "camera_location": camera_location,
        "camera_ortho_scale": diag * margin,
        "scene_revision": scene.get("scene_revision"),
        "foreground_fill_ratio": round(fill_ratio, 6),
        "foreground_unique_colors_5bit": unique_quantized,
        "dominant_channel_pixel_counts": dominant,
    }


def _object_from_face_group(source_obj, faces, name):
    source_verts = sorted({vert for face in faces for vert in face.verts}, key=lambda vert: vert.index)
    index = {vert: position for position, vert in enumerate(source_verts)}
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(
        [tuple(vert.co) for vert in source_verts], [],
        [[index[vert] for vert in face.verts] for face in faces],
    )
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source_obj.matrix_world.copy()
    return obj


def render_semantic_region(name, region_id, output_path, view="front", resolution=512, margin=1.15):
    """Render one persistent-ID face region against the rest of its base cage.

    The pass is explicitly base-cage evidence because evaluated modifiers do not preserve a stable
    one-to-one face-ID mapping. It validates the region before rendering and reports missing IDs.
    """
    source = bpy.data.objects.get(name)
    if source is None or source.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    try:
        regions = json.loads(source.get("agent_semantic_regions", "{}"))
    except (TypeError, json.JSONDecodeError):
        regions = {}
    region = regions.get(region_id)
    if region is None:
        return {"error": f"no region '{region_id}' on '{name}'"}
    target_ids = set(region.get("face_ids", []))
    if not target_ids:
        return {"error": f"region '{region_id}' has no face IDs"}
    bm = bmesh.new()
    bm.from_mesh(source.data)
    bm.faces.ensure_lookup_table()
    layer = bm.faces.layers.int.get("agent_face_id")
    if layer is None:
        bm.free()
        return {"error": f"'{name}' has no persistent face-ID layer"}
    found_ids = {face[layer] for face in bm.faces}
    missing = sorted(target_ids - found_ids)
    if missing:
        bm.free()
        return {"error": "semantic region is stale", "missing_face_ids": missing}
    region_faces = [face for face in bm.faces if face[layer] in target_ids]
    context_faces = [face for face in bm.faces if face[layer] not in target_ids]
    temp_objects = []
    try:
        if context_faces:
            temp_objects.append(_object_from_face_group(source, context_faces, "__region_context__"))
        temp_objects.append(_object_from_face_group(source, region_faces, "__region_target__"))
        result = render_diagnostic_pass(
            [obj.name for obj in temp_objects], output_path, "component_mask",
            view=view, resolution=resolution, margin=margin, frame_name=name,
        )
    finally:
        bm.free()
        for obj in temp_objects:
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(mesh)
    result.update({
        "pass_type": "semantic_region",
        "source_object": name,
        "region_id": region_id,
        "region_role": region.get("role"),
        "region_face_ids": sorted(target_ids),
        "region_face_count": len(region_faces),
        "context_face_count": len(context_faces),
        "geometry_source": "BASE_CAGE",
        "missing_face_ids": [],
    })
    return result
