# Held-out CC0 boombox benchmark

**Status:** PASS for the predeclared automated stylized hard-surface gates. Experienced human
acceptance and photoreal replication remain open.

## Source boundary

The reference is Poly Haven's CC0 `boombox`: <https://polyhaven.com/a/boombox>. The downloaded GLTF
is kept under ignored `media/`. `tools/render_multiview_reference.py` imported it only to create
neutral front/side/top/isometric pixels and silhouettes. Source topology, modifiers, construction,
and object dimensions were not inspected or copied. The manifest records SHA-256
`8f5851b81d0d0b16fadf9ca89133b59ee48718ed8d9f8244b87e4d293755d2d3`.

## Modeling result

The final scene contains 41 named semantic meshes created without mesh primitive operators. Its main
housing is one connected 72-vertex/70-quad edited cage: a front/back cut grid with the central front
region recessed in the same mesh. Separate objects are limited to physically separate panels,
speakers, controls, handle, antenna, fasteners, and repeated vent hardware. The scene also contains
authored lathed profiles, one connected carry handle, linked bilateral speaker data, linked repeated
controls, and two Array-driven 13-slat side vents. Materials separate painted case, control panel,
recesses, smoked glazing, brushed metal, speaker grille, and keys. Every mesh has an actual
smart-projected UV layout.

Normalized fixed-view silhouette IoU is `0.870970` front, `0.756590` side, `0.820119` top, and
`0.815893` mean, clearing the declared `0.82/0.72/0.72/0.78` gates.

## Preserved failures and evidence correction

- A uniform proportion correction was rejected because it reduced normalized IoU in all views.
  This also exposed that the first assessment had mixed a raw same-canvas result with the brief's
  explicitly normalized gate. `compare_alpha_multiview.py` now records configurable thresholds.
- The first production candidate created two zero-area faces on each lathed family by emitting full
  coincident rings at zero-radius endpoints. That scene/report remain under
  `failed_degenerate_lathe_caps/`; the helper now caps adjacent nonzero rings directly.
- A technically clean but visually primitive-assembled housing was rejected after user review and
  preserved under `failed_primitive_assembly_review/`. It was replaced by the connected edited cage.
- Broad and then vertex-group perimeter bevels created visible corner spikes/fins on the cut grid.
  The broad failure is retained under `failed_unscoped_housing_bevel/`; final topology keeps the
  authored outer corners and scopes a narrow bevel only to the recessed transition.

## Independent verification

`tools/verify_heldout_boombox.py` opens the saved scene in a fresh Blender 5.2 factory process,
without importing the generator. It passes 15 assertions covering base/evaluated health, the single
connected edited housing, region-scoped recess treatment, connected handle topology, linked
speakers, Array counts, purposeful bevel stacks, populated UV loops, node materials, render
evidence, source isolation, and exact declared silhouette gates.

## Production export

`tools/run_boombox_production_export.py` exports the accepted scene as GLB with evaluated modifiers.
`tools/verify_boombox_production_export.py` then imports it in a fresh Blender factory process and
directly reads the GLB 2.0 JSON chunk. The round trip preserves 41 semantic mesh objects, 15,292
evaluated triangles, exact combined dimensions, all UV/material presence, and all seven material
families. Every GLB primitive declares POSITION, NORMAL, and TEXCOORD_0; tangent attributes exist on
the package where Blender could calculate them.

The first verifier incorrectly expected Y-up package dimensions after Blender had already converted
the import back to Z-up. That rejected assumption is preserved in `export/failed_axis_expectation.json`.
Several radial meshes do not export tangents from their current smart-projected UVs. Because this
asset has no tangent-normal textures, that is not a current semantic failure, but a future normal-map
pass must repair/author those UVs and require tangents on every affected primitive.

## Limitations

- This is a clean stylized interpretation, not a photoreal copy. Fine typography, exact grille
  perforations, stickers, and wear are omitted or represented at detail-family/material level.
- Normalized silhouette scores remove absolute scale and translation and do not replace visual
  surface judgment.
- One held-out asset does not prove broad professional proficiency. No experienced artist has
  accepted the result.
- The GLB round trip is structurally validated in Blender, not visually accepted in a named external
  engine; tangent completeness for a future normal-mapped version remains open.
