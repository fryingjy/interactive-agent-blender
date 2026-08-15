# Operator card: high-poly/low-poly production collection pipeline

**Status:** OBSERVED (7/10 studied professional files) | TYPED PACKAGING VALIDATED | PRODUCTION AUDIT TRANSFER VALIDATED | AUTONOMOUS RETOPOLOGY PENDING

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

### Production low-poly readiness — audit validated, autonomous authoring pending

A production low-poly requires separate topology chosen for silhouette, deformation, UV layout,
baking, and export constraints. `get_production_high_low_audit` now combines read-only Blender
evidence for collection isolation, independent mesh datablocks, materially lower base topology,
connectivity, low UV validity, multiview silhouette preservation, and current live modifier stacks.
It classifies an equal cage as `EDITABLE_VARIANT_ONLY` even when the object is named low-poly and is
stored in a separate collection.

The audit does not infer authoring history. A lower face ratio is necessary evidence in this
controlled contract, not proof that a human or agent purposefully retopologized the object. Blender
can show that modifiers are live now; it cannot prove that no modifier was applied earlier. The
controlled build therefore also keeps a static no-`modifier_apply` check, a scene declaration, and a
fresh-process source inspection. All modifiers remain unapplied for the user.

## Runtime evidence

- `runs/2026-08-15_typed-high-low-variants/` — controlled commit, reject, name-collision failure,
  saved `.blend`, and independent fresh-process inspection. Both variants retain live Subdivision and
  Solidify modifiers; evaluated density differs while editable base cages remain independent and equal.
- `runs/2026-08-15_nailsea-form-correction/` — real asset transfer through the typed operation.
  `Corrected_Nailsea_Candlestick_HIGH` and `_LOW` are isolated in separate collections, both modifier
  stacks are unapplied, and a fresh Blender verifier passes the production-variant checks.
- `runs/2026-08-13_blend-file-study/{batarang,alien_force_watch,broken_sword,adventure_time_sword,
  ap15,ak47}/inspection.json` — observed professional-file organization and distinct topology evidence.
- `runs/2026-08-15_production-high-low-audit/` — two controlled shape families, a rejected radial
  cage that omitted a profile-defining ring, three-view silhouette gates, valid low UVs, real Cycles
  Selected-to-Active tangent bakes, low-only GLBs, fresh source/export verification, and five
  fail-closed controls. `HIGH_POLY` and `LOW_POLY` remain separate and all source Bevel modifiers
  remain live and unapplied.

## Promotion boundary

Typed editable-variant packaging is `RUNTIME_VALIDATED`, and the production-readiness audit is
`TRANSFER_VALIDATED` across two controlled families. Autonomous production retopology remains
unimplemented and must not inherit either status.
