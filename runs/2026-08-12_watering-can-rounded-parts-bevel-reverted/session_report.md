# Corrective reversal: incorrect bevel weighting on rounded parts

## What went wrong

Direct human visual review (screenshots of `Rose_Head`, `Handset`, and the watering-can
handle/spout, annotated with the specific over-weighted edges) found that the earlier no-Bevel
triage corrections in this session made three watering-can parts and the telephone handset **look
worse and less accurate**, not better. Comparing against the actual reference photos confirms it:

- `Rose_Head` (the watering can's spray-head fitting) is a smoothly rounded dome in the reference.
  The correction gave it visible hard facet edges and highlight breaks -- a faceted-gemstone read
  instead of a rounded nozzle.
- `Connected_Tapered_Spout` and `Arched_Handle` are smooth, continuously curved tube/tapered forms
  in the reference. The correction gave the spout/handle assembly a crisp hard seam running its
  length instead of a soft cylindrical highlight.
- `Handset` (the telephone receiver) is a smooth bakelite-style shape in the reference. The
  correction gave it the same crisp seam-down-the-shaft defect.

## Root cause

`sharp_edge_ids()` (used by all of this session's no-Bevel triage corrective scripts) selected
*every* edge with a dihedral angle over 25 degrees between its two faces and gave it a real
geometric Bevel weight. That conflates two different things:

1. **Shading hardness** -- already handled correctly by Smooth by Angle alone, purely from
   geometric angle, with no Bevel modifier needed at all.
2. **Physical edge rounding** -- a real geometric operation (adding polygons to create a visible
   radius/chamfer) that should only be applied where the actual reference shows a genuine
   machined/pressed seam.

On a low-segment-count round member (these parts have 8-16 sides around their circumference, not
100+), the *natural* angle between adjacent segments is large simply because there are few segments
-- not because those edges represent an intended hard transition. The threshold selected nearly
every circumferential edge on these parts, so the WEIGHT-limited Bevel added a real visible chamfer
strip at each one, turning "faceted-but-smoothly-shaded" (correct, matches the reference) into
"actually faceted" (wrong).

This is exactly the failure mode this repository's own `smooth_by_angle.md` already warned about
("Weighting every edge creates uncontrolled highlight breakup and does not mean every edge is a
physical design edge") -- the corrective scripts built this session reproduced it at scale through
an automated heuristic instead of reference-driven judgment, and neither the technical audit nor the
"before is blurry, after has facets -> looks like an improvement" visual check caught it, because
neither compares against the actual reference photo.

## Fix

`tools/run_revert_incorrect_rounded_part_bevels.py` removes the `WEIGHT`-limited Bevel modifier,
the `bevel_weight_edge` attribute, and the `hard_surface_intended_bevel_edge_ids` property from all
four objects, leaving Smooth by Angle as their only shading policy -- the same strategy
`Connected_Vessel` already used successfully (real Bevel weight only at its genuine rim/shoulder
seams, smooth shading everywhere else via adequate segment count). Rendered comparisons after the
revert show all four parts reading as smooth, continuous, rounded forms again, matching the
reference.

`Opening_Rim` and `Opening_Shadow` (watering can) were deliberately **not** reverted: the reference
does show a real pressed-lip edge at the vessel's opening, and their visible faceting in the
corrected render is consistent with the pre-existing, already-accepted `Connected_Vessel` body's own
16-sided segment count, not a new defect this session introduced. This is left as an open question
rather than decided unilaterally.

## Verification

- `tools/verify_revert_incorrect_rounded_part_bevels.py` (separate process, 13/13 checks): confirms
  the Bevel weighting is actually gone on all four objects, all four remain evaluated-clean,
  `Connected_Vessel`'s and `Main_Housing`'s genuine seam bevels are undisturbed, `Handset`'s
  Subdivision modifier is preserved, and both immediate source files are byte-for-byte unmodified.
- Visual re-render (`reverted_isometric.png` in both output directories) confirms the fix against
  the reference by eye, not just by mesh validity.

## What this means for the rest of this session's no-Bevel triage work

The mechanism itself (`set_bevel_weight_by_ids`, persistent-ID recording, the
`get_hard_surface_shading_audit` check) is not wrong -- it correctly records and verifies whatever
edge selection it is given. The defect was entirely in *which* edges the corrective scripts chose to
weight, using a geometric-angle threshold instead of reference-driven judgment. The boombox's 11
corrected small parts and the telephone's 15 corrected trim parts (dial apertures, clock face, trim
panels) used the same flawed selection method and have **not** been individually re-checked against
their references in this pass -- the boombox asset was separately rejected and removed entirely on
its own visual merits, and the telephone trim parts remain an open item.
