# Curriculum card: Contextual topology under Subdivision Surface

**Status:** DOCS ✓ | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ ~ | RUNTIME_USE ✓ | SECOND_SHAPE ✓

## Principle

Triangles, n-gons, and non-four-valence vertices are not defects by category. Their effect depends on planarity, curvature, deformation, support context, density transitions, shading, and editability. Always inspect both the control cage and evaluated surface.

Official sources:

- <https://docs.blender.org/manual/en/5.0/modeling/meshes/editing/index.html>
- <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/subdivision_surface.html>

## Blender 5.2 controlled specimens

Evidence: `runs/2026-08-10_topology-subd/`

- Valence-3, -5, and -6 poles on planar open fans remained planar under Catmull-Clark, demonstrating that pole presence alone does not imply visible pinching.
- A triangulated flat patch stayed exactly planar, while the same topology on a curved patch produced a 7.60° maximum adjacent-face normal change.
- A planar six-sided n-gon remained planar; a deliberately nonplanar counterpart had 0.2598 base nonplanarity and an 11.88° evaluated adjacent-face change.
- An uneven all-quad patch raised evaluated face-area coefficient of variation from 0.1244 to 0.5992 despite remaining planar. All-quads did not make its density good.
- Tight generated support geometry retained 99.19% of cube span, while a wider transition retained 96.76%. Both independently verified clean, but they intentionally produce different edge sharpness/highlight width.
- Matched circumferential loops preserved an all-quad cylindrical side with very low evaluated area variation (`~0.000063`).

## Interpretation boundaries

Most planar specimens are intentionally open, so boundary-edge counts are expected and are not closed-solid failures. Conversely, clean manifoldness on the support cubes does not decide whether their highlight width fits a design.

Use poles and loop terminations to redirect density where the resulting surface tolerates them. Keep nonplanar n-gons and abrupt density changes away from critical curved/highlight regions unless evaluated evidence supports the choice. Prefer measurable surface behavior over blanket topology slogans.
