# Connect Vertex Path

## Purpose

Connect selected vertices by splitting the faces and crossed edges between them. Use it when a
surface needs a deliberate connected cut and when inserting a vertex on only one side of a shared
boundary would create a T-junction.

## Preconditions and selection

- Blender Edit Mode uses `J` and can follow selection history for multiple vertices.
- The typed runtime deliberately requires exactly two visible selected endpoint vertices because a
  remote mesh-selection snapshot does not preserve trustworthy ordering for three or more points.
- Endpoints must be connected through a shared face region and must not already share an edge.

## Topology effect

The operation splits every crossed face and boundary edge. In the Blender 5.2 lab, opposite points
on one convex six-sided face produced two quads without new vertices. A diagonal path across three
quads inserted two boundary vertices and produced four quads plus two endpoint triangles. Therefore
it prevents hanging T-junctions, but it does **not** promise all-quad output.

## Good and bad use

Good:

- propagate a cut through all faces sharing a route;
- split an existing planar region while preserving one connected surface;
- repair the construction pattern that subdivides only one face along a shared edge.

Bad:

- claim that any diagonal route is SubD-ready merely because it is connected;
- use it when an existing edge already joins the endpoints;
- infer ordered multi-point paths from unordered remote selection state;
- accept endpoint triangles on a deformation-critical or highlight-sensitive surface without review.

## API and typed support

`bmesh.ops.connect_vert_pair` implements the two-endpoint route. Typed
`connect_vertex_path` probes an independent BMesh copy first, rejects invalid/degenerate outcomes,
clears inherited IDs on created geometry, and participates in transaction-owned rollback and
persistent-ID reconciliation.

For a SubD-sensitive repair, callers can pass `require_all_quads=True`. The independent BMesh
preflight then rejects the operation before mutation if its result would leave any triangle or
n-gon. This is deliberately a strict whole-mesh contract, not a promise that every connected path
can be made SubD-safe.

## Evidence and boundary

`runs/2026-08-16_connect-vertex-path/` contains 6/6 Blender 5.2 transaction cases (including a live
Edit Mode mutation), a solid topology render, saved `.blend`, and 5/5 fresh-process checks. Adjacent
and disconnected controls preserve the complete layered fingerprint and scene revision.

`runs/2026-08-16_connect-vertex-path-curved-transfer/` adds two nonplanar six-sided patch repairs:
each becomes two base quads with a live unapplied Catmull-Clark Subdivision modifier and clean
evaluated topology. A curved three-quad diagonal control is rejected by the strict all-quad
preflight with unchanged fingerprint and scene revision. The clean builder passes 6/6 assertions and
an independent fresh Blender process passes 9/9 checks. Evidence is still controlled geometry; real
prop use and ordered multi-point support remain open.

## Official sources

- Blender Manual: Connect Vertex Path
- Blender Python API: BMesh operators (`connect_vert_pair`)
