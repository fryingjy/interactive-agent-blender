"""Mode-aware bmesh read/write, shared by persistent_ids.py and
decision_transaction.py.

state_probe.py and mesh_ops.py read meshes via bmesh.new()+from_mesh(),
which is correct in Object Mode but silently reads STALE data if the
object is in Edit Mode with unsaved edit-bmesh changes -- discovered live
during the mug-retopo session (obj.data.polygons reported a count that had
already diverged from the true live edit-mesh, and bm.to_mesh() raised
outright when the object turned out to be in Edit Mode). These helpers
pick the correct API for the object's actual current mode, so new callers
don't have to special-case it themselves.
"""

import bmesh


def read_bmesh(obj):
    """Return a bmesh reflecting the object's true current state, whether
    it's in Object or Edit Mode."""
    if obj.mode == "EDIT":
        return bmesh.from_edit_mesh(obj.data)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    return bm


def write_bmesh(obj, bm):
    """Write a bmesh back to the object using the correct API for its
    current mode. In Object Mode this also frees the bmesh; the Edit Mode
    bmesh is owned by Blender's edit-mesh system, not this call, so it must
    not be freed here."""
    if obj.mode == "EDIT":
        bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)
    else:
        bm.to_mesh(obj.data)
        obj.data.update()
        bm.free()
