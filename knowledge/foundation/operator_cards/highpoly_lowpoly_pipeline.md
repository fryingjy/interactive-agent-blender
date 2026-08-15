# Operator card: high-poly/low-poly production collection pipeline

**Status:** OBSERVED (7/10 studied professional files) | TYPED PACKAGING VALIDATED | RUNTIME USE VALIDATED | TRUE RETOPOLOGY PENDING

## What it is

A collection-based organization pattern appears in 7 of the 10 professional `.blend` files studied
under `docs/BLEND_FILE_STUDY_PROTOCOL.md` (`batarang.blend`, `alien force watch.blend`,
`broken sword.blend`, `adventure time sword.blend`, `ap15.blend`, `ak47.blend`, and the simpler
single-stage version in `battle axe.blend`):

- A working high-poly collection contains the editable source and its live non-destructive modifier
  stack.
- A production low-poly collection normally contains genuinely separate, purpose-authored topology,
  UVs, and bake targets. It is not merely the high cage with Subdivision disabled.
- An optional dense sculpt collection can hold immutable bake sources for high-frequency detail.

The studied low-poly materials include baked PBR textures, confirming a real high-to-low bake
pipeline rather than only an internal viewport convenience.

## Two distinct workflows

### Editable internal variants — typed and runtime validated

`package_high_low_variants` packages an existing mesh into separate `HIGH_POLY` and `LOW_POLY`
collections. The source remains the high object. The low object receives an independent mesh
datablock and an independently editable copy of the full modifier stack. Subdivision remains present
at a caller-selected level, normally zero. No modifier is applied.

The operation is one rollback-owned typed decision. Rejecting it restores the source's original
collection membership and removes the duplicate object, duplicate mesh, and transaction-created
collections. Existing object or collection name collisions fail closed.

This is the correct quick packaging mechanism when the user wants to apply modifiers manually. It is
also honest about its limit: identical base counts do not make the duplicate a production low-poly
retopology.

### True production low-poly — still pending

A production low-poly requires separate topology chosen for silhouette, deformation, UV layout,
baking, and export constraints. The runtime does not yet infer or author that retopology. UV transfer,
selected-to-active baking, and engine export have separate evidence elsewhere in the repository, but
they are not combined here into an autonomous high-to-low retopology pipeline.

## Runtime evidence

- `runs/2026-08-15_typed-high-low-variants/` — controlled commit, reject, name-collision failure,
  saved `.blend`, and independent fresh-process inspection. Both variants retain live Subdivision and
  Solidify modifiers; evaluated density differs while editable base cages remain independent and equal.
- `runs/2026-08-15_nailsea-form-correction/` — real asset transfer through the typed operation.
  `Corrected_Nailsea_Candlestick_HIGH` and `_LOW` are isolated in separate collections, both modifier
  stacks are unapplied, and a fresh Blender verifier passes the production-variant checks.
- `runs/2026-08-13_blend-file-study/{batarang,alien_force_watch,broken_sword,adventure_time_sword,
  ap15,ak47}/inspection.json` — observed professional-file organization and distinct topology evidence.

## Promotion boundary

Typed editable-variant packaging is `RUNTIME_VALIDATED`. Autonomous production retopology remains
unimplemented and must not inherit that status.
