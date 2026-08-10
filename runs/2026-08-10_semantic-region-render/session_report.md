# Semantic selected-region render and reference tickets

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS after one preserved visual false positive

## Result

A persistent face-ID region named `top_panel` rendered in green against red base-cage context from
an orthographic isometric camera. The final image contains 8,679 green-dominant target pixels and
17,498 red-dominant context pixels. Metadata records revision 77, camera, projection, resolution,
source object, region role, persistent face ID, and explicit `BASE_CAGE` geometry source. The saved
source independently verified clean.

Appending a nonexistent face ID made the region stale. Rendering was rejected before file creation
and returned the exact missing ID. The recognized semantic-role vocabulary now includes the
directive's `flat_panel` and `high_curvature` roles.

`make_reference_tickets` converts contour, enclosed-negative-space, landmark, and component-mask
errors into localized, severity-sorted tickets with stable priorities. Missing landmarks/components
receive hard severity 1.0 instead of being diluted in a global overlap score.

## Preserved failure

The initial top-panel render used a front view, leaving the target face edge-on and invisible.
Anti-aliasing still produced three quantized colors, so the original “multiple colors” assertion
passed falsely. `failed_attempt_region_edge_on.*` preserves that output. The final test uses an
isometric view and requires substantial red- and green-dominant pixel counts.

## Limits

Semantic face IDs belong to the editable base cage. Modifier evaluation does not provide stable
one-to-one face identity, so this pass does not pretend to highlight exact evaluated faces. Surface
diagnostic positions can instead be mapped approximately back to nearby cage IDs.
