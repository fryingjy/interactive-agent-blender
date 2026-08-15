# Typed editable high/low variant packaging

## Outcome

The runtime now packages one editable source into separate `HIGH_POLY` and `LOW_POLY` collections
through a single typed decision. The high object remains the source. The low object owns an
independent mesh datablock and an independent copy of the modifier stack. Subdivision remains live
at level zero on the low variant, and no modifier is applied on either object.

The controlled commit case and fresh-process verifier pass every declared check. The high and low
base cages both contain 8 vertices, 12 edges, and 6 faces; evaluated geometry differs because high
Subdivision remains level 2 while low remains level 0. Both also retain live Solidify modifiers.

## Rollback and failure controls

A second package was deliberately rejected after it had moved the source and created a low object
and two collections. Rejection restored the source's original scene-root membership and modifier
state, removed the duplicate object and mesh, removed both empty collections, and left the revision
unchanged. This exposed and fixed Blender's special scene-root lookup: `Scene Collection` appears in
`Object.users_collection` but not in `bpy.data.collections`.

An existing-collection collision fails before persistent change. Abandoning that failed decision
reports that its transaction-owned automatic rollback completed.

## Boundary

This is editable internal variant packaging for a user who wants to apply modifiers manually. It is
not production low-poly retopology and does not create UVs, bake maps, or export an engine asset.

## Reproduction

```powershell
blender --background --factory-startup --python tools/run_high_low_variant_lab.py
blender --background runs/2026-08-15_typed-high-low-variants/typed_high_low_variants.blend --python tools/verify_high_low_variant_lab.py
```
