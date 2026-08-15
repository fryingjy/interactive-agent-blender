# Operator card: Bridge Edge Loops, Fill, Grid Fill

**Status:** DOCS ✓ (Blender 5.2 LTS Manual) | EXPERIMENT ✓ (multiple rounds, including real failures) | FAILURE_CASE ✓✓ (two distinct, understood failure modes) | QUIZ pending

## Official sources

- Bridge Edge Loops: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/bridge_edge_loops.html
- Grid Fill: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/face/grid_fill.html

Both current pages were fetched successfully on 2026-08-10 and identify controls relevant to the
recorded failures: loop pairing/twist/cuts/interpolation for Bridge, and Span/Offset plus Simple
Blending for Grid Fill. The Manual recommends equal vertex counts for predictable paired loops.

Never used in this project before this session. All three are genuinely new ground, and two of the three initial attempts failed in real, informative ways -- documented here rather than only showing the eventual working case.

## `bmesh.ops.bridge_loops(bm, edges=...)`

**Failure #1, root-caused**: first attempt used `edges=[e for e in bm.edges if e.is_boundary]` on two bare wire-edge rings (`fill_type='NOTHING'` circles, no faces at all). Produced 0 faces. Root cause, confirmed by direct inspection: `BMEdge.is_boundary` is defined as "exactly ONE linked face" -- a wire edge (0 linked faces) does not qualify, so the filter silently excluded every edge, leaving `bridge_loops` nothing to work with. **Fix**: for pure wire-edge loops, pass `list(bm.edges)` directly (or filter by `e.is_wire`), not `is_boundary`. Confirmed working after the fix: two separate 8-vert rings, 16v/16e/0f -> 16v/24e/8f (a correct tube wall, one face per edge pair).

**Separate no-op, understood, not a bug**: bridging the top and bottom boundary rims of a cube that still has its 4 side faces intact (only top+bottom faces deleted via `context='FACES'`) produces 0 new faces. This is *correct* behavior, not a failure -- the two rims are already connected by a valid manifold path through the existing side walls, so there is nothing left to bridge. Bridge is for loops that are NOT already connected by faces.

**Typed control update (2026-08-15):** `mesh_ops.bridge_selection(..., twist=<integer>)` now exposes Blender 5.2's low-level `twist_offset` parameter. The new controlled lab uses two matched 8-vertex loops and proves that `twist=2` changes the actual cross-loop vertex pairing while preserving eight quad faces and manifold bridge edges (the two open rims remain intentionally boundary edges). This solves the runtime omission that prevented an intentional pairing choice. It does **not** claim that twist alone repairs the earlier teapot handle: its two loops had unequal counts (10 and 12), so matching attachment-loop density and inspecting the bridge remain required before using a bridge in a production prop. Evidence: `runs/2026-08-15_bridge-twist-control/bridge_twist_control_report.json`.

## `bmesh.ops.grid_fill` / `bpy.ops.mesh.fill_grid`

Real API-level finding (confirmed against the Blender Python API): the low-level `bmesh.ops.grid_fill(bm, edges, mat_nr, use_smooth, use_interp_simple)` has **no `span`/`offset` parameters** -- those exist only on the higher-level `bpy.ops.mesh.fill_grid(span, offset)`. Do not expect to control grid orientation/pairing from the low-level bmesh operator.

**Simple case (4-edge single-quad hole): works correctly**, verified via `bpy.ops.mesh.fill_grid`: 5 faces -> 6 (deleted 1 face, filled it back).

**Grid case (12-edge boundary from a 3x3-subdivided hole): fails, with a real, specific, informative Blender error**, not a silent failure: `"Info: Connecting edge loops overlap"`, 5 faces -> 5 (no-op). Confirmed with a clean, step-verified reproduction (subdivide top face 2 cuts -> 9 sub-faces confirmed -> delete all 9 -> 12 boundary edges confirmed selected -> fill_grid still fails). The operator's automatic loop-pairing/corner-detection cannot unambiguously resolve a boundary with 3 equal-length segments per side without some additional disambiguation (likely explicit corner selection order or a different span value) that a plain "select all boundary edges" does not provide.

**Practical conclusion for this project**: do not assume `fill_grid`/`grid_fill` reliably re-fills a subdivided grid hole. It is reliable for the trivial single-face case; for a multi-segment grid hole, either avoid deleting the interior in the first place (edit in place instead) or plan to investigate span/corner-selection requirements before depending on it in a real prop.

## `bmesh.ops.triangle_fill` (fan fill, for comparison)
Works as expected on a simple 4-edge boundary: 5 faces -> 7 (adds 2 triangles + 1 diagonal edge for a 4-sided hole). No failure mode found in this session's testing.
