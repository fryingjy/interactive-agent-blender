# Secondary modifier breadth

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS (9/9 controlled assertions)

## Results

- Screw generated a 24-quad one-turn helical surface from a two-vertex profile.
- Remesh rebuilt an eight-vertex beveled cube into 2,528 vertices and 2,526 clean quads.
- Decimate ratio 0.25 reduced 320 icosphere faces to 80.
- Triangulate converted six cube quads into exactly 12 triangles.
- Smooth and volume-preserving Laplacian Smooth reduced the same noisy-sphere Laplacian signal
  from 0.08206 to 0.04345 and 0.04785 respectively.
- Corrective Smooth's `Only Smooth` mode moved vertices by up to 0.1653.
- Curve displaced a segmented strip by up to 1.838; Lattice displaced a subdivided cube by 0.4174.

Fresh-process evaluated-mesh verification independently accepted all seven applicable closed
results: Remesh, Decimate, Triangulate, Smooth, Corrective Smooth, Laplacian Smooth, and Lattice.
The Screw ribbon and Curve strip are intentionally open and are judged by operation-specific
topology/displacement rather than falsely required to be closed solids.

## Failure/access evidence

Direct browser fetches for all nine latest Blender Manual child URLs returned HTTP 402. Official
search-index text exposed the modifier index and substantive excerpts for Screw, Decimate,
Corrective Smooth, Curve, and Lattice. The lab reproduces runtime behavior in installed Blender
5.2; exhaustive child-page study is not claimed.

The first passing report accidentally persisted thousands of transient evaluated coordinates,
making the JSON over 10,000 output tokens. The runner now strips those calculation samples; the
final machine-readable report is 3.5 KB and retains only decision-relevant metrics.

## Limits

These are one-shape foundation cases. Corrective Smooth is not tested after an armature, Remesh is
not credited with production edge flow, Decimate is not retopology, and Curve/Lattice results are
not cross-asset runtime validation.
