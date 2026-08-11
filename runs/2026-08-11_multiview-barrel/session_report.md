# Multi-view profile-authored industrial barrel

**Status:** PASS for the declared corrective multi-view and topology gates. Not held-out evidence.

## Reference and use boundary

- Source: Poly Haven `Barrel_01`, CC0, https://polyhaven.com/a/Barrel_01
- Source GLTF SHA-256: `e084945dedd6a3379c6f3e97842cac89df7169797707e123a5e5b42c135d6888`
- The source mesh was used only to render neutral front/side/top/isometric reference images. Its
  topology was not inspected, copied, or used as a modeling recipe.
- Because the builder and measurements were developed against this asset, this run is explicitly
  corrective/reference-development evidence and cannot count as held-out generalization.

## Closed loop

1. Measured a 0.638655 front width/height ratio, identical front/side silhouettes, a circular top,
   major-hoop landmarks at 31.7% and 69.6% of height, 11 central corrugations, and two lid fittings.
2. Stage 1 initially produced a 0.515419 ratio. That failed checkpoint is retained; the corrected
   primary body reached 0.636364 before secondary work proceeded.
3. Stage 2 integrated the corrugations. An initial implementation used separate major-hoop and seam
   meshes; user review correctly rejected that topology strategy.
4. Rebuilt the wall, both major hoops, all corrugations, and both rolled seams as one continuous
   revolved profile. The lid and bung assemblies remain separate because they are physically separate.
5. Independent evaluation caught 96 degenerate faces created by a redundant bevel modifier. Removing
   the modifier produced a clean base and evaluated body.
6. Top-view circle detection exposed a swapped/too-inward fitting placement. The final fitting errors
   are 8.544 px/1.1 px radius for the large bung and 3.606 px/1.2 px for the small vent.

## Final evidence

- Body base cage: 5,376 quads, zero non-quads, zero non-manifold edges, one connected component.
- Evaluated collection: 6/6 meshes closed, outward, UV-bearing, non-degenerate, and free of n-gons or
  loose geometry.
- Normalized silhouette IoU: front 0.977375, side 0.977375, top 0.994176, mean 0.982975.
- No mesh primitive operators are used. Geometry comes from explicit profile revolution and explicit
  capped fitting construction.

## Honest limitations

- Surface wear, dents, warning decal, and texture variation were not recreated; the final material is
  a clean painted-metal presentation used to inspect form and highlights.
- Silhouette scores are bbox-normalized and do not prove absolute world scale or camera calibration.
- The source is rotationally symmetric in front/side silhouette, so this run does not test asymmetric
  side-form reconstruction.
- No independent experienced modeler has accepted the asset, and this single corrective asset does
  not prove professional proficiency or held-out transfer.
