# Operator card: Bisect

**Status:** DOCS ✓ (Blender 5.2 LTS Manual) | EXPERIMENT ✓ | FAILURE_CASE ✓ | QUIZ pending | TYPED_SUPPORT ✓

## Official source

- Blender 5.2 LTS Manual, **Bisect**: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/bisect.html
- Fetched successfully on 2026-08-10; the page documents Plane Point/Normal, Fill, Clear Inner,
  Clear Outer, Axis Threshold, move/snap/flip controls, and filled-cut attribute behavior.

## Reproduction (this session)
`bmesh.ops.bisect_plane(bm, geom=<all verts+edges+faces>, plane_co=(0,0,0), plane_no=(0,0,1), clear_inner=False, clear_outer=False)` on a fresh cube (8v/12e/6f):

Result: 12v/20e/10f. +4 verts (new intersection points where the Z=0 plane crosses the 4 vertical edges), +8 edges (4 new cut edges + 4 existing vertical edges each split into 2), +4 faces (each of the 4 side faces split into 2 by the cut). `clear_inner=False, clear_outer=False` correctly left both halves in place, connected by the new cut edges -- a pure topology-adding cut, not a boolean split.

## Controlled clear/fill transfer

`runs/2026-08-10_bisect-foundation/bisect_foundation_report.json` reproduces all typed modes in
Blender 5.2.0 LTS. Clear Inner and Clear Outer each reduce a cube half to 8v/12e/5f and leave the
expected four-edge open boundary. The new `fill=True` mode caps that boundary, restoring a closed
8v/12e/6f result with zero boundary/non-manifold edges. Fill without either clear flag is rejected
because the un-cleared cut is internal and has no boundary loop to cap. Six of six cases pass.

## Failure lesson

`bmesh.ops.bisect_plane` does not expose the Manual's Fill toggle directly. The typed operation
must first bisect/clear, then cap only boundary edges returned in `geom_cut`; treating every cut
edge as a hole boundary would be incorrect for cut-only mode.
