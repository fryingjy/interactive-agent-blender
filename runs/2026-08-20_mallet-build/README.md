# Wooden mallet — trust-rebuild after the 2026-08-19 magnifying glass purge

Built the same day the magnifying glass build was purged for repeated overclaiming (declaring the
neck/ring junction "fixed" from flat-grey renders and non-manifold counts alone, while it was still
visibly broken — see [[feedback_verification_before_claiming_done]] and
[[blender-modeling-technique-corrections]] in project memory).

## What this proves and what it doesn't

The mallet is a single continuous revolved profile (`blender_ops/profile_mesh.py`,
`revolve_closed_profile`) — no boolean anywhere, no join between separate objects. That deliberately
sidesteps the exact failure class that broke the magnifying glass (a boolean union between a fat
neck and a thin ring band). It's a valid, honest technique — a real object built this way would be
clean — but it means this build never actually re-tested the join skill that failed. That's the next
real test, not this one.

## Build

- 928 faces, 100% quads, 0 non-manifold, 0 ngons.
- Both end caps closed with `bpy.ops.mesh.fill_grid()` (all-quad), not `bmesh.ops.pointmerge`
  (triangle-fan pole) — the first version used pointmerge and the user caught the resulting SubD
  pinch immediately from a render.
- A metal ferrule ring added as raised profile geometry (not a separate joined object), with
  `bevel_weight_edge` marked on its 4 corner rings and a `Bevel` modifier (`limit_method='WEIGHT'`,
  before Subsurf) — the established project policy for genuinely sharp edges.
- Organized into `Model` (Subsurf active) / `LowPoly` (modifiers off) collections per established
  project convention, applied here for the first time.

## Real bug found and fixed, not hidden

Adding the ferrule's bevel weight introduced a visible sawtooth shading artifact on the *plain*
shaft above it — an area with no bevel-weighted edges at all. Diagnosed properly rather than
assumed:
- Ruled out edge-selection error (checked the actual `bevel_weight_edge` values on disk — exactly
  the 4 intended z-rings, nothing else).
- Ruled out `harden_normals` (artifact persisted with it off).
- Ruled out bevel-width overlap (persisted at width 0.008, an order of magnitude smaller).
- Isolated with a direct with/without-bevel render comparison: clean with the modifier removed,
  artifact present the instant it's added, at any width.
- Root cause: the plain shaft had a ~4-unit run with zero intermediate geometry sitting immediately
  next to four tightly-packed sharp corners. Fixed by adding support loops on the shaft and at the
  head/neck shoulder (the same underlying issue, pre-existing there too, just not noticed until this
  investigation) — matching the project's own documented "support/proximity loop cuts" technique
  ([[blender-modeling-technique-corrections]] §2, third data point).
- A small residual is still visible immediately at the bevel-weighted edge itself, not spreading into
  adjacent geometry — read as an acceptable transition at a deliberately sharp crease, not a defect,
  after diminishing returns on trying to chase it further.

## Status

Done as a small, honestly-verified asset. Not pursuing further detail (wood grain texture, etc.) —
that would be scope creep past what this exercise was for. Next real test: an object that requires
an actual two-part join (see `runs/2026-08-20_mug-handle-join/`).

**Human visual review (2026-08-20): accepted, no repair tickets.** Recorded via
`tools/record_external_visual_review.py` against `human_review.json` at scene_revision 0; see
`human_review_repair_handoff.json`. This is the first build in this project to actually complete
the human-review step described in `docs/HUMAN_VISUAL_REVIEW_PROTOCOL.md`.
