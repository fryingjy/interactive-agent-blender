# Expanded typed modeling operations

## Registered transaction operations

`rotate_selection`, `bevel_selection`, `delete_selection`, `dissolve_selection`,
`merge_selection`, `fill_selection`, `bridge_selection`, `spin_selection`,
`loop_cut_selection`, `bisect_selection`, `symmetrize_selection`, `split_selection`, and
`separate_selection`.

Each operation acts on current selection or explicit plane/axis parameters. The agent must inspect
and select the intended region first; these functions do not choose artistic targets or generate a
full asset. New BMesh element IDs are found by pre/post set differences, not assumed return keys.

`separate_selection` creates a new object and reports `identity_discontinuity: true`. Transaction
rejection removes created objects as well as restoring target geometry.

## Evidence

`runs/2026-08-10_expanded-typed-ops/` has 15/15 cases, a revision/identity transaction, registry
discovery, rollback coverage, independent reports, and preserved symmetrize failures.
