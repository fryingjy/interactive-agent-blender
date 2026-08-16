# Curriculum card: UV seams, unwrap, distortion, and packing

**Status:** DOCS ✓ (Blender 5.0/5.2 Manual generations) | VIDEO ✓ (official Blender lesson) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ~ | SECOND_SHAPE ✓

Official sources:

- <https://docs.blender.org/manual/en/dev/modeling/meshes/uv/workflows/layout.html>
- <https://docs.blender.org/manual/en/4.1/modeling/meshes/uv/editing.html>
- <https://docs.blender.org/manual/en/latest/render/cycles/baking.html>
- <https://docs.blender.org/manual/en/dev/render/shader_nodes/vector/normal_map.html>
- <https://commons.wikimedia.org/wiki/File:UV_Unwrapping_-_Blender_2.80_Fundamentals.webm>

## Studied behavior

- Split complex forms into suitable islands or mark seams, then unwrap and pack.
- Average Island Scale targets consistent scale; Minimize Stretch reduces angular distortion.
- Packing reduces wasted space but does not itself guarantee consistent world texel density or sensible seam placement.
- Multiple UV maps and layout transfer are valid for distinct production purposes.

## Blender 5.2 findings

Evidence: `runs/2026-08-10_uv-material-sculpt/`

The same non-uniformly scaled cube was seam-unwrapped before and after applying scale. Blender emitted its own warning for the unapplied case. World-space texel-ratio coefficient of variation fell from `0.5345` to `0.2778` after applying scale. The result improved but was not perfectly uniform, so Apply Scale is a precondition—not a complete UV-quality solution.

Smart UV Project on a cube packed all UVs inside 0–1 and produced nearly equal face ratios. That is a useful mechanical baseline, not evidence that automatic islands are artistically or production optimal.

`runs/2026-08-10_uv-bake-learning/` adds a genuine lesson-to-experiment loop on a different flared
housing. Twenty-seven authored seams produce two cap islands plus one opened side strip; the packed
layout has zero degenerate UV faces and `0.12050` world texel-ratio CV. A real Cycles
Selected-to-Active tangent bake from a 1,602-vertex detailed source to a 50-vertex low mesh produced
27,552 non-neutral pixels. The missing-high-source failure was reproduced, and both meshes passed
fresh-process verification. This replaces the earlier synthetic-normal-map-only evidence with an
actual high/low bake. That historical run is no longer retained and cannot serve as current
reproduction evidence by itself.

`runs/2026-08-16_uv-seam-production-transfer/` restores current Blender 5.2 evidence and transfers
the seam mechanism across a radial tube and a bent rounded-rectangular tube. Each high/low source is
one connected all-quad cage with live unapplied Solidify→Bevel modifiers. One longitudinal seam
opens each periodic low cage into one measured UV island. Against matched no-seam controls, mean
corner-angle error falls from `15.00°` to `1.87°` and from `14.82°` to `0.66°`. Both UV layouts are
nondegenerate and packed in the unit tile; both tangent bakes, three-view production audits,
low-only GLB imports, and fresh source checks pass. This is controlled tube-family transfer, not a
universal seam layout or real-asset runtime use.

## Verification

Check seams, island count/continuity, overlap, bounds, distortion, world texel density, padding, orientation requirements, and intended material use. A UV layer's mere existence is not a pass.
