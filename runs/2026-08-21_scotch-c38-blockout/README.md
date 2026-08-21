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

## Status

Primary envelope blockout only. Not yet reviewable as "does this read as the object" -- a plain
stacked box doesn't yet. Next decision: taper the shell's roofline (sloped from tall rear to lower
front cutter face) per the reference photos, one bounded edit at a time, each rendered and checked
before the next.
