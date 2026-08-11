# Operator card: Dissolve (verts/edges/faces) vs Delete

**Status:** DOCS ✓ (Blender 5.2 LTS Manual) | EXPERIMENT ✓ | FAILURE_CASE ✓ (the whole point of this card IS the failure-mode distinction) | QUIZ pending

## Official source

- Blender 5.2 LTS Manual, **Deleting & Dissolving**:
  https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/delete.html

Fetched successfully on 2026-08-10. The current page distinguishes vertex/edge/face deletion,
Only Edges & Faces, Only Faces, dissolve variants, Limited Dissolve, Edge Collapse, and Edge Loops.

## Core distinction, confirmed by direct reproduction (this session, fresh -- never used in this project before)

**Dissolve removes an element and MERGES the surrounding geometry to fill the gap** (result is a valid, closed mesh with an n-gon where the element used to be). **Delete removes an element and its dependents, leaving an actual hole** unless a `FACES` context also removes now-unused boundary edges/verts.

| Operation | Cube 8v/12e/6f before | After | N-gons after |
|---|---|---|---|
| `bmesh.ops.dissolve_verts(verts=[v])` (1 vertex) | 8/12/6 | 7/9/4 | 1 (the 3 faces meeting at that corner merge into one) |
| `bmesh.ops.dissolve_edges(edges=[e])` (1 edge) | 8/12/6 | 8/11/5 | 1 (the edge's 2 faces merge; verts unchanged since the edge's endpoints are still used elsewhere) |
| `bmesh.ops.dissolve_faces(faces=[f1,f2])` (2 adjacent faces) | 8/12/6 | 8/11/5 | 1 (merges into one n-gon, removes their shared edge) |
| `bmesh.ops.delete(geom=[v], context='VERTS')` (1 vertex) | 8/12/6 | 7/9/3 | -- (all 3 faces touching that vertex are gone entirely -- a hole, not a fill) |
| `bmesh.ops.delete(geom=[f], context='FACES_ONLY')` (1 face) | 8/12/6 | 8/12/5 | -- (verts/edges untouched -- a hole with its boundary wireframe still fully intact) |

## When to use which
- **Dissolve**: cleaning up unwanted topology while keeping the mesh watertight/closed -- e.g. removing a support loop that's no longer needed, collapsing an accidental extra edge. Produces an n-gon; follow with `triangulate_ngons` if the n-gon then matters (subdivision boundary, export requirement).
- **Delete with VERTS/EDGES/FACES context**: genuinely removing material, creating an opening (e.g. before `bridge_edge_loops` or `extrude` to build a cavity/socket) -- matches this project's own established pattern (SpeakerEnclosure's driver cavity: inset then extrude the resulting inward-facing hole, not dissolve).
- **Delete with FACES_ONLY**: keep the boundary wireframe (verts/edges) but remove the face -- useful right before `bridge_edge_loops` or `grid_fill`, since those need existing boundary edges to attach to.

## Real gotcha found this session
`context='FACES_ONLY'` vs plain `context='FACES'` matters and is easy to get wrong -- `FACES_ONLY` was required for the bridge/fill experiments below specifically because it preserves the boundary edges that `bridge_loops`/`fill_grid` need to operate on; plain `FACES` would also strip the now-unused boundary edges/verts, leaving nothing to bridge/fill against.
