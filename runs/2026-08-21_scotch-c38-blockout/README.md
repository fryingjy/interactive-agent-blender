# Scotch C38 tape dispenser — primary blockout, stage 1

Moving to a new prop after the MasterLock 140D's first human review. Chosen over starting
something entirely fresh: `runs/2026-08-16_reference-gathering-scotch-c38/` already has a
fully verified, unused reference package (`disposition: READY_TO_MODEL`, re-checked
2026-08-21 and still passing) and is Tier-1 item 2 on `docs/PROGRESSIVE_PROP_BENCHMARK_CURRICULUM.md`
-- the actual next step on the curriculum, not a random pick. Its prior model build (if one ever
existed) was swept up in the 2026-08-17 deletion; only the reference evidence survives.

## What this stage is

Two separate literal box primitives -- `UpperShell_HIGH` and `WeightedBase_HIGH` -- matching
`reference_plan.md`'s explicit staging: *"Begin with literal box profiles. Do not round the four
main body corners before the profile and cavity proportions match the board."* No taper, no
cavity, no cutter face, no rounding. This is deliberately not yet a recognizable tape dispenser.

## Dimensions

| | Value | Source |
| --- | ---: | --- |
| Overall length (X) | 162.56 mm | official spec (6.4 in) |
| Overall width (Y) | 68.58 mm | official spec (2.7 in) |
| Overall height (Z) | 68.58 mm | official spec (2.7 in) |
| Base height | 20.0 mm | **visually estimated from reference photos, not spec'd** |
| Shell height (added atop base) | 48.58 mm | derived (total minus estimated base) |
| Shell width | 64.47 mm (94% of overall) | **visually estimated** -- the base visibly extends past the shell's footprint at the seam in all three reference photos |

Only the overall envelope is exact. The base/shell height split and the shell's narrower width are
readable in the reference photos but not measurable precisely from oblique shots -- flagged as
estimates to be corrected once the taper and seam are actually built and compared, not treated as
settled.

## Verification

`decision_state.current_revision()` at save: `0` -- primitive creation is the documented
one-time starting block (`object_ops.create_primitive`'s own docstring: "not itself an asset
builder"), not a typed decision. Real decisions -- shaping these boxes into the wedge profile,
cavity, and cutter face -- start from here through `DecisionTransaction`, unlike the MasterLock
build (which inherited pre-transaction-system geometry); this prop is typed from the very first
shaping edit.

## Shell taper (decision_revision 0 -> 1)

Tapered `UpperShell_HIGH`'s roofline: moved the two front-top vertices down to 60% of the rear
height, via a real `DecisionTransaction` (`TAPER_SHELL_ROOFLINE`). Structurally clean (0
non-manifold, 0 degenerate) and now reads as a genuine wedge silhouette against the reference's
gestalt in a front render.

The 60% figure is a visual estimate, not measured. Directly tracing the roofline from
`ofix_clean_profile.jpg`'s pixels was deliberately rejected as a method: the traced curve visibly
*peaks* mid-object (min-y column around x=340-360, rising toward both ends) rather than sloping
monotonically -- that shape is the oblique photo's own perspective foreshortening, not the object's
real profile, and copying it would bake a camera artifact into the mesh. `docs/
REFERENCE_COLLECTION_PROTOCOL.md`'s warning against tracing a perspective photo as if it were
orthographic applies directly here, same as it did on the MasterLock's negative-space decision.

## Top cavity (decision_revision 1 -> 2)

Cut the top cavity -- `reference_plan.md`'s declared "primary negative space" -- via
`ADD_TOP_CAVITY`. Same bisect-isolate-then-extrude technique validated on the MasterLock sockets
(no boolean, no inset+bevel): 4 vertical planes isolate a rectangular region of the shell's tilted
top face, that region's 4 corner verts are set to a flat floor Z directly (not translated by a
uniform delta, since the tilted roof means they start at different heights), then the original
face is deleted. Structurally clean (0 non-manifold, 0 degenerate). Bounds read off the shell's own
current geometry (not re-guessed): opens 15% in from the rear, closes at 80% along the length
(leaving room for the front cutter/bridge, not yet built), spans 58% of the shell's width, centered.

## Status

Real negative space now visible, matching the reference's gestalt. Still open, in order: base
footprint taper (currently a plain box; the reference shows it narrowing toward the front), the
front cutter face, and the hub/tape-roll assembly. One bounded decision at a time, each rendered
and checked before the next.
