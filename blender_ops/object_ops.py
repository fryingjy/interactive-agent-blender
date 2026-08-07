"""Object/scene-level helpers -- modifiers, undo/redo, file checkpoints --
distinct from mesh_ops.py's mesh-editing bmesh helpers, since none of these
touch bmesh at all.
"""

import os
import time

import bpy


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
