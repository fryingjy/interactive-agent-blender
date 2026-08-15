# Teapot body: revolved profile complete, spout attempt reverted with lessons kept

**Status: body done and clean; spout not yet attached (reverted after a real bug, not silently
abandoned).** Started toward the teapot per `reference/teapot/notes.md` (the mug's replacement
transfer-test candidate: two grown appendages instead of one).

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

## Next step (not done in this pass)

Reattach the spout lower on the body, at the z=0.51 ring, where the outward normal was directly
measured and confirmed reliable: `(0.922, 0.091, -0.376)` at a face near angle 0 -- clearly
X-dominant and outward, unlike the ambiguous z=1.4 ring. Apply the "always re-select by ID before
each perform_decision" fix throughout. The handle (C-shaped, two attachment points, needs a real
`bridge_selection` back into the body) is a further stretch goal beyond that.
