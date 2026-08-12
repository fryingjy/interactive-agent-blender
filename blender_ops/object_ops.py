"""Object/scene-level helpers -- modifiers, undo/redo, file checkpoints --
distinct from mesh_ops.py's mesh-editing bmesh helpers, since none of these
touch bmesh at all.
"""

import os
import time

import bpy

try:
    from . import persistent_ids
except ImportError:
    import persistent_ids


_PRIMITIVES = {
    "cube": bpy.ops.mesh.primitive_cube_add,
    "cylinder": bpy.ops.mesh.primitive_cylinder_add,
    "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
    "cone": bpy.ops.mesh.primitive_cone_add,
    "torus": bpy.ops.mesh.primitive_torus_add,
    "plane": bpy.ops.mesh.primitive_plane_add,
}


def create_primitive(name, primitive_type, location=(0.0, 0.0, 0.0), **kwargs):
    """Create a new mesh object from a basic primitive and give it `name`.
    Not itself an asset builder -- it's the one-time starting block a
    modeling session begins from, same as picking a base mesh in the
    Blender UI. All actual form comes from typed decisions afterward.

    kwargs are passed straight through to the underlying bpy.ops.mesh.*
    operator, since each primitive has different dimension parameters
    (cube/plane: size; cylinder/sphere: radius; cone: radius1/radius2/
    depth; torus: major_radius/minor_radius) -- there is no single generic
    "size" that means the same thing across all of them."""
    fn = _PRIMITIVES.get(primitive_type)
    if fn is None:
        raise ValueError(f"unknown primitive_type '{primitive_type}' -- available: {sorted(_PRIMITIVES)}")
    if name in bpy.data.objects:
        raise ValueError(f"object '{name}' already exists")
    fn(location=location, **kwargs)
    obj = bpy.context.active_object
    obj.name = name
    if obj.data is not None:
        obj.data.name = name
    return {"name": obj.name, "type": obj.type, "location": list(obj.location)}


def add_modifier(name, modifier_type, modifier_name=None):
    """CORRECTION (found live, chasing why a Subdivision Surface modifier's
    effect wasn't showing up in evaluated_probe's results): obj.modifiers.new()
    does NOT default show_viewport/show_render to True -- confirmed
    directly (a freshly created SUBSURF modifier read back show_viewport
    == False before this fix), so the modifier was silently invisible to
    both the evaluated-mesh dependency graph AND the actual Blender
    viewport the whole time. This likely also affected the speaker
    enclosure's earlier Bevel modifier test, which was never checked
    against the evaluated mesh (evaluated_probe.py didn't exist yet) --
    that decision is still an honest record of add_modifier/
    set_modifier_parameter succeeding, but not evidence the modifier was
    ever actually visible. Explicitly enabling both flags now."""
    obj = bpy.data.objects[name]
    mod = obj.modifiers.new(name=modifier_name or modifier_type.title(), type=modifier_type)
    mod.show_viewport = True
    mod.show_render = True
    return {"modifier_name": mod.name, "type": mod.type, "show_viewport": mod.show_viewport}


def set_modifier_parameter(name, modifier_name, parameter, value):
    obj = bpy.data.objects[name]
    mod = obj.modifiers.get(modifier_name)
    if mod is None:
        raise ValueError(f"no modifier '{modifier_name}' on '{name}' -- current modifiers: {[m.name for m in obj.modifiers]}")
    if not hasattr(mod, parameter):
        raise ValueError(f"modifier '{modifier_name}' ({mod.type}) has no parameter '{parameter}'")
    setattr(mod, parameter, value)
    return {"modifier_name": modifier_name, "parameter": parameter, "value": getattr(mod, parameter)}


def set_shading(name, smooth=True):
    """Set polygon interpolation explicitly on one mesh object.

    Smooth/flat shading changes the visible surface without changing topology, so it belongs in
    the same one-decision transaction path as modifier edits rather than in presentation fallback
    code.  The mesh snapshot owned by DecisionTransaction preserves polygon flags for rollback.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    value = bool(smooth)
    changed = 0
    for polygon in obj.data.polygons:
        if polygon.use_smooth != value:
            polygon.use_smooth = value
            changed += 1
    obj.data.update()
    return {"smooth": value, "changed_polygons": changed, "polygon_count": len(obj.data.polygons)}


def set_smooth_by_angle(name, angle=0.5235987756, keep_sharp_edges=True):
    """Apply Blender's Smooth by Angle asset to one mesh.

    This is the hard-surface default when a mesh needs normal interpolation
    without smoothing across every design transition.  It deliberately does
    not replace topology: first identify semantic hard edges, use a scoped
    Bevel (normally WEIGHT) where a physical radius is required, put Bevel
    before SubD when both are warranted, then use this for the remaining
    normal split/shading behavior.  Do not call ``set_shading(..., True)`` as
    a blanket substitute for that sequence.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    result = bpy.ops.object.shade_smooth_by_angle(
        angle=float(angle), keep_sharp_edges=bool(keep_sharp_edges)
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Smooth by Angle failed for '{name}': {result}")
    obj["shading_policy"] = "SMOOTH_BY_ANGLE"
    obj["smooth_by_angle_radians"] = float(angle)
    obj["smooth_by_angle_keep_sharp_edges"] = bool(keep_sharp_edges)
    return {
        "shading": "SMOOTH_BY_ANGLE",
        "angle": float(angle),
        "keep_sharp_edges": bool(keep_sharp_edges),
        "modifier_count": len(obj.modifiers),
    }


def set_bevel_weight_by_ids(name, edge_ids, weight=1.0, clear_others=False):
    """Assign a semantic bevel-weight set by persistent edge IDs.

    The caller must first inspect the cage and choose the design edges that
    require a physical radius. It is not a "make everything sharp" command.
    Blender 5 stores this as the generic ``bevel_weight_edge`` float
    attribute, so persistent IDs protect authored intent across unrelated
    topology edits.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    if obj.mode == "EDIT":
        raise ValueError("set_bevel_weight_by_ids requires Object Mode; leave Edit Mode before changing mesh attributes")
    value = float(weight)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"weight must be in [0, 1], got {weight}")
    persistent_ids.ensure_persistent_ids(name)
    id_map = persistent_ids.get_id_maps(name)["edges"]["id_to_index"]
    attribute = obj.data.attributes.get("bevel_weight_edge")
    if attribute is None:
        attribute = obj.data.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
    if attribute.domain != "EDGE":
        raise ValueError("bevel_weight_edge exists but is not an EDGE-domain attribute")
    if clear_others:
        for item in attribute.data:
            item.value = 0.0
    assigned, missing = [], []
    for agent_id in edge_ids:
        edge_index = id_map.get(int(agent_id))
        if edge_index is None:
            missing.append(int(agent_id))
            continue
        attribute.data[edge_index].value = value
        assigned.append(int(agent_id))
    obj.data.update()
    return {
        "attribute": "bevel_weight_edge",
        "weight": value,
        "assigned_edge_ids": assigned,
        "missing_edge_ids": missing,
        "clear_others": bool(clear_others),
    }


def undo():
    """CORRECTION (found live, testing this against a scratch object):
    this does NOT reliably undo "the last decision." DecisionTransaction
    mutations write via bm.to_mesh()+obj.data.update(), which do NOT push
    an entry onto Blender's own undo stack -- confirmed directly: one
    mesh_ops mutation followed by exactly one undo() call deleted the
    ENTIRE object, jumping straight past the mutation to the last real
    bpy.ops-recorded action (object creation). Any number of committed
    decisions on an object can be sitting between "now" and whatever
    undo() actually reverts to. Do not call this expecting it to revert
    one committed decision -- verify with get_full_state/mesh_health
    before and after, on every call, and treat a large unexpected change
    as the normal outcome, not a bug."""
    bpy.ops.ed.undo()
    return {"undone": True}


def redo():
    """See undo()'s docstring -- the same disconnect between Blender's
    undo stack and DecisionTransaction's bmesh-direct mutations applies
    in reverse."""
    bpy.ops.ed.redo()
    return {"redone": True}


def save_checkpoint(label, directory):
    """Save a labeled, timestamped copy of the current file WITHOUT
    switching the working file (copy=True) -- a restorable snapshot, not a
    save-and-continue-from-here."""
    os.makedirs(directory, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    filename = f"{label}_{ts}.blend"
    filepath = os.path.join(directory, filename)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)
    return {"filepath": filepath}


def restore_checkpoint(filepath):
    """Reload a previously saved checkpoint, replacing the entire live
    scene. Irreversible for any unsaved work since that checkpoint --
    callers should save_checkpoint first if the current state matters."""
    bpy.ops.wm.open_mainfile(filepath=filepath)
    return {"restored": filepath}


def save_file(filepath=None):
    if filepath:
        bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)
        return {"filepath": filepath}
    bpy.ops.wm.save_mainfile()
    return {"filepath": bpy.data.filepath}
