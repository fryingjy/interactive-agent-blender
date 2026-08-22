# Blender Guru beginner scene — corrected completion pass

This run continues the incomplete 2026 Blender Guru beginner tutorial reproduction at
`https://www.youtube.com/watch?v=z-Xl9tGqH14`. The prior failure remains documented in Git history;
its redundant v2 blend/render were removed after v3 and v4 superseded them. It visibly failed in
composition, object separation, coffee geometry, and the missing sprinkle stage.

The current pass uses two independent source paths: the timestamped public captions for procedural
coverage and the creator-published still on Blender Guru's Blender 5 tutorial page for visual
comparison. Gemini audiovisual extraction was attempted after the ramen lesson but hit the active
free-tier quota and therefore remains pending; it is not represented as completed evidence.

## Corrections made

- moved the plate under the donut and raised the food onto it;
- separated the mug from the donut silhouette while keeping its connected extruded handle visible;
- replaced the 14-vertex coffee ngon with a 32-sided shallow liquid surface and live Bevel;
- implemented sprinkles through a live, unapplied Geometry Nodes scattering modifier;
- reduced excessive sprinkle density and randomized orientation after rejecting the first uniform
  upright result;
- iterated the camera three times until both objects and the mug handle read in the final frame;
- added controlled key/fill lighting and a neutral backdrop.
- rejected v3 after creator-still comparison showed pale, washed-out values;
- corrected v4 toward the verified top-down composition, dark countertop, partly cropped upper-right
  mug, stronger pink icing, darker ceramic, and five live sprinkle color sources.

The scene preserves the original tutorial-modeled donut, connected mug/handle, icing, and plate.
The new modifier stack remains live; no tutorial geometry was flattened merely to make the render.

## Status

`TECHNICALLY_VERIFIED / CREATOR-STILL FIDELITY 7.0/10 / DOES NOT PASS`.

All eight tutorial subject areas are represented in `beginner_scene_v4.blend`, including live
Shrinkwrap, Solidify, Subdivision, Geometry Nodes scattering, materials, and final lighting.
`independent_verification_v4.json` proves that the fresh saved file contains the expected objects,
five hidden sprinkle sources, live modifiers, and manifold evaluated icing/plate surfaces.

The result does not reach 8/10. It matches the creator still's broad composition and object layout,
but the donut and icing remain too regular, the plate and countertop lack the source texture, the
sprinkle distribution is less natural, and the lighting/material response is much simpler. The
main learned correction is that matching object inventory is insufficient: camera, relative scale,
tonal hierarchy, material response, and deliberately irregular primary forms control resemblance.
