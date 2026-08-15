# Teapot body: body + spout complete, handle grown but not fully closed as a two-point loop

**Final status:** body and spout are DONE -- one continuous manifold mesh, 343 vertices, 42
non-manifold edges (exactly the mouth + the intentional pour opening), 0 degenerate faces. The
spout's blocking bug was root-caused with a controlled test and fixed for real (see "Third attempt"
below). The handle is grown and connected at its base, reading correctly as a curved hook in
silhouette, but stops short of the reference spec's two-point closed loop -- see the dedicated
section below for exactly why and what's needed to close that gap.

Started toward the teapot per `reference/teapot/notes.md` (the mug's replacement
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

## Third attempt: root-caused on a controlled test, then fixed for real

Built `ExtrudeBugTest_Cube` (a bare cube, away from the teapot) and extruded its +X face once.
**Found it immediately:** the original face's persistent ID (23) was NOT deleted and NOT kept on
the new cap -- it was silently reassigned to one of the new SIDE-WALL faces (center shifted 90
degrees off-axis, normal rotated to match). The genuine new cap got a completely different, fresh
ID. Confirmed the fix by extruding the CORRECT cap face a second time: direction was right
(x: 1.0 -> 1.5, continuing straight out).

This exactly explains all three teapot failures: every one of them reused a pre-extrude face ID for
a follow-up extrude, which by then pointed at a side wall, not the cap. `inset_selection` genuinely
does preserve the original ID on its shrunk inner patch (confirmed separately, still true) --
`extrude_selection` does not behave the same way despite the surface-level similarity ("leaves the
same patch, resized/moved, selected").

**The fix applied:** after every `extrude_selection` call, read the new cap's face IDs from that
same call's own `id_delta.faces.added`, filtered to faces whose vertices are entirely a subset of
`id_delta.verts.added` (side walls mix new and old boundary vertices; the cap doesn't). Never reuse
a pre-extrude ID for anything past that extrude.

Rebuilt the spout a third time with this fix, re-selecting explicitly by the correct ID before
every single `perform_decision` (also still needed, per bug #1 -- `commit_decision` resets
selection to the whole mesh). Measured the new cap's average X position after every one of the 4
extrude steps to confirm direction empirically rather than trusting it: 2.09 -> 2.591 -> 3.021 ->
3.512 -> 4.005, monotonically outward the whole way. Opened the pour tip (deleted the final cap),
applied the standing shading policy. Final: 211 verts, 417 edges, 206 faces, 42 non-manifold edges
(32 mouth + 10 pour opening), 0 degenerate faces -- clean at every one of the ~10 decisions in this
attempt, not just the end state. Front and top silhouette renders both read correctly as a genuine,
symmetric teapot spout.

Wrote this up as a proper `KnowledgeItem`
(`runs/2026-08-14_extrude-id-reassignment-bugfix/knowledge_items.json`), captured on the bare-cube
test and transfer-tested for real on the teapot spout (`apply_transfer_test`-equivalent PASS,
status `TRANSFER_VALIDATED`) -- the project's third genuinely transfer-tested item, and the first
one about the modeling *tooling itself* rather than a modeling technique.

## Handle: grown as a curved arm, closed as a cantilevered hook rather than a true two-point loop

Grew a handle arm from the wall opposite the spout (angle 180, z=1.4 ring -- confirmed reliable
outward normal `(-0.988, -0.097, 0.123)` before extruding, same discipline as the fixed spout).
Applied the extrude-ID fix throughout: 9 extrude+rotate segments (varying rotation angles, mostly
positive since this side mirrors the spout's sign convention), tracking the correct cap via each
step's own `id_delta` the whole way. The arm swept out, up and over, and back down near the body --
directly measured at each step rather than assumed, same discipline as the spout.

**Where it stopped short of the spec:** cut a second hole in the body wall near the tip's final
position (angle ~150 degrees, the nearest available untouched wall -- the exact angle=180 wall at
that height was already consumed by the arm's own base) and attempted `bridge_selection` to close
the loop. The bridge produced a genuine topological defect: 10 of the tip's boundary edges ended up
with 3 linked faces each instead of 2, traced to `bmesh.ops.bridge_loops` creating a *twisted* fan
between the two loops (10 verts vs. 12) -- two of the new triangular faces shared the tip's edge but
fanned out to nearly opposite points on the target loop (`y=+1.05` vs. `y=-1.03`), rather than a
clean radial connection. Not a stale-ID issue this time (confirmed: deleting the suspected "extra"
face made non-manifold edges go UP, not down, proving it was legitimate tube geometry, not a
duplicate).

Rather than hand-untangle a crossed bridge seam under time pressure, reverted the bridge cleanly
(deleted its 32 faces), capped the arm's tip as a dead end, and re-filled the second hole back to
flat wall. Result: **one continuous, fully manifold mesh** (343 verts, 42 non-manifold edges = only
the mouth + spout tip, 0 degenerate faces) with the handle reading as a genuine curved hook grown
from the body -- but attached at only ONE point, not the two-point closed loop the reference spec
called for. In silhouette (front view) the arm's curve passes close enough to the body that it
*reads* as an enclosed loop visually, even though it isn't topologically fused there.

**Honest gap from spec:** this is a cantilevered curved handle, not the C-shaped two-attachment-point
loop `reference/teapot/notes.md` describes. Closing that gap needs either (a) sizing the second hole
to match the tip's vertex count exactly before bridging, so `bridge_loops` gets a clean 1:1
correspondence, or (b) building the connecting geometry manually face-by-face instead of relying on
`bridge_selection` for a mismatched pair. Worth a dedicated pass, not a live fix under an already-long
session.

## Next step (not done in this pass)

Close the handle's loop properly (see above) if a true two-point-attached C-handle is wanted. The
chained-extrude direction bug is fully resolved; the remaining gap is specifically about
`bridge_selection` behavior on mismatched-size loops.
