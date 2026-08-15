# Teapot body: revolved profile complete, TWO spout attempts reverted with a real unresolved bug found

**Status: body done and clean; spout not yet attached, after two separate attempts both reverted
cleanly.** Started toward the teapot per `reference/teapot/notes.md` (the mug's replacement
transfer-test candidate: two grown appendages instead of one). The user manually fixed the first
attempt's leftover ugly repair patch (3 small ngons) mid-session -- confirmed via
`get_full_state`'s external-edit detection, IDs re-synced cleanly, body was fully clean (0 ngons)
before the second attempt began.

## What was built successfully

`Teapot_Body` -- a 6-point profile (radius, z) spun 360 degrees around Z via `spin_selection`
(the same validated revolve mechanism from the first transfer test), then `merge_by_distance` to
fuse the ~32 near-coincident vertices spin leaves at an axis-touching point. Final: 168 vertices,
325 edges, 160 faces, 32 non-manifold edges (exactly the intended open mouth, nothing else), 0
degenerate faces, 0 loose verts. The mouth opens naturally because the profile's top point sits off
the Z axis (radius 0.9) while the bottom point sits on it (radius 0) -- no separate hole-cutting
step was needed for the lid opening.

## What went wrong with the spout, and the two real bugs found

Attempted to grow a spout from the wall's widest-point ring (z=1.4, r=2.24) using the same
inset+extrude+curve technique that passed the door-handle transfer test. Two distinct bugs
surfaced, both documented here rather than smoothed over:

1. **`commit_decision` resets selection to the whole mesh, not just the new geometry it left
   selected mid-build.** A `rotate_selection` call right after committing an extrude got 195
   verts (the entire body) instead of the intended 13-vert tip ring -- caught before it executed
   any damage (rejected the pending decision first). Confirmed via direct `get_selection` calls
   that `reject_decision`'s own restore covers geometry and transform only, NOT selection state.
   **Fix applied for the rest of this build: explicitly re-select the target elements by
   persistent ID (from the previous step's own `id_delta`) before every single `perform_decision`
   from that point on, never relying on selection surviving a commit.**

2. **`extrude_selection`'s "average face normal" direction assumption failed on a doubly-curved
   attachment point.** The door handle's boss sat on a simple cylindrical wall (normal ~= pure
   radial). The teapot's z=1.4 ring sits on a *tapering* section of the profile (radius decreasing
   as z increases toward the shoulder) -- the true local surface behavior there is more complex
   than a simple radial cylinder wall, and the first extrude moved the patch *inward* (measured:
   attach ring at x=2.162 -> post-extrude ring at x=1.581, i.e. toward the axis, not away from it)
   instead of outward. Confirmed the body's own overall normals are NOT inverted (checked a
   wall face far from the spout: normal direction matches the outward radial direction exactly).
   The bug is specific to relying on face-normal direction at a doubly-curved attachment point
   without verifying it geometrically first.

## Recovery (clean, no data loss)

Rather than leave a mangled or half-finished spout in the record: identified all 52 spout-related
faces by ID (everything created since the inset began, ID >= 746), deleted them, found and removed
7 leftover vertices from an earlier extrude stage that had escaped the ID-based deletion (they kept
low IDs from before the inset, per `inset_selection`'s own documented behavior of reusing the
original face's ID for the shrunk patch), then filled the resulting clean 14-edge boundary loop back
to a closed wall in 3 incremental `fill_selection` passes (contextual_create didn't close the whole
loop in one shot -- had to re-query the remaining open edges twice and re-fill). Final state: 32
non-manifold edges (mouth only), 0 degenerate faces, 0 loose verts -- genuinely clean, confirmed via
`get_full_state`. One small honest cosmetic blemish remains: the repair patch (3 small ngons instead
of the original 4 clean quads) creates a faint concave notch visible in the front-view silhouette
render -- not a manifold defect, `recalc_normals` didn't change it (so it isn't a backface-culling
artifact, just a slightly non-planar small patch). Left as-is rather than over-engineered away.

## Second attempt: reattached lower, direction confirmed on the FIRST extrude, then failed three more times

Reattached at the z=0.51 ring using the directly-measured reliable normal `(0.922, 0.091, -0.376)`.
Applied the "re-select by ID before every `perform_decision`" fix throughout. The very first
extrude from the original wall worked correctly -- measured, not assumed: x went 2.09 -> 2.591,
genuinely outward. Everything after that first extrude failed, in three different ways, each a
real attempt at a fix rather than a repeat of the same mistake:

1. **Anisotropic taper then extrude:** scaling the tip ring by `(1, 0.7, 0.7)` in world-aligned
   axes (not the ring's own tilted local frame) likely sheared the ring's plane, since this ring's
   normal has real Y and Z components (not just X). The next extrude moved inward (x: 2.591 ->
   2.241). Reverted; hypothesis untested further since the next two attempts also failed.
2. **Edge-based extrude of an open rim:** with no cap face to select, `extrude_selection` fell back
   to its edge path, which uses averaged boundary-vertex normals -- and a rim's vertex normal
   represents the tube's *radial* direction at that cross-section, not its *length* direction.
   Barely moved in X, mostly drifted sideways/down. Reverted.
3. **Face-based extrude of a freshly-filled, clean cap:** filled the open rim with
   `fill_selection` (closed cleanly, 32 non-manifold edges = mouth only, confirmed clean), selected
   the new cap faces specifically, extruded. Still moved inward (x: ~2.6 -> 2.318). This was the
   most surprising failure -- a proper single-normal-bearing cap face, freshly created, still gave
   the wrong direction. Reverted.

**This is now a real, unresolved, three-times-confirmed bug in chained/repeated
`extrude_selection` calls** -- the FIRST extrude from an original wall face reliably goes the
correct direction; SUBSEQUENT extrudes building on the newly-created geometry (regardless of
whether that geometry came from taper+extrude, edge-extrude, or a fresh fill+extrude) have failed
every single time in this session, 3 for 3. Not something to keep guessing at live under time
pressure -- stopping here rather than risking further mesh damage or shipping a broken build.
Fully reverted to a clean flat wall (161 verts, matching the pre-spout count exactly; 32
non-manifold edges = mouth only; 0 degenerate faces) rather than leaving anything half-built.

## Next step (not done in this pass)

**Before attempting the spout a third time:** investigate WHY chained extrudes fail directionally
in this codebase -- read `extrude_face_region`'s actual behavior on a controlled test case (a bare
cube, extrude twice in a row, check direction each time) rather than debugging live on a
complicated tapered profile. This deserves a dedicated lab script, not another live attempt. The
handle (C-shaped, two attachment points, needs a real `bridge_selection` back into the body) should
wait until the chained-extrude direction bug is actually understood and fixed, since it will hit
the exact same problem.
