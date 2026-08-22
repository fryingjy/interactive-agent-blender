# CG Boost UV and production-bake tutorial reproduction

Stage 6 studies CG Boost's complete 59:06 UV course and Ryan King Art's 24:58 baking tutorial through
full audiovisual Gemini passes. Indexed title/creator/chapter metadata, retained thumbnails, and the
Blender 5.2 UV and Cycles baking manuals independently constrain the source claims. No video is
archived.

## Modeled evidence

- `uv_production_tutorial.blend` contains independently generated high and low cages in separate
  `HIGH_POLY` and `LOW_POLY` collections. Both modifiers remain live and unapplied.
- `tutorial_weird_cube_*` reproduces the tutorial's connected compound-form lesson as a box-like
  base grown through a curved tube into an enlarged rounded end. It is one connected all-quad cage,
  not overlapping primitive parts.
- `transfer_curved_clasp_*` applies the seam/bake workflow to a different C-shaped form.
- Matched `*_NO_SEAM_FAILURE` objects retain the technical failure. The low cages use 12-sided
  cross-sections, one authored longitudinal cut, Average Island Scale, packing, and positive margin.

The first piecewise-linear build was rejected despite passing automated checks: the bends were
faceted and the transfer self-intersected into a spike. The retained build uses a smooth clamped
Catmull-Rom centerline and reduced bend radii. This failure is evidence that mesh-health and UV
metrics do not replace visual review.

## Measurements and boundary

The tutorial cage reduces mean UV corner-angle error from `14.90°` to `3.97°`; the transfer reduces
it from `36.02°` to `5.09°`. Both corrected layouts contain one packed island, zero degenerate UV
faces, zero positive-area overlap pairs, and remain inside the 0-1 tile. Three-view high/low
silhouette IoU ranges from `0.9707` to `0.9936`. Both 512px tangent-normal bakes contain non-neutral
signal, use Non-Color, are saved externally, packed, and connected through Normal Map nodes. The
UV-driven checker renders deliberately expose remaining curvature stretch.

This is a bounded connected-cage interpretation, not an exact copy of CG Boost's downloadable mesh.
It closes the tutorial-stage seam/distortion/material/normal-bake exercise, while full packed PBR
channel delivery remains part of Stage 7.
