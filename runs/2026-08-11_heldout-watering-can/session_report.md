# Held-out metal watering-can benchmark

## Scope and source boundary

The CC0 Poly Haven asset `watering_can_metal_01` was selected and its gates were frozen before its
isolated GLTF was downloaded. The source was used only to render neutral front, side, top, and
isometric reference pixels. Its topology was not inspected or copied. Source media is ignored by
Git; the reference manifest and derived measurements are retained.

## Construction

- `Connected_Vessel` is one closed all-quad, 16-sided ring loft. Its shoulder, base, and rim
  transitions come from rings in the same cage and intended circumferential edges feed a weighted
  Bevel modifier.
- `Connected_Tapered_Spout` is one closed all-quad, 12-sided tapered path loft.
- `Arched_Handle` is one closed all-quad continuous path loft. A prior converted Curve version was
  rejected because its cap islands were disconnected and non-manifold.
- The rose head, opening rim, and opening shadow are separate only as physically distinct insert/
  opening assemblies.

## Retained failures

`candidate_v1` stopped before verification because factory startup did not contain a World.
`candidate_v2` stopped after a verifier indexing error. `candidate_v3` rendered and cleared the
visual gates but rejected its converted Curve handle: 32 non-manifold edges and three components.
`candidate_v4` replaces that handle with the closed mesh path loft.

## Accepted automated evidence

`candidate_v4/normalized_silhouette_report.json` records normalized IoU of 0.963043 front,
0.791417 side, and 0.947144 top (mean 0.900535), all above the predeclared gates. Its fresh Blender
verifier passes 9/9 assertions: source absent, required parts present, primary forms closed and
all-quad, sparse 16/12 radial controls, complete weighted bevel assignment, UV/node-material
presence, and clean evaluated meshes.

`production/production_report.json` records a real Cycles selected-to-active tangent normal bake
with 16,384 non-neutral pixels and a 87,272-byte GLB export. This is an automated production
handoff check. `production/godot_project/godot_import_report.json` adds a fresh Godot 4.7.1
import: 7 mesh instances/surfaces, 1,368 vertices, UVs and tangents on all seven surfaces, one
normal-mapped surface, and unit node scales. The first sandboxed Godot attempt imported the GLB but
could not write Godot user settings and crashed; the first normal runtime attempt then exposed a
typed-GDScript `fmt` inference error. Both failures were corrected before the passing run.

## Limits

This benchmark adds a fourth unrelated hard-surface/product family, but it remains source-specific
and automated. It does not establish broad low-intervention modeling ability, production texture
quality under compression/mips beyond this Godot import, or human professional acceptance.
