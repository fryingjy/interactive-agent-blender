# A-frame open-shell correction

## Evidence

The official IKEA KUPONG side render shows a folded A-frame: two leaning
faces meet at a short top rollover while the lower side remains open. The
stage-07 connected cage was technically all-quad and editable, but its
generic closed-shell operation bridged every exterior boundary from front to
rear. Its side render therefore read as a solid triangular wall rather than
the target's open-underbody structure.

## Diagnosis

Manifoldness is not a universal primary-cage quality requirement. For an
open manufactured shell, requiring the starting cage to be a closed volume
causes a reference mismatch. A continuous single object can validly begin as
an open surface and gain wall thickness later through an unapplied Solidify
modifier.

## Correct construction rule

For folded A-frame products:

1. Author one connected surface cage from measured front/rear grids.
2. Bridge only the physical fold/rollover boundary, never every outer
   boundary merely to make the base mesh manifold.
3. Keep the underbody and side opening visible in Workbench silhouette
   review.
4. Add a live Solidify modifier only after front, side, and isometric
   primary-form acceptance; do not apply it.
5. Add SubD/creases only after the open shell's support topology exists.

## Negative evidence retained

`runs/2026-08-16_ikea-kupong-model/stage_07_side_solid.png` demonstrates
why a closed all-quad cage is rejected for this target. It is not evidence
that all-quad topology or manifoldness is sufficient for visual fidelity.
