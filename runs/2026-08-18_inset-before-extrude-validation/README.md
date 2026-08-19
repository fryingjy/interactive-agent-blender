# Validating inset-before-extrude end to end, and finding a real boundary

Second full run through `review -> reproduce -> transfer -> visually inspect -> technically
verify -> integrate with retrieval -> planner use -> runtime validation`, following the exact
pipeline established for `bevel.segments.parity_avoids_corner_triangle`
(`runs/2026-08-17_bevel-segment-parity-validation/`). Chosen because the live spout-growing
transfer test earlier this session already gave it real supporting evidence, and because it
directly tests the standing instruction to find the boundary of a tutorial claim rather than
promote it as stated.

## Source claim (CAPTURED, transcript-only)

From `runs/2026-08-17_video-study-mcglasham-insetting-softbodies/knowledge_items.json`: extruding
a face directly, "even on an already-subdivided flat plane," plants a five-spoked pole at the
extrusion's base -- "the area of maximum distortion" -- and forces mesh-wide tightening loops
instead of a local control loop.

## A confound caught and fixed before trusting any result

The first `curved_large` pass selected "the largest single side face" on a single-band open
cylinder -- which, with no intermediate loop cuts, meant selecting a face spanning the tube's
*entire* height. That is nothing like the live-validated spout-growth construction (a properly
proportioned mid-band cell) and produced a nonsensical result (a 173-degree "fold" in the inset
case) that would have been actively misleading if reported. Rebuilt the cylinder with 3 height
bands, matching the proven live construction exactly, before trusting any further number.

## Result: the claim did not hold where tested first, and did hold -- differently than expected -- where tested second

**Case 1 -- fine flat grid, small feature** (`flat_small_direct` vs `flat_small_inset`): a
6x6-subdivided flat panel, one interior face extruded 0.4 units. Direct and inset produced
near-identical results: same 4 five-valence poles, similar dihedral angles (27.9 vs 32.3 degrees),
and visually indistinguishable clean rounded bumps (`flat_small_direct_iso.png`,
`flat_small_inset_iso.png`). **The source's own "even on an already-subdivided plane" framing did
not reproduce here.**

**Case 2 -- curved body, coarser surrounding structure, larger feature**
(`curved_large_direct` vs `curved_large_inset`): a 16-segment, 3-band cylinder (matching the live
spout construction), the front mid-band face extruded 0.8 units. Here a real difference appeared,
confirmed visually: direct extrude produced an uneven, drooping bump whose deformation spread
unevenly into the surrounding wall (`curved_large_direct_iso.png`); inset-first produced a clean,
well-contained, deliberately-shaped feature (`curved_large_inset_iso.png`).

**The important correction, findable only by looking at the render, not the numbers:** raw max
dihedral angle was *higher* for the inset case (88.8 vs 53.6 degrees) -- which, read naively,
says inset is worse. It is not. The higher angle there comes from a tighter, better-contained
transition boundary; the lower angle in the direct case comes from the deformation drooping and
spreading with no local edge loop to contain it. Pole counts were identical between conditions in
both cases (4 and 5 five-plus-valence points respectively) -- pole count does not discriminate
this defect at all. **Containment, judged from a shaded render, is the real signal; angle
magnitude and pole count are not.** This is a direct, concrete instance of this project's own
standing rule that a technically-measured metric can point the wrong way and visual inspection is
not optional.

## The actual validated rule (conditional, not universal)

Inset-before-extrude's real mechanism is guaranteeing a local boundary loop around a new feature,
independent of whatever the surrounding topology already provides. On an already-fine surrounding
grid, an adequate implicit local loop already exists, so insetting first adds little. On a
relatively coarse surrounding surface -- the common real case for early hard-surface blockouts,
which is exactly when this technique gets reached for -- skipping the inset leaves no local
containment and the feature visibly droops. Surrounding mesh density is the deciding factor, not
a blanket "always inset."

## Retrieval and runtime integration

`knowledge/skills/inset-before-extrude-containment.json` written matching the established schema,
with a `planner_hint` included from the start (unlike the bevel-parity skill, which needed a
follow-up commit to add one). Retrieval confirmed working against the real consumer:
`StructuredSkillStore` ranks it first for a matching natural-language query (score 14.4) and
correctly abstains on an unrelated UV query.

`runs/2026-08-18_inset-containment-skill-runtime-use/` (`tools/run_inset_containment_skill_runtime_use.py`,
following the same headless pattern as the bevel-parity runtime-use script): a fresh coarse
3-band cylinder, a `local_feature_extrusion_on_coarse_surface` ticket at `SECONDARY_FORMS` stage --
retrieval ranked the skill first, the planner selected `inset_selection` with the ticket's own
parameters, and two typed decision transactions (inset, then extrude) committed cleanly. One real
implementation snag along the way: the coarse test body's intentionally open collar boundary
(matching the live spout construction) tripped the planner's non-manifold-defect gate until
declared via `intentional_non_manifold_edge_ids` -- fixed, not worked around.

## Status and honest limits

`RUNTIME_VALIDATED`. Same limits as the bevel-parity skill: not yet `PROMOTED` to default planner
behavior outside a matching ticket, and not yet exercised on an actual unfamiliar-reference
modeling task -- only synthetic fixtures so far, across two skills now.
