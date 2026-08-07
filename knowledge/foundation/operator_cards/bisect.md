# Operator card: Bisect

**Status:** DOCS pending (Manual page not yet fetched) | EXPERIMENT ✓ | FAILURE_CASE pending | QUIZ pending

## Reproduction (this session)
`bmesh.ops.bisect_plane(bm, geom=<all verts+edges+faces>, plane_co=(0,0,0), plane_no=(0,0,1), clear_inner=False, clear_outer=False)` on a fresh cube (8v/12e/6f):

Result: 12v/20e/10f. +4 verts (new intersection points where the Z=0 plane crosses the 4 vertical edges), +8 edges (4 new cut edges + 4 existing vertical edges each split into 2), +4 faces (each of the 4 side faces split into 2 by the cut). `clear_inner=False, clear_outer=False` correctly left both halves in place, connected by the new cut edges -- a pure topology-adding cut, not a boolean split.

## Not yet tested
`clear_inner=True`/`clear_outer=True` (removing one side of the cut, the more common real use -- e.g. cutting a prop in half for a cross-section, or removing material past a plane) -- deferred, real gap.
