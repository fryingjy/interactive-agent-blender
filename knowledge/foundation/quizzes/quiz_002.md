# Retrieval quiz 002 — delayed foundation check

**Date:** 2026-08-10

**Conditions:** Answered as a new retrieval pass without copying quiz 001 answers. This is a second same-day check, not yet evidence of long-term multi-day retention.

## 1. Why can a manifold mesh still have poor topology?

Manifoldness checks connectivity/closure, not density, pole placement, face shape, editability, deformation flow, or highlight continuity. The tangent Boolean failure remained manifold while containing 18 degenerate faces and a zero-length edge; the uneven all-quad patch remained valid while its area variation was nearly five times its uniform control.

## 2. When should Dissolve be preferred to Delete?

Use Dissolve when removing an element while preserving the surrounding surface. Delete is appropriate when the region itself should become a hole or disappear. Scope still matters: broad Limited Dissolve erased an open patch in the BMesh lab, while dissolving only the shared diagonal merged two planar triangles into one quad.

## 3. How does support-loop spacing affect SubD?

Closer support constrains the transition and retains a sharper silhouette; wider spacing broadens curvature. In the controlled cube pair, tight support retained 0.9919 of span and wide support 0.9676. Neither number alone decides which design is correct.

## 4. Why does modifier order matter?

Each modifier receives the previous modifier's evaluated output, so order changes what geometry exists to process. The effect is pair- and topology-specific: Boolean/Bevel can be a design choice, Solidify before Bevel is necessary on a single plane, and Mirror/SubD failed in one flat-seam cage but stayed manifold in both orders on a curved exact seam.

## 5. When may a triangle be harmless?

On a flat, non-deforming, non-critical region where it preserves shading and downstream operations. The flat triangulated patch remained exactly planar under SubD; the same triangle context on a curved patch produced measurable normal changes.

## 6. When is an n-gon especially risky?

Across curvature, deformation, booleans, or SubD regions where implicit triangulation can alter shading and flow. A flat hexagonal n-gon stayed planar; its nonplanar counterpart showed 0.2598 base nonplanarity and an 11.88° evaluated adjacent-face change.

## 7. What does Mirror clipping change?

Clipping constrains Edit Mode movement at the mirror plane. It does not retroactively weld vertices already outside Merge Distance; seam distance, merge settings, local axes, origin, and evaluated topology still need inspection.

## 8. When should geometry remain separate objects?

When components are physically/conceptually separate, need independent transforms/materials/modifiers, repeat/mirror differently, or gain editability from modular construction. A continuous mesh is justified when surface continuity or deformation flow truly requires it.

## 9. When should a region be rebuilt rather than patched?

When repeated repairs fail, topology degrades, complexity grows, and visual improvement remains small. Track those signals per region; two or more failed repairs plus sustained degradation/complexity pressure should trigger an explicit rebuild decision.

## 10. Why can Boolean be useful as an intermediate workflow?

It quickly establishes intersections/cutouts whose silhouette and proportions can be evaluated before committing to final topology. The result still needs checks for tangency, n-gons, degenerates, edge lengths, shading, and editability, followed by cleanup or rebuild if needed.

## 11. Why is applying scale important before UV unwrap or width/thickness modifiers?

Many operations use local dimensions. Unapplied scale doubled measured Bevel/Solidify world dimensions and raised UV world-texel inconsistency. Applying scale improved consistency but did not automatically make the UV layout perfect.

## 12. Why is an existing UV layer or material slot not enough evidence?

A UV layer can be packed yet distorted or semantically wrong; a material can exist in a slot while no polygon uses it; `diffuse_color` can differ from the connected Principled Base Color. Validate the actual downstream data and assignment.

## 13. What must a BMesh script do that Blender does not guarantee automatically?

Maintain valid topology/selection state, refresh lookup/index tables when needed, write standalone BMesh changes back to the mesh, update Edit Mode data/tessellation appropriately, and free owned BMeshes. Operator return values and no-exception execution are not substitutes for post-state verification.

## 14. What does Shrinkwrap not solve in retopology?

It projects/conforms vertices; it does not choose density, route loops, isolate details, place poles, preserve animation deformation, or judge silhouette. Wrong projection direction can also produce a complete no-op.

## 15. What is the honest boundary of the current video capability?

The system can safely inspect permitted local video/audio streams, captions/transcripts, and timestamped frames. The project-owned fixture proves those modalities, not external expert knowledge. No inaccessible platform video is claimed as studied.

**Self-check:** 15/15 answers contain a mechanism, context, or measured example. This is still self-administered and same-day; a later cross-session quiz is required for stronger retention evidence.
