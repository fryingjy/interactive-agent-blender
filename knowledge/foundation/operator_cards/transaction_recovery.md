# Scoped transaction recovery

## Use

Open one `DecisionTransaction`, execute exactly one sanctioned artistic mutation with `perform`,
inspect with `verify`, then either `commit` or `reject`. Prefer rejection to a forward-fix when the
decision itself is unacceptable.

## Restored channels

For an Object Mode mesh target, rejection restores the independent mesh datablock (including UVs,
material slots, element selection, and mesh custom data), transform, object custom properties and
semantic regions, modifier stack and assignable parameters, object selection, active object, and
the unchanged decision revision. Objects created during the operation are removed.

## Mechanism warning

Detached Blender object copies are registered datablocks. Capture the pre-operation object-name
baseline after allocating transaction snapshots, and remove the object snapshot before its mesh
snapshot. Reversing cleanup order can invalidate the Object RNA wrapper.

## Evidence

`runs/2026-08-10_transaction-rollback/` passes 8/8 channel assertions and includes an independently
verified clean saved mesh. Evidence is scoped to Object Mode and ordinary assignable modifier RNA.

## Multi-object batching: commits share one global revision counter (2026-08-14)

`commit_decision` "advances the live decision-revision counter by exactly one" -- that counter is
global across the whole scene, not per-object. Discovered building `runs/2026-08-14_simple-crate/`
(16 objects): `begin_decision` and `perform_decision` can be issued in parallel across many
different objects with no conflict (they don't touch the counter), but only the **first**
`commit_decision` in a batch succeeds -- every other pending decision, even on a completely
different object, immediately becomes stale ("decision was reasoned against revision N, but the
scene is now at revision N+1") the moment any one of them commits.

This is not a bug to route around with a fresh mutation retry. `perform_decision` already mutated
the live mesh before commit was attempted, so the underlying geometry is already correct even
though the decision's own bookkeeping didn't finalize. The correct recovery is cheap: call
`begin_decision` again on the stale object (its "external edit detected... this check just
captured the current state as the new baseline" response is expected and correct here, not an
error to work around), confirm via `get_evaluated_state` that the geometry already matches intent,
then `abandon_decision` immediately -- no further `perform_decision` needed. Do not re-run the
original mutation a second time; the geometry is already right, and re-applying it would double
the effect.

Practical pattern for N similar objects (e.g. an array of slats): batch-create all N with
`create_primitive` (free, no transaction), batch `begin_decision` + `perform_decision` for all N in
parallel, `commit_decision` exactly one, then `begin_decision` + `abandon_decision` (in two more
parallel batches) for the remaining N-1 to adopt their already-correct state as the new baseline.
