# Blender Bros advanced SubD topology-sheet reproduction

Stage 4 begins with the complete `xUEs7cszlb0` lesson on topology size, flow, redirection, loop
termination, and curved-surface pinching. The modeled evidence must include matched clean/failure
patches, a curved deformation check, and a different-geometry transfer. Transcript claims remain
candidates until the actual audiovisual source and Blender reproduction support them.

This first Stage 4 run is a topology sheet, not a held-out prop and not a production asset claim.

## Result

The first Stage 4 sheet is complete. The full 16:08 source was inspected audiovisually and checked
against the previously retained timestamped captions. Four connected, all-quad, manifold cages were
then built with live unapplied SubD:

- a uniformly spaced curved shell and an equal-count uneven-spacing failure;
- a coarse sloped boundary whose grid runs directly into the perimeter and a matched correction
  with a continuous local support ring.

The curved pair confirms that topology count alone is insufficient: both evaluated to 450 vertices,
448 quads, and zero non-manifold edges, while the uneven cage produced the larger robust curvature
outlier and a visibly less balanced top-view arc. The boundary correction reduced diagnostic pinch
candidates from 20 to 4 and produced a substantially cleaner, controlled perimeter in MatCap.

A second matched pair now reproduces the tutorial's 2-to-1 loop-termination lesson using a new
generic validated `create_authored_quad_mesh` operation. Both samples begin as one connected open
patch with 21 vertices and 13 quads, then use the same live Bend, Solidify, and SubD stack. Moving
one reduction vertex behind the incoming boundary creates concave quads: the evaluated wire forms a
concentrated fan and MatCap shows a visible crease. The convex reduction remains smooth. Both
evaluated results are closed, all-quad, and manifold after live Solidify/SubD, so the failure is not
explained by object count, face count, or open delivery geometry.

The multi-problem topology sheet is complete. Stage 4 still requires a complete advanced SubD
tutorial asset that combines these rules before the ladder can advance.
