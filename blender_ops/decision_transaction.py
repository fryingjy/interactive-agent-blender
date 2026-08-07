"""Enforces exactly one artistic operation per decision -- closes the gap
decision_state.py alone left open: advance_revision(rev) only proves that one
revision-advancing call happened before the counter moved. It does NOT prove
that only one Blender mutation occurred in between. A script could legally do

    rev = current_revision()
    extrude(); scale(); bevel(); move_vertices(); add_modifier()
    advance_revision(rev)

and the counter would still show a clean 50->51.

DecisionTransaction closes that specific hole: the only way to mutate through
it is tx.perform(fn, *args, **kwargs), and perform() raises if called a second
time in the same transaction. Mechanical queries (state_probe calls) are not
gated -- they're reads, not mutations, and are expected to happen freely
before/after the one permitted operation.

This does not (and cannot) stop code from bypassing the object entirely and
calling bpy.ops/bmesh.ops directly -- no in-process Python API can fully
sandbox its own caller. What it changes is the sanctioned path: using it
correctly is one line, and skipping it is a visible, auditable choice rather
than something the log's numbers alone would hide.
"""

import bmesh
import bpy

import decision_state
import persistent_ids
import state_probe


class TransactionError(Exception):
    pass


class DecisionTransaction:
    def __init__(self, observed_revision, action_type, target_object=None):
        self.observed_revision = observed_revision
        self.action_type = action_type
        self.target_object = target_object
        self._performed = False
        self._committed = False
        self._rejected = False
        self._before_op_count = None
        self._before_state = None
        self._after_state = None
        self._before_ids = None
        self._after_ids = None
        self._op_delta = None
        self._before_mesh_snapshot = None
        self._before_transform = None
        self.result = None
        self.reject_reason = None

    def __enter__(self):
        actual = decision_state.current_revision()
        if actual != self.observed_revision:
            raise TransactionError(
                f"stale observation: transaction opened against revision "
                f"{self.observed_revision}, but the scene is now at {actual} -- "
                f"re-observe before starting a new transaction"
            )
        self._before_op_count = len(bpy.context.window_manager.operators)
        if self.target_object:
            self._before_state = state_probe.mesh_health(self.target_object)
            # Backfill IDs for any pre-existing element that doesn't have one yet
            # (e.g. the first transaction ever run against an object), so the
            # before/after ID sets captured around this transaction are complete.
            persistent_ids.ensure_persistent_ids(self.target_object)
            self._before_ids = persistent_ids.get_id_maps(self.target_object)
        return self

    def perform(self, fn, *args, **kwargs):
        """The one and only sanctioned mutation point. Raises on a second call.

        Captures a restorable pre-mutation snapshot (a full, independent
        mesh-datablock copy plus object transform) immediately before calling
        fn(), not in __enter__ -- so a transaction that's opened and then
        abandoned without ever calling perform() never allocates a snapshot
        that would otherwise leak as an orphan mesh datablock. This is what
        makes reject() a real transaction-owned rollback rather than relying
        on bpy.ops.ed.undo(), which object_ops.undo()'s own docstring already
        found unreliable for reverting one specific decision."""
        if self._performed:
            raise TransactionError(
                "perform() was already called once in this transaction -- exactly "
                "one artistic operation is permitted per decision. Close this "
                "transaction, advance the revision, and open a new one for the "
                "next operation."
            )
        if self.target_object:
            obj = bpy.data.objects[self.target_object]
            self._before_mesh_snapshot = obj.data.copy()
            self._before_transform = {
                "location": tuple(obj.location),
                "rotation_euler": tuple(obj.rotation_euler),
                "scale": tuple(obj.scale),
            }
        self.result = fn(*args, **kwargs)
        self._performed = True
        return self.result

    def verify(self):
        """Capture the after-state and the operator-history delta.

        CORRECTION (found 2026-08-07, mug milestone): window_manager.operators is
        NOT a reliable per-transaction signal. Direct inspection showed it's a
        capped ring buffer (observed length 24, not growing further) that is also
        shared with the user's own concurrent GUI clicks in the same live session
        -- its tail has contained VIEW3D_OT_select/OBJECT_OT_delete entries this
        script never issued. A bpy.ops-based operation can legitimately show
        op_delta==0 simply because the buffer is full and the user's own actions
        are cycling through it. Treat op_delta as informational only, never as
        proof that exactly one bpy.ops call happened -- it cannot be trusted for
        that in a session where a human may be editing concurrently, which this
        project's own history shows is a real, not hypothetical, condition."""
        if not self._performed:
            raise TransactionError("verify() called before perform() -- no operation happened yet")
        after_op_count = len(bpy.context.window_manager.operators)
        self._op_delta = after_op_count - self._before_op_count
        id_delta = None
        if self.target_object:
            self._after_state = state_probe.mesh_health(self.target_object)
            # Assign IDs to anything perform() created, then diff against the
            # before-set captured in __enter__ -- this is the real, provable
            # delta for exactly this one decision, not an arbitrary revision
            # range: added/removed persistent element IDs.
            persistent_ids.ensure_persistent_ids(self.target_object)
            self._after_ids = persistent_ids.get_id_maps(self.target_object)
            id_delta = {}
            for kind in ("verts", "edges", "faces"):
                before_ids = set(self._before_ids[kind]["id_to_index"])
                after_ids = set(self._after_ids[kind]["id_to_index"])
                id_delta[kind] = {
                    "added": sorted(after_ids - before_ids),
                    "removed": sorted(before_ids - after_ids),
                }
        return {
            "action_type": self.action_type,
            "op_delta": self._op_delta,
            "before": self._before_state,
            "after": self._after_state,
            "id_delta": id_delta,
        }

    def commit(self):
        if not self._performed:
            raise TransactionError("cannot commit: no operation was performed")
        if self._committed:
            raise TransactionError("this transaction was already committed")
        if self._rejected:
            raise TransactionError("this transaction was already rejected")
        new_revision = decision_state.advance_revision(self.observed_revision)
        self._committed = True
        self._free_snapshot()
        return new_revision

    def reject(self, reason=""):
        """Transaction-owned rollback: restore geometry and transform to
        exactly the pre-perform() snapshot, independent of Blender's global
        undo stack. decision_state's revision counter is never advanced (no
        commit() ever happened), so the scene is left exactly as if this
        transaction had never been opened -- not a forward-fix, a true
        revert. Mode-aware: an Edit Mode target must have its actual live
        edit-bmesh cleared and refilled (mutating a separate, unrelated
        bmesh and calling bmesh.update_edit_mesh does nothing useful, since
        that call refreshes derived data FROM the currently active edit
        bmesh, it does not accept a replacement bmesh as an argument)."""
        if not self._performed:
            raise TransactionError(
                "cannot reject: no operation was performed -- there is nothing to "
                "undo, just discard this transaction instead of calling reject()"
            )
        if self._committed:
            raise TransactionError("cannot reject: this transaction was already committed")
        if self._rejected:
            raise TransactionError("this transaction was already rejected")
        obj = bpy.data.objects[self.target_object]
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            bm.clear()
            bm.from_mesh(self._before_mesh_snapshot)
            bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)
        else:
            bm = bmesh.new()
            bm.from_mesh(self._before_mesh_snapshot)
            bm.to_mesh(obj.data)
            obj.data.update()
            bm.free()
        obj.location = self._before_transform["location"]
        obj.rotation_euler = self._before_transform["rotation_euler"]
        obj.scale = self._before_transform["scale"]
        self._rejected = True
        self.reject_reason = reason
        self._free_snapshot()
        return {
            "rejected": True,
            "restored_revision": self.observed_revision,
            "reason": reason,
        }

    def _free_snapshot(self):
        if self._before_mesh_snapshot is not None:
            bpy.data.meshes.remove(self._before_mesh_snapshot)
            self._before_mesh_snapshot = None

    def __exit__(self, exc_type, exc, tb):
        return False


def decision_transaction(observed_revision, action_type, target_object=None):
    return DecisionTransaction(observed_revision, action_type, target_object)
