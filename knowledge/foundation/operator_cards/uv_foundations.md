# Curriculum card: UV seams, unwrap, distortion, and packing

**Status:** DOCS ✓ (Blender 5.0 Manual generation) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ~ | SECOND_SHAPE ✓

Official sources:

- <https://docs.blender.org/manual/en/dev/modeling/meshes/uv/workflows/layout.html>
- <https://docs.blender.org/manual/en/4.1/modeling/meshes/uv/editing.html>

## Studied behavior

- Split complex forms into suitable islands or mark seams, then unwrap and pack.
- Average Island Scale targets consistent scale; Minimize Stretch reduces angular distortion.
- Packing reduces wasted space but does not itself guarantee consistent world texel density or sensible seam placement.
- Multiple UV maps and layout transfer are valid for distinct production purposes.

## Blender 5.2 findings

Evidence: `runs/2026-08-10_uv-material-sculpt/`

The same non-uniformly scaled cube was seam-unwrapped before and after applying scale. Blender emitted its own warning for the unapplied case. World-space texel-ratio coefficient of variation fell from `0.5345` to `0.2778` after applying scale. The result improved but was not perfectly uniform, so Apply Scale is a precondition—not a complete UV-quality solution.

Smart UV Project on a cube packed all UVs inside 0–1 and produced nearly equal face ratios. That is a useful mechanical baseline, not evidence that automatic islands are artistically or production optimal.

## Verification

Check seams, island count/continuity, overlap, bounds, distortion, world texel density, padding, orientation requirements, and intended material use. A UV layer's mere existence is not a pass.
