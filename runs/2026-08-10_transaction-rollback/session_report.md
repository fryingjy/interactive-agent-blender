# Multi-channel transaction rollback

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS after two preserved implementation failures

## Result

A rejected `DecisionTransaction` now restores all directive-scoped channels tested in one stress
mutation: base geometry, UV layers, material slots, modifier stack and parameters, semantic-region
and custom-property metadata, face selection, object selection, active object, transform, and scene
revision. The transaction-owned mesh/object snapshots are independent of Blender's global undo
stack. Objects created by the rejected operation are still removed.

The final report passes 8/8 assertions. A fresh Blender process independently verified the saved
`RollbackChannels` cube as closed, consistently oriented, nondegenerate, manifold, and without
loose geometry. `transaction_rollback_report.json` contains exact before/during/after state.

## Preserved failures

- The first stress runner used `uv_layers.clear()`, which Blender 5.2 does not expose. It was
  replaced with explicit layer removal; the failed run produced no success report.
- The first completed rollback removed the mesh snapshot before its detached object snapshot,
  invalidating the latter's RNA wrapper and raising `ReferenceError`. Cleanup now removes the
  object snapshot first and defensively handles already-invalid datablocks.
- The next passing run revealed an audit-only bookkeeping error: the detached snapshot object was
  listed as operation-created. The baseline object-name set is now captured after allocating
  transaction-owned snapshots. The final report correctly lists no created objects for this case.

## Scope and limit

The stress test runs in Object Mode. Edit Mode retains the existing live-BMesh restoration path;
object metadata/modifiers/selection are restored there too, but UV/material mutation while an edit
BMesh is active is not claimed by this fixture. Linked-library and Geometry Nodes internal state
are also outside this scoped evidence.
