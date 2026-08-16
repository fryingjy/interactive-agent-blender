"""Curve-object primitives -- for geometry a mesh primitive can't represent
directly: a path that wraps, overlaps, and tapers along its length.

Built after a real, documented mistake: the first pass at the gadget
wristband used a torus (a symmetric ring) to approximate a strap that
actually wraps around, overlaps itself, has a buckle-hole gap, and tapers
to a closed point at one end -- verified by pixel-measuring the reference
image (tools/measure_reference.py), not by eye. A torus cannot represent
any of that. Blender's Curve object (bevel_depth for a 3D cross-section
along the path, taper_object for width control along its length) is the
actual right tool, confirmed against the Blender Manual before building
this, not guessed from memory.

Every other typed operation in this project works on bmesh/mesh data.
Curves are a genuinely different object type -- convert_curve_to_mesh()
is the bridge back into the normal typed vocabulary (bevel_edges,
subdivide_selection, etc.) once a curve-based blockout reads correctly.
"""

import bmesh
import bpy


def create_curve_from_points(name, points, bevel_depth=0.05, closed=False, curve_type="POLY"):
    """Create a curve object from a list of [x, y, z] control points.
    curve_type 'POLY' gives straight segments between points -- predictable
    and easy to verify against measured reference coordinates, unlike
    'BEZIER' where each point's handle directions also need reasoning
    about. Start with POLY; a later decision can convert control-point
    density/smoothing once the gross path is verified correct."""
    clean_type = str(curve_type).strip().upper()
    if clean_type not in {"POLY", "BEZIER", "NURBS"}:
        raise ValueError("curve_type must be POLY, BEZIER, or NURBS")
    if name in bpy.data.objects:
        raise ValueError(f"object '{name}' already exists")
    if len(points) < 2:
        raise ValueError("need at least 2 points to define a curve")
    curve_data = bpy.data.curves.new(name, type="CURVE")
    curve_data.dimensions = "3D"
    spline = curve_data.splines.new(clean_type)
    if clean_type == "BEZIER":
        spline.bezier_points.add(len(points) - 1)
        for index, point in enumerate(points):
            control = spline.bezier_points[index]
            control.co = (point[0], point[1], point[2])
            control.handle_left_type = "AUTO"
            control.handle_right_type = "AUTO"
    else:
        spline.points.add(len(points) - 1)
        for index, point in enumerate(points):
            spline.points[index].co = (point[0], point[1], point[2], 1.0)
    spline.use_cyclic_u = closed
    curve_data.bevel_depth = bevel_depth
    curve_data.fill_mode = "FULL"
    # CORRECTION (found live, first real test): fill_mode alone does not
    # close a beveled tube's end caps -- confirmed directly, a 4-point open
    # POLY curve converted to mesh with fill_mode=FULL still showed 24
    # non-manifold edges (the two open end rings). use_fill_caps is the
    # actual property; defaulting it True here since an OPEN path (the
    # normal case -- a closed loop sets closed=True instead) should still
    # produce a solid, manifold tube once converted to mesh, matching this
    # project's 0-non-manifold standard everywhere else.
    curve_data.use_fill_caps = True
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(obj)
    return {"name": obj.name, "type": obj.type, "point_count": len(points), "bevel_depth": bevel_depth}


def set_curve_bevel_depth(name, depth):
    obj = bpy.data.objects[name]
    if obj.type != "CURVE":
        raise ValueError(f"'{name}' is not a curve object")
    obj.data.bevel_depth = depth
    return {"name": name, "bevel_depth": depth}


def set_curve_taper(name, taper_object_name):
    """Attach a separate curve object as this curve's taper -- its shape
    (as a profile along its own length, evaluated 0..1) scales this
    curve's cross-section along ITS length. Both curves must already
    exist; the taper curve is typically a simple 2-point POLY curve
    describing a width-vs-position profile (e.g. wide at one end,
    narrowing to near-zero at the other), not a copy of the main path."""
    obj = bpy.data.objects[name]
    taper_obj = bpy.data.objects[taper_object_name]
    if obj.type != "CURVE":
        raise ValueError(f"'{name}' is not a curve object")
    if taper_obj.type != "CURVE":
        raise ValueError(f"'{taper_object_name}' is not a curve object")
    obj.data.taper_object = taper_obj
    return {"name": name, "taper_object": taper_object_name}


def convert_curve_to_mesh(name, new_mesh_name=None, merge_dist=0.0001, replace_source=False):
    """Bake the evaluated curve (bevel + taper applied) into a real,
    editable mesh object -- how a curve-based blockout re-enters the
    normal bmesh typed vocabulary for topology/surface work. The source
    curve object is left in place, untouched; this creates a new object.

    CORRECTION (found live, first real test): a beveled curve's end caps
    are NOT welded to the tube wall by bpy.data.meshes.new_from_object() --
    confirmed directly, a 4-point open curve converted to mesh showed 48
    non-manifold edges even with use_fill_caps=True, all located exactly at
    the two end rings. The caps exist as separate, coincident-but-unmerged
    geometry. bmesh.ops.remove_doubles at a tight threshold immediately
    after conversion fixes this completely (verified: 72v/126e/56f with 48
    non-manifold -> 48v/102e/56f with 0), so it's done here unconditionally
    rather than left as a step every caller has to remember -- the same
    reasoning as why ensure_persistent_ids is called automatically around
    DecisionTransaction rather than left to each caller's judgment."""
    obj = bpy.data.objects[name]
    if obj.type != "CURVE":
        raise ValueError(f"'{name}' is not a curve object")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(obj_eval)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_dist)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    new_name = new_mesh_name or (name if replace_source else f"{name}_mesh")
    if new_name in bpy.data.objects and not (replace_source and new_name == name):
        raise ValueError(f"object '{new_name}' already exists")
    temporary_name = f"{new_name}__converted" if replace_source and new_name == name else new_name
    new_obj = bpy.data.objects.new(temporary_name, mesh)
    new_obj.matrix_world = obj.matrix_world.copy()
    bpy.context.scene.collection.objects.link(new_obj)
    if replace_source:
        source_data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if source_data.users == 0:
            bpy.data.curves.remove(source_data)
        new_obj.name = new_name
    return {
        "name": new_obj.name,
        "type": new_obj.type,
        "vertices": len(mesh.vertices),
        "faces": len(mesh.polygons),
        "source_replaced": bool(replace_source),
    }
