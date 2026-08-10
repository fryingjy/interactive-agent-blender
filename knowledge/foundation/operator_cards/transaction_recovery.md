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
