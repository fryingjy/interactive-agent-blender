# Operator card: Bevel

**Status:** DOCS ✓ | EXPERIMENT ✓ (pre-existing, this project) | FAILURE_CASE ✓ (pre-existing) | QUIZ pending

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
Bevel is the single most load-bearing operation in this project (used in every hard-surface prop). Deferred a fresh from-scratch reproduction in favor of prioritizing operations this project has NEVER used (dissolve, bisect, bridge edge loops, spin, rip, split, separate, symmetrize, fill/grid fill, slides) -- see those cards for this session's actual new experiments. Width Type and Clamp Overlap remain a real, stated gap: this project has only ever used bmesh.ops.bevel's defaults, never explicitly varied Width Type or tested an intentionally-too-wide bevel against Clamp Overlap.

## When to use / not use
Use for: softening a hard edge for realistic light response, adding a manufactured/machined look, avoiding a razor-sharp silhouette edge that would alias badly under subdivision or in a render.
Caution: on a subdivision control cage, an unbevelled hard edge reads as an unintended soft rounded corner under Catmull-Clark (see subdivision_surface.md) -- bevel vs support-loop choice is a real strategy decision, not interchangeable.
