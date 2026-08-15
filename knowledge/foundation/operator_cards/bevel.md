# Operator card: Bevel

**Status:** DOCS ✓ | EXPERIMENT ✓ (including modifier-order conflict) | FAILURE_CASE ✓ | QUIZ pending

## Source
- Tier A: [Blender Manual — Bevel](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/bevel.html), read 2026-08-07.

## Definition (from docs)
Smooths a corner or edge by replacing it with new geometry across a controllable width. Mode: Edit Mode. `Ctrl-B` bevels edges (and vertices where 3+ edges meet); `Shift-Ctrl-B` bevels vertices only, leaving edges unchanged.

## Key parameters (from docs)
- **Width Type**: Offset / Width / Depth / Percent / Absolute — changes what the Width number actually measures. Not yet reproduced in this project; every bevel_edges call so far has used the bmesh.ops default, not explicitly varied this.
- **Segments**: density of new geometry (higher = smoother). Directly exposed as `segments` in `mesh_ops.bevel_edges`.
- **Clamp Overlap**: prevents a bevel from overshooting past a neighboring face's edge. Not yet tested against a deliberately-too-wide bevel in this project.
- **Loop Slide**: whether new inner edges stay perpendicular to the beveled edge vs match existing inner-edge direction.
- **Harden Normals**: custom split normals so beveled faces read as smoothly shaded without affecting the rest of the mesh — relevant for hard-surface production prep, not yet used in this project (every prop so far relies on flat/smooth shading toggles, not custom normals).
- **Miter Outer/Inner**: controls whether extra geometry is added at a beveled corner to avoid pinching when 3+ edges meet at >180°/<180°. Directly relevant to this project's own bevel-corner-ID work below.

## Real findings from this project (empirical, pre-existing -- see blender_ops/persistent_ids.py and mesh_ops.py)
- `bmesh.ops.bevel` **interpolates custom data (including this project's persistent-ID layer) from a source element onto new geometry** rather than leaving new elements at the 0/unassigned sentinel -- confirmed directly: beveling one edge left three different vertices sharing persistent ID 7. `persistent_ids.ensure_persistent_ids`'s duplicate-detection (0-or-already-seen) exists specifically because of this.
- **`segments=1` removes the original corner vertex's persistent ID outright** (replaces it), while `segments=2` keeps the original corner ID alongside new ones — a real, asymmetric identity-discontinuity between bevel segment counts, found live during the SpeakerEnclosure benchmark (`README.md` "Item 23" writeup, decision 20).
- Beveling 4 vertical corner edges on a boxy body turned the flat top/bottom quad caps into 8-sided n-gons (the corner clipping removes a triangle of material from each cap corner) — a real, expected geometric consequence of bevel on adjacent faces, not a bug, fixed with `triangulate_ngons`.

## Fresh reproduction this session
Bevel is a load-bearing operation in this project. `runs/2026-08-10_bevel-parameters/` now reproduces
all five Blender 5.2 BMesh width types and an intentionally oversized bevel with Clamp Overlap both
off and on. At comparable nominal amounts, OFFSET, WIDTH, DEPTH, and PERCENT produced measurably
different volume/area results; ABSOLUTE matched OFFSET on the equal-edge cube fixture, which narrows
that equivalence to this geometry instead of universalizing it. Width numbers are not portable
between modes.

The 5.0-unit unclamped bevel remained manifold but expanded into a nonsensical 105.28-volume result.
Clamping constrained it to 3.15 volume, yet the minimum face area fell to approximately `1.4e-14`.
Therefore Clamp Overlap is a damage limiter, not a topology-quality guarantee. The typed operation
now exposes `offset_type`, `profile`, and `clamp_overlap`; every result still requires evaluated
surface and minimum-area inspection.

## When to use / not use
Use for: softening a hard edge for realistic light response, adding a manufactured/machined look, avoiding a razor-sharp silhouette edge that would alias badly under subdivision or in a render.
Caution: on a subdivision control cage, an unbevelled hard edge reads as an unintended soft rounded corner under Catmull-Clark (see subdivision_surface.md) -- bevel vs support-loop choice is a real strategy decision, not interchangeable.

## Bevel before or after Subdivision Surface (controlled reconciliation, 2026-08-15)

The source conflict is real, but the experiment rejects a universal order. On identical supported
all-quad box cages, weighted Bevel before Subdivision produced the broadest, smoothest radius and no
localized pinch candidates, at 2,400 evaluated quad faces. Crease-protected Subdivision followed by
weighted Bevel preserved the flattest panels and a tighter manufactured chamfer at 1,176 faces, but
concentrated highlights at three-edge corners and produced 16 localized curvature candidates. A
post-Subdivision Bevel without crease/support protection visibly over-rounded the design because
Subdivision moved the intended edge before Bevel evaluated.

Decision rule: use pre-Subdivision Bevel when the radius belongs to the smoothed primary form; use
crease/support protection plus post-Subdivision Bevel for a final tight chamfer on an already
controlled form, with explicit corner inspection. Never infer the right order from technical
cleanliness alone; all three fixtures were closed, all-quad, and manifold. Evidence:
`runs/2026-08-15_bevel-subd-order/`.
