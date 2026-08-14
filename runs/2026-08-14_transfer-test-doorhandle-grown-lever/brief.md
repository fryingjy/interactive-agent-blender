# Transfer test: connected-topology lesson, re-tested on a different base form

**Claim under test:** a part meant to read as structurally fused to a body must be grown from
the body's own mesh (extrude/inset/bridge), not built separately and conformed on afterward.
Captured from the user's live correction on the mug handle (`mug_handle_join`,
`runs/2026-08-14_shrinkwrap-vs-join-handle-correction/`). Never previously tried on a different
asset.

**Why a door handle, not the teapot:** the teapot re-tests the exact vessel-plus-appendage case
the mug already covered. A lever door handle changes the base form entirely -- a flat disc with a
through-bore, not a revolved vessel -- so passing here is evidence the principle generalizes,
not evidence it works twice on the same kind of object.

## What was built

`DoorHandle_Rose`, entirely through the typed decision-transaction protocol (18 committed
decisions, one `perform_decision` per transaction after an early correction -- see below):

1. Cylinder primitive (radius 1.1, depth 0.25) -- the rose disc.
2. Inset the top face to radius 0.45, extruded upward 0.4 -- the spindle boss, grown from the
   rose's own top face, not a separate ring.
3. Inset the boss top down to radius 0.25 and deleted it; inset the disc bottom down to radius
   0.25 and deleted it; bridged the two resulting boundary loops into one continuous through-bore.
4. Inset an 8-face patch on the boss's outer wall (arc centered on the attachment direction),
   then extruded it outward in stages: a straight 1.5-unit base segment, a taper (scale 0.75 in
   the cross-section plane), a straight 1.0-unit mid segment, then three 0.4-unit extrude+12°-
   rotate steps to curve the tip downward -- the lever arm, grown from the boss's own wall.
5. `set_smooth_by_angle` for shading, matching this project's standing shading policy.

**Final mesh health:** 300 vertices, 600 edges, 300 faces, 0 non-manifold edges, 0 ngons, 0
degenerate faces -- true at every one of the 18 intermediate steps, not just the end state.
Valence distribution: 292 quads, 4 tri-poles, 4 five-poles (at the bore-bridge seam, the same
kind of small pole cluster the user's own mug join produced).

## One real correction mid-build

Chained two `perform_decision` calls (extrude, then rotate) inside a single transaction. The
server's external-edit detector flagged the extrude's own edge-ID changes as unexpected
mid-transaction drift on the second call -- a stale transaction, correctly rejected via
`reject_decision` (clean rollback, no data loss) rather than forced through. Redid the two ops as
separate transactions, matching the pattern used everywhere else in this build. Documented here
rather than smoothed over: the protocol wants exactly one `perform_decision` per
begin/verify/commit cycle, not a batch.

## Honest limitations

- The curve came out gentler than the reference spec's 30-40 degree target (measured roughly
  8-9 degrees of drop from three 12-degree rotation steps) -- each `rotate_selection` call
  pivots around the selection's own median, which is a smaller effective lever arm than intended.
  Visually the curve still reads correctly in the front-view silhouette render, but the exact
  angle undershot the plan; a future pass could use a larger per-step angle or an explicit external
  pivot to hit the target more precisely.
- No wall-thickness / hollow interior was attempted (matches the reference notes' explicit
  "solid throughout for this milestone" scope).
- Only the connected-topology principle was transfer-tested here. The boss's through-bore
  (inset+delete+bridge to punch a hole through two separated faces) is a reusable technique in its
  own right but wasn't captured as its own knowledge item or separately transfer-tested.

## Result

`apply_transfer_test()` recorded a **PASS** on the door-handle build. The connected-topology
knowledge item's status moved from `CAPTURED` to `TRANSFER_VALIDATED` --
`runs/2026-08-14_shrinkwrap-vs-join-handle-correction/knowledge_items.json`. This is the second
genuinely transfer-tested item in the project (after the screw-modifier revolve), and the first
one tested on an asset type never seen during its capture.
