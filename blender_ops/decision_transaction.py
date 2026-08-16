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
import copy

import decision_state
import persistent_ids
import state_probe


class TransactionError(Exception):
    pass


def _copy_custom_property_value(value):
    """Convert Blender ID-property containers into assignable Python values."""
    if hasattr(value, "to_list"):
        return [_copy_custom_property_value(item) for item in value.to_list()]
    if hasattr(value, "to_dict"):
        return {key: _copy_custom_property_value(item) for key, item in value.to_dict().items()}
    if isinstance(value, dict):
        return {key: _copy_custom_property_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_copy_custom_property_value(item) for item in value]
    return copy.deepcopy(value)


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
        # A transaction may own an editable mesh *or* curve.  The old name
        # reflected the original mesh-only implementation and encouraged
        # curve edits to bypass transaction rollback entirely.
        self._before_data_snapshot = None
        self._before_transform = None
        self._before_object_names = None
        self._before_collection_names = None
        self._before_target_collection_names = None
        self._removed_created_collections = []
        self._before_object_snapshot = None
        self._before_selected = None
        self._before_active_object = None
        self.result = None
        self.reject_reason = None
        self._failure_rolled_back = False

    @staticmethod
    def _supported_target(obj):
        return obj is not None and obj.type in {"MESH", "CURVE"}

    @staticmethod
    def _remove_data_if_unused(data):
        """Free only the datablock types this transaction snapshots."""
        if data is None or data.users != 0:
            return
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Curve):
            bpy.data.curves.remove(data)

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
            target = bpy.data.objects.get(self.target_object)
            if not self._supported_target(target):
                raise TransactionError(
                    f"target '{self.target_object}' must be a MESH or CURVE object"
                )
            if target.type == "MESH":
                self._before_state = state_probe.mesh_health(self.target_object)
                # Backfill IDs for any pre-existing element that doesn't have one yet
                # (e.g. the first transaction ever run against an object), so the
                # before/after ID sets captured around this transaction are complete.
                persistent_ids.ensure_persistent_ids(self.target_object)
                self._before_ids = persistent_ids.get_id_maps(self.target_object)
            else:
                self._before_state = state_probe.get_curve_state(self.target_object)
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
            if obj.type == "CURVE" and obj.mode == "EDIT":
                raise TransactionError(
                    "curve transaction requires Object Mode; Curve Edit Mode rollback is not yet "
                    "safe in the background runtime"
                )
            self._before_data_snapshot = obj.data.copy()
            self._before_object_snapshot = obj.copy()
            # Object.copy() keeps a user on the live mesh by default. Point the detached
            # object snapshot at the transaction-owned mesh copy instead; otherwise a
            # failed operation leaves the replaced live mesh orphaned but still retained
            # until the object snapshot is freed.
            self._before_object_snapshot.data = self._before_data_snapshot
            self._before_selected = obj.select_get()
            self._before_active_object = bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
            self._before_transform = {
                "location": tuple(obj.location),
                "rotation_euler": tuple(obj.rotation_euler),
                "scale": tuple(obj.scale),
            }
        # Capture after transaction-owned snapshots are allocated so detached
        # snapshot datablocks are never reported as objects created by fn().
        self._before_object_names = set(bpy.data.objects.keys())
        self._before_collection_names = set(bpy.data.collections.keys())
        if self.target_object:
            self._before_target_collection_names = [
                collection.name for collection in bpy.data.objects[self.target_object].users_collection
            ]
        try:
            self.result = fn(*args, **kwargs)
        except Exception as operation_error:
            # An operator can mutate BMesh and then raise. Treating that as "never performed" and
            # merely abandoning the transaction would preserve a partial edit and leak both
            # snapshots. Restore atomically before propagating the original failure.
            try:
                if self.target_object:
                    self._restore_target_snapshot()
                self._failure_rolled_back = True
            except Exception as rollback_error:
                raise TransactionError(
                    f"operation failed ({operation_error}); automatic rollback also failed "
                    f"({rollback_error})"
                ) from operation_error
            finally:
                self._free_snapshot()
            raise
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
            target = bpy.data.objects[self.target_object]
            if target.type == "MESH":
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
            else:
                self._after_state = state_probe.get_curve_state(self.target_object)
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
        created_objects = self._restore_target_snapshot()
        self._rejected = True
        self.reject_reason = reason
        self._free_snapshot()
        return {
            "rejected": True,
            "restored_revision": self.observed_revision,
            "reason": reason,
            "removed_created_objects": created_objects,
            "removed_created_collections": self._removed_created_collections,
        }

    def _restore_target_snapshot(self):
        """Restore every transaction-owned target channel without changing decision state."""
        obj = bpy.data.objects[self.target_object]
        if obj.type == "MESH" and obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            bm.clear()
            bm.from_mesh(self._before_data_snapshot)
            bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)
        else:
            replaced_data = obj.data
            replaced_name = replaced_data.name
            restored_data = self._before_data_snapshot.copy()
            obj.data = restored_data
            self._remove_data_if_unused(replaced_data)
            # Rename only after the replaced datablock is gone so Blender does not append
            # a numeric suffix and make a successful rollback observably change identity.
            restored_data.name = replaced_name
        obj.location = self._before_transform["location"]
        obj.rotation_euler = self._before_transform["rotation_euler"]
        obj.scale = self._before_transform["scale"]
        self._restore_object_channels(obj)
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        for collection_name in self._before_target_collection_names or []:
            collection = bpy.data.collections.get(collection_name)
            if collection is None and bpy.context.scene.collection.name == collection_name:
                # The scene's master collection can own objects and appears in
                # Object.users_collection, but it is not a member of
                # bpy.data.collections. Resolve that root explicitly.
                collection = bpy.context.scene.collection
            if collection is None:
                raise TransactionError(
                    f"cannot restore target collection '{collection_name}' because it was removed"
                )
            collection.objects.link(obj)
        created_objects = sorted(set(bpy.data.objects.keys()) - (self._before_object_names or set()))
        for object_name in created_objects:
            created = bpy.data.objects.get(object_name)
            if created is not None:
                data = created.data if created.type in {"MESH", "CURVE"} else None
                bpy.data.objects.remove(created, do_unlink=True)
                self._remove_data_if_unused(data)
        created_collections = sorted(
            set(bpy.data.collections.keys()) - (self._before_collection_names or set())
        )
        for collection_name in created_collections:
            collection = bpy.data.collections.get(collection_name)
            if collection is None:
                continue
            if collection.objects or collection.children:
                raise TransactionError(
                    f"cannot remove transaction-created collection '{collection_name}' because it is not empty"
                )
            bpy.data.collections.remove(collection)
        self._removed_created_collections = created_collections
        return created_objects

    def _restore_object_channels(self, obj):
        """Restore object metadata, modifiers, and object selection from the object snapshot."""
        snapshot = self._before_object_snapshot
        if snapshot is None:
            return
        for key in list(obj.keys()):
            del obj[key]
        for key in snapshot.keys():
            obj[key] = _copy_custom_property_value(snapshot[key])

        for modifier in list(obj.modifiers):
            obj.modifiers.remove(modifier)
        for source in snapshot.modifiers:
            target = obj.modifiers.new(name=source.name, type=source.type)
            for prop in source.bl_rna.properties:
                identifier = prop.identifier
                if identifier in {"rna_type", "name", "type"} or prop.is_readonly:
                    continue
                try:
                    setattr(target, identifier, getattr(source, identifier))
                except (AttributeError, TypeError, ValueError):
                    # Runtime-only and collection properties are not universally assignable.
                    continue
        obj.select_set(bool(self._before_selected))
        obj.hide_render = bool(snapshot.hide_render)
        obj.hide_set(bool(snapshot.hide_get()))
        if self._before_active_object:
            active = bpy.data.objects.get(self._before_active_object)
            if active is not None:
                bpy.context.view_layer.objects.active = active

    def _free_snapshot(self):
        # The detached object copy still owns one user of the mesh snapshot.
        # Remove it first: removing the mesh first invalidates the Object RNA
        # wrapper and a later bpy.data.objects.remove() raises ReferenceError.
        if self._before_object_snapshot is not None:
            try:
                if self._before_object_snapshot.name in bpy.data.objects:
                    bpy.data.objects.remove(self._before_object_snapshot)
            except ReferenceError:
                # Blender may already have invalidated an unlinked snapshot as
                # a side effect of datablock cleanup. It is then already free.
                pass
            self._before_object_snapshot = None
        if self._before_data_snapshot is not None:
            try:
                self._remove_data_if_unused(self._before_data_snapshot)
            except ReferenceError:
                pass
            self._before_data_snapshot = None

    def __exit__(self, exc_type, exc, tb):
        return False


def decision_transaction(observed_revision, action_type, target_object=None):
    return DecisionTransaction(observed_revision, action_type, target_object)
