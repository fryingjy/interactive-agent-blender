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

import bpy

import decision_state
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
        self._before_op_count = None
        self._before_state = None
        self._after_state = None
        self._op_delta = None
        self.result = None

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
        return self

    def perform(self, fn, *args, **kwargs):
        """The one and only sanctioned mutation point. Raises on a second call."""
        if self._performed:
            raise TransactionError(
                "perform() was already called once in this transaction -- exactly "
                "one artistic operation is permitted per decision. Close this "
                "transaction, advance the revision, and open a new one for the "
                "next operation."
            )
        self.result = fn(*args, **kwargs)
        self._performed = True
        return self.result

    def verify(self):
        """Capture the after-state and the operator-history delta. For bpy.ops-based
        operations this delta is a real, hard-to-fake signal (each operator call
        appends exactly one entry to window_manager.operators). bmesh.ops-based
        operations don't touch that history at all, so a delta of 0 there is
        expected, not suspicious -- this is a known asymmetry, not a false claim
        of full proof."""
        if not self._performed:
            raise TransactionError("verify() called before perform() -- no operation happened yet")
        after_op_count = len(bpy.context.window_manager.operators)
        self._op_delta = after_op_count - self._before_op_count
        if self.target_object:
            self._after_state = state_probe.mesh_health(self.target_object)
        return {
            "action_type": self.action_type,
            "op_delta": self._op_delta,
            "before": self._before_state,
            "after": self._after_state,
        }

    def commit(self):
        if not self._performed:
            raise TransactionError("cannot commit: no operation was performed")
        if self._committed:
            raise TransactionError("this transaction was already committed")
        new_revision = decision_state.advance_revision(self.observed_revision)
        self._committed = True
        return new_revision

    def __exit__(self, exc_type, exc, tb):
        return False


def decision_transaction(observed_revision, action_type, target_object=None):
    return DecisionTransaction(observed_revision, action_type, target_object)
