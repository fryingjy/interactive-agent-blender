# Secondary modeling modifiers

**Status:** official index/excerpts ~ | Blender 5.2 experiment ✓ | failure/access limit ✓ | runtime transfer mostly pending

## Generate modifiers

- **Screw:** revolves a correctly aligned profile around an axis; angle, screw offset, iterations,
  steps, merge, and normals govern the helix. The lab's two-vertex profile produced a 24-quad open
  helical ribbon. Open profile boundaries are expected, not a closed-solid pass.
- **Remesh:** rebuilds topology around volume/form. A beveled eight-vertex cube became a clean
  2,528-vertex/2,526-quad evaluated mesh at octree depth 5. This demonstrates uniform rebuilding,
  not animation flow or semantic-data preservation.
- **Decimate:** reduces evaluated triangle budget. Collapse ratio 0.25 reduced an icosphere from
  320 to 80 faces. Use for measured delivery/performance goals; do not treat it as intentional
  retopology or assume it preserves edge flow.
- **Triangulate:** makes delivery triangles explicit and reproducible. A six-quad cube evaluated to
  exactly 12 triangles. Stack position and quad/n-gon methods matter when downstream shading or
  export depends on diagonals.

## Deform modifiers

- **Smooth:** repeated neighbor relaxation reduced the noisy-sphere Laplacian signal from 0.08206
  to 0.04345 while moving vertices up to 0.1082. It can remove intended volume/detail.
- **Corrective Smooth:** in `Only Smooth` preview, three iterations moved the noisy sphere up to
  0.1653. Its production purpose is deformation correction with a valid rest/bind state; this
  preview is not armature-joint validation.
- **Laplacian Smooth:** volume-preserving mode reduced the same signal to 0.04785 with maximum
  displacement 0.0860. A lower scalar does not by itself prove better silhouette or anatomy.
- **Curve:** a 17-segment strip moved up to 1.838 along a guide. Dominant axis, origins, and global
  spatial relationship are preconditions; a wrong setup can deform in an unexpected direction.
- **Lattice:** a 3×3×3 cage smoothly displaced a subdivided cube up to 0.4174 without altering base
  topology. Fit/transform the cage before editing its control points; broad deformation can still
  damage proportions.

## Evidence and source boundary

`runs/2026-08-10_secondary-modifiers/` passes 9/9 declared runtime assertions. Direct fetches of
the latest official child pages returned HTTP 402; official search-index excerpts and the modifier
index were available. The source registry records that access limit, and this card does not claim
an exhaustive child-page/parameter study or second-shape transfer.
