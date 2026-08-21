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

## Hub

Added `Hub` as its own object -- `reference_plan.md` lists Hub/TapeRoll/CutterBlade as separate
functional assemblies from the shell (a removable plastic hub, independently manufactured).
Cylinder primitive, 12 radial sides, 25.4mm diameter matching the official "replaceable 1-inch
hub" spec. Position and height read directly off the cavity's own geometry.

Caught and fixed a real bug before committing, not after: the first attempt found the cavity's
extent by filtering "any vertex below some Z," which also matched the shell's actual bottom cap
(also well below zero) -- it silently put the hub's base 22mm too low, fully inside solid material
and invisible in the cavity rather than sitting in it. Direct inspection of every face's normal
found the actual bug: the cavity floor's outward normal points +Z (up, into the open cavity), not
-Z as assumed, and needed to be picked out from several similarly-oriented roof faces by being the
lowest of them, not the only match. Verified correct by rendering before saving the fix as final,
not by re-deriving the same wrong assumption more confidently.

## Tape roll

Added `TapeRoll` concentric with `Hub`. Width 19.05mm from the official "3/4-inch maximum tape
width" spec; outer diameter (38mm) is a visual estimate, flagged as such -- no exact spec exists
for it. In the combined material render the roll and hub visually blend into one shape, since both
currently share the same flat grey material and sit at a similar height/Z -- confirmed this is a
render-only artifact, not a geometry defect, by rendering each object's own wireframe separately
(`wireframe_TapeRoll_front.png` clearly shows a distinct 16-sided cylinder at the expected size).
Distinct materials belong at a later stage, not blockout.

## Base front chamfer (decision_revision 2 -> 3), correcting an earlier guess

A closer crop of the reference photo showed the base doesn't narrow along its length at all --
that was a misreading. What's actually there is a diagonal chamfered facet at the front corners,
the same kind of treatment already validated on the MasterLock 140D's front corner. Chamfered both
front (+X) corners via `CHAMFER_BASE_FRONT_CORNERS` (bisect_plane + edgenet_fill, same technique).
Only the front: the rear isn't visible in any reference photo at this angle, so it stays a plain
box edge rather than inventing a matching treatment with no evidence for it. Structurally clean.

## Cutter blade

Added `CutterBlade` -- `reference_plan.md`'s declared separate functional assembly (metal, a real
material/function boundary from the plastic shell). A close photo crop shows a thin metallic plate
with a serrated front edge, mounted at the shell's front-top edge, projecting slightly forward.
Serration itself is tertiary detail and not built yet -- this establishes the mass and position
only, per this same plan's own instruction not to add detail before primary form is settled.
Position read directly off the shell's own current front-face geometry, not re-guessed.

## Status

All five components `reference_plan.md` names are now present: `UpperShell_HIGH` (wedge, tapered,
with the cavity), `WeightedBase_HIGH` (chamfered front), `Hub`, `TapeRoll`, `CutterBlade`. This is
a genuine primary-form blockout, not just a box.

## Primary-form comparison against the reference

Segmented the reference photo (`reference_segmentation/`, `tools/segment_reference_grabcut.py`,
visually verified clean) but deliberately did **not** force a numeric silhouette IoU against it:
the photo is oblique (`front_right_oblique`, `PERSPECTIVE` per the manifest), the model has no
calibrated camera angle matching it the way the MasterLock inherited one, and forcing that
comparison would reintroduce the same oblique-vs-orthographic distortion problem already caught
once this session. A direct side-by-side crop against the model's iso render instead:

- **Reads as the same object.** Wedge shell, top cavity, hub + roll, stepped/chamfered base --
  all present and roughly proportioned right.
- **Real, visible difference**: the reference's rear shell corner and roofline are smoothly
  rounded/curved; the current blockout's are hard box angles. Not a defect at this stage --
  `reference_plan.md` explicitly stages rounding *after* proportions and cavity match the board,
  which is exactly where this build is. Flagged as the next real primary-form/secondary-form step,
  not silently left unrecorded.
- Minor, lower-confidence observations, not yet acted on: the cavity opening may read slightly
  narrow relative to the shell width in the reference; the cutter blade's integration with the
  front slope could be more continuous rather than a distinct add-on tab.

Not yet reviewed by a human.

## Rear shoulder rounding (decision_revision 3 -> 4)

Addressed the one real difference the comparison above found. Two real bugs surfaced and fixed
before this landed, not after:

1. The earlier `ADD_TOP_CAVITY` decision's Y-direction cuts weren't restricted to a local band and
   quietly split the rear-top edge -- far away in X from the cavity -- into three collinear
   segments. Same class of bug already fixed once on the MasterLock (unrestricted cuts reaching
   further than intended); harmless-looking here since the split stayed a straight line, only
   surfacing now that a bevel needed one clean edge, not three fragments. Fixed by dissolving the
   two redundant middle vertices first.
2. After that dissolve, no single edge remained directly connecting the two true rear-top corners
   (the flanking faces had different vertex counts -- 4 and 6 -- so the merge didn't preserve a
   bevelable ridge edge). Switched to a vertex bevel on the two corner points instead, which turned
   out to be the more correct tool anyway: the reference shows a real rounded 3D corner (roof,
   back, and side curving together), not just a curved ridge line.

Structurally clean (0 non-manifold, 0 degenerate). Real geometry, not just shading -- re-baked
`set_smooth_by_angle` afterward per this project's own established policy (smooth shading alone
does not make a hard edge read as round). Honest assessment: modest in scale compared to the
reference's more sweeping curve, and only the two extreme corner points are rounded rather than
the whole ridge -- a real improvement in the right direction, not yet a full match. Left as-is for
this pass rather than over-iterating on one shading detail.

## Roof shape (flat vs. curved): recorded as UNDECIDABLE, not resolved

Direct human feedback ("far from accurate, figure out why") led to re-examining whether
`UpperShell_HIGH`'s tapered roofline should actually be a single flat plane (as built) or a
continuously curved profile. A landmark-based pixel measurement on `ofix_clean_profile.jpg` came
back internally contradictory -- the traced boundary didn't behave consistently with either a
straight line or a clean curve. Root cause, confirmed today: a flat 3D plane does not project to a
straight line in image space under uncalibrated PERSPECTIVE projection (only under orthographic or
a calibrated camera does "does the silhouette look straight" actually test "is the surface flat").
The measurement had silently assumed an orthographic reading of an oblique photo -- the same mistake
this project's own docs already warned against for the shell taper decision above and the
MasterLock's negative-space decision, made again anyway because nothing actually checked the
reference's recorded projection before running the test.

Built the fix for the mechanism, not just the one measurement: `knowledge_engine/representation_hypothesis.py`'s
`evaluate_predicted_consequence()` now reads a reference item's `projection` before testing a
`boundary_linearity` prediction, and refuses with `UNDECIDABLE` on `PERSPECTIVE`/`UNKNOWN` instead of
guessing. Ran it for real against this exact question --
`runs/2026-08-21_scotch-c38-blockout/roof_shape_hypothesis.json` (both the flat and curved
candidates) against `runs/2026-08-16_reference-gathering-scotch-c38/reference_manifest.json`'s
`ofix_c38_left_side` item (`projection: PERSPECTIVE`) via `tools/test_representation_hypotheses.py`
-- and it reproduces today's real finding: both candidates come back `UNDECIDABLE` with the reason
above, saved in `roof_shape_hypothesis_result.json`.

**The precise pixel-linearity question stays UNKNOWN** -- that result doesn't change, and shouldn't:
it was never possible to prove or disprove flat-vs-curved by measuring pixel positions on a
PERSPECTIVE photo, and it still isn't.

**But a different, coarser kind of evidence turned up real signal, and the geometry has now been
changed on the strength of it (decision_revision 4 -> 5, `CURVE_SHELL_ROOFLINE`).** Looking directly
at the highest-quality reference image available (`media/retailer/texas_art_white_background.jpg`,
much cleaner than the small/blurry ofix crop the earlier pixel test used) shows the roofline reading
as one smooth continuous curve from the rear shoulder down to the front -- not a flat facet meeting a
hard crease. This is a *qualitative* shape-class judgment ("does this look like one curve or two
flat planes meeting at a line"), not a precision measurement, and it's a fundamentally different kind
of evidence than the boundary-linearity pixel test: a real 3D crease stays visually salient under
almost any projection, so this read is far more robust to the oblique camera angle than trying to
fit precise straight lines to pixel coordinates ever was. It does NOT retroactively make the earlier
`UNDECIDABLE` result wrong -- both are honest, correct conclusions from different evidence types.

Reshaped `UpperShell_HIGH`'s roof from the fixed anchor at the cavity's rear wall (x=-56.896, where
the already-verified rounded corner from the previous decision ends -- deliberately never touched)
through to the front-top corner (x=81.28), using 4 new loop cuts and a smooth sine-based bulge
(5mm magnitude, a flagged visual estimate of curvature *amount*, not a measurement -- same honesty
standard as the original 60% taper estimate) rather than a straight interpolation between the two
endpoints. Structurally clean (0 non-manifold, 0 degenerate; verified via `state_probe.mesh_health`)
and confirmed under real material rendering, not just the health check --
`curved_roofline_front.png`, `curved_roofline_iso.png`, and `curved_roofline_wireframe_front.png`
all show a clean continuous curve with no fragmented topology. Caught and fixed a real bug before
this landed: the first attempt at the bisect cuts filtered candidate geometry to faces where *every*
vertex was past the protected boundary, which wrongly excluded every face that legitimately spans
the boundary (the roof-land strips, the cavity side walls) and left the roof almost untouched (8
verts moved instead of the intended 20). Found by checking the actual `PERFORM_RESULT` counts against
what the topology should have produced, not by trusting a clean health check alone -- fixed by
requiring only *any* vertex past the boundary, re-verified clean on the corrected run.

**Honest status: the exact curve profile (its precise shape, whether it's symmetric, where it's
steepest) remains a visual estimate, not a measurement** -- that part of the original UNKNOWN finding
still applies and isn't overclaimed as resolved. What changed is the shape *class*: flat-plane-with-
crease is no longer the model's claim: continuously-curved is, on the strength of a real qualitative
read from the best available photo. If a genuinely orthographic or calibrated reference view ever
becomes available, the exact curve shape can be measured for real and this estimate corrected.

## Human review board

`review_board/review_board.html` -- a self-contained primary-form review package (both reference
photos, verified silhouette segmentation, front/side/3-4 model renders, shell MatCap and wireframe,
the full component/construction log, known uncertainties, and 8 structured review questions), same
format as the MasterLock 140D's. Explicitly notes what's *not* done here yet: no calibrated
silhouette IoU (both reference photos are oblique with no matching camera setup), modest-not-full
shoulder rounding, and an unintegrated cutter blade placeholder. No review recorded against it yet.
