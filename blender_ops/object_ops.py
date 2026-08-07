"""Object/scene-level helpers -- modifiers, undo/redo, file checkpoints --
distinct from mesh_ops.py's mesh-editing bmesh helpers, since none of these
touch bmesh at all.
"""

import os
import time

import bpy


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
    obj = bpy.data.objects[name]
    mod = obj.modifiers.new(name=modifier_name or modifier_type.title(), type=modifier_type)
    return {"modifier_name": mod.name, "type": mod.type}


def set_modifier_parameter(name, modifier_name, parameter, value):
    obj = bpy.data.objects[name]
    mod = obj.modifiers.get(modifier_name)
    if mod is None:
        raise ValueError(f"no modifier '{modifier_name}' on '{name}' -- current modifiers: {[m.name for m in obj.modifiers]}")
    if not hasattr(mod, parameter):
        raise ValueError(f"modifier '{modifier_name}' ({mod.type}) has no parameter '{parameter}'")
    setattr(mod, parameter, value)
    return {"modifier_name": modifier_name, "parameter": parameter, "value": getattr(mod, parameter)}


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
