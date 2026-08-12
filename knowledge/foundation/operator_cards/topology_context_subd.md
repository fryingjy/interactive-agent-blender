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

## Production transfer: connected product housing

Evidence: this section's original example (a boombox benchmark) was rejected on direct human visual
review for not resembling its reference at all -- wrong color, wrong proportions, generic detailing
-- and its files were removed entirely (2026-08-12); see
`docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md`. The topology-construction lessons below were not the cause
of that rejection and remain independently supported by `runs/2026-08-11_connected-camera-corrective/`
below, which demonstrates the same cut-grid-not-primitives principle on an asset that also passed
human review.

- When trim, recesses, ribs, or rings belong to one manufactured skin, first test whether cuts,
  inset/extrusion, and loop routing can keep them in one editable cage. Do not substitute intersecting
  primitives merely because the silhouette is easy to match.
- Separate meshes remain appropriate for genuinely separate assemblies such as doors, knobs,
  speakers, fasteners, handles, and repeated vent inserts.
- A bevel limited by a vertex group may affect unintended connecting edges on a subdivided grid.
  Inspect the evaluated result from an oblique fixed view; technical manifoldness does not catch
  corner fins or pinching. In this run, removing the unsafe perimeter bevel and retaining only the
  narrow recess treatment was the correct repair.
- Revolved profiles must not emit a full ring of coincident vertices at a zero-radius endpoint. Cap
  the adjacent nonzero ring or author a single pole; otherwise nominally closed radial parts contain
  zero-area faces.

## Corrective transfer: one-object product form

Evidence: `runs/2026-08-11_connected-camera-corrective/`

- Object count is not enough. Joining disconnected shells into one Blender object does not satisfy
  a connected-cage strategy; verify mesh connected-component count as well as scene object count.
- When the body and detail can be manufactured/read as one continuous skin, route the base surface
  into an inset loop and extrude that loop. The accepted camera routes a rounded-rectangle front
  perimeter into a circular lens loop and grows the stepped barrel from that loop.
- A technically clean four-sided lens failed visually because the cage encoded a square cap.
  Sparse topology must still carry the intended design shape.
- Thirty-two authored vertices were unnecessary for small circular controls. The first correction's
  four-sided top loops were also insufficient: SubD rounded them, but they remained rounded squares.
  The final controls use regular 12-vertex loops measured for equal radius and angular spacing.
- A 12-edge rectangular shell opening (five edges along each long side and one along each short side)
  bridges one-to-one into each 12-edge circle with quads. This is the topology consequence of using
  Edit Mode routing and extrusion instead of attaching a separate cylinder.
- Sharpness begins in the control cage. An n=6 rounded-rectangle superellipse remained pill-shaped
  even after the correct corner rails were weighted. An n=16 replacement improved it but still
  encoded curvature before Bevel. The accepted cage is a literal box perimeter with flat sides and
  exact 90-degree corner rails; Bevel alone controls the highlight width.
- Treat `12-16` as a tested range for controls at this scale, not a universal cylinder rule. The lens
  uses 24 because its radial loop matches a locally refined 24-edge body perimeter for an all-quad
  bridge; density follows connectivity and silhouette needs.
- The accepted result is one object, one connected component, 530/530 base quads, and 25,120/25,120
  evaluated quads after weighted Bevel and SubD. Its GLB returns as one mesh with exact evaluated
  bounds, UVs, and four materials.
