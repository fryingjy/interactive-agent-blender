# IKEA KUPONG alarm clock — primary cage, stage 0 (research + reference analysis)

## Why this prop, and why now

Moving on from the Scotch C38 (primary-form blockout complete, not yet human-reviewed) per direct
instruction to pick up another prop and apply lessons learned from a round of reference-analysis
research. Picked the IKEA KUPONG black alarm clock (906.218.11) because it's the last
curriculum-authorized target on record
(`knowledge/foundation/progressive_prop_benchmark_curriculum.json`, `active_prop_id: 5`) with a
fully verified reference package already in place.

**Flagging a real discrepancy rather than silently trusting the tracker**: that JSON's `updated`
field is `2026-08-16`, and its `active_prop_exercise_outcome` references
`runs/2026-08-16_ikea-dekad-model/` as an in-progress rejected exercise — that directory does not
exist in the current repo (only `runs/2026-08-16_reference-gathering-ikea-dekad/`, reference-only,
survives). Prop 1 (stapler), 3 (desk lamp), and 4 (kettle) show the same pattern: only
reference-gathering directories remain. This strongly matches the 2026-08-17 purge already
documented for the Scotch C38 -- the curriculum tracker's prose narrative about specific prior
attempts is stale, but its **authorization** (`modeling_authorized: true`) and the **reference
package itself** (`runs/2026-08-16_reference-gathering-ikea-kupong/`, fully passing all 8 audit
checks including `orthographic_coverage_pass`) are real, current, and verified. Proceeding on that
basis, not on the stale narrative.

## What was studied first (direct instruction: research reference/image-analysis technique, apply it)

Pulled transcripts (via TubeAlfred, since no Gemini-branded tool exists in this environment --
confirmed by checking both loaded tools and the MCP connector registry, and the user chose
TubeAlfred as the substitute) for three videos:

1. **"Orthographic Textures from Perspective Photos"** (Alex Cheparev) -- a real, named technique
   for rectifying a perspective photo into an approximately-orthographic texture: build a plane
   textured with the raw photo, manually cut edge loops along real-world straight/repeating
   features (window edges, floor lines), then iteratively adjust vertex positions using known
   real-world constraints (equal spacing, parallel lines) until the distortion resolves -- more
   loops added, more the warp straightens out. Directly relevant to this project's own recent
   failure (assuming orthographic projection on the Scotch C38's oblique roofline photo, formalized
   this session in `knowledge_engine/representation_hypothesis.py`): this is the actual
   *constructive* technique for cases where enough constraint features exist in the photo, as
   opposed to just refusing the test (`UNDECIDABLE`). Doesn't apply to the C38's smooth curved
   shell (no parallel/repeating constraint lines to anchor it), but is a real tool to reach for on
   props with more angular, repeating structure -- flagged for future use, not built as new
   infrastructure now (matches this project's standing rule against speculative infrastructure
   ahead of a proven need).

2. **"The Right Way to Use Reference when Sculpting"** (FlippedNormals / Henry Moreton) -- reference
   discipline for organic/character work, several points transfer directly to hard-surface product
   work: (a) use a *bounded, curated* set of reference images, not as many as possible -- too many
   contradictory sources produce a generic blend, not a faithful model; (b) work general to
   specific -- block major proportions/landmarks before any detail; (c) *actively analyze* reference
   rather than passively trace it -- directly validates this project's own standing rejection of
   literal pixel-tracing (the C38 roofline, the MasterLock negative space) as matching real
   professional practice, not just an ad hoc caution; (d) cross-reference the *same* feature across
   multiple images/lighting conditions before trusting a read of it; (e) use reference to
   self-critique work at every stage, not just at initial blocking -- matches this project's
   already-established "compare against reference after each decision" habit.

3. **"how i collect reference photos for Blender"** (Blender Bros) -- reference-network gathering
   (follow one good source, see who/what they reference, chain outward). More applicable to
   stylized/concept work than this project's real-product-accuracy goal, but the general principle
   (actively seek additional corroborating angles rather than settling for one photo) is sound and
   already reflected in this project's multi-source reference manifests.

## Reference analysis for KUPONG (applying the above directly, not just reading it)

Looked at all four rendered neutral views (`official_3d_reference/reference_{front,side,top,isometric}_beauty.png`,
from the already-locally-present, already-authorized `official_3d_reference.glb` -- rendered
views only, no source topology used as modeling guidance, per that package's own recorded
`use_boundary`) plus the real oblique product photos, before writing any construction plan --
directly applying the "analyze deeply across multiple views before blocking" lesson rather than
glancing at one image.

**Found a real ambiguity and resolved it with one more targeted render, not a guess.** The
isometric view's shading made it look like the object might be two separate parts -- a flat front
panel (carrying the U-shaped foot cutout and display recess) plus a distinct, thinner rear support
strut set behind it. That would have been a materially different construction plan (two joined
parts vs. one continuous shell) and was worth checking directly rather than assumed either way.
Rendered one additional rear-orthographic view from the same local GLB (`reference_rear_beauty.png`,
matching this package's existing front/side/top/isometric render pattern) -- research done "only to
resolve a concrete question," matching this project's global rules. The rear view shows the
**identical rounded-rectangle-with-U-cutout silhouette as the front** (just without the display
recess). Combined with the side view's smooth A-arch profile, this confirms the reference
package's own existing claim (`kupong_rear_support` in `reference_to_blockout_contract.json`):
**this is one continuous bent shell** -- like a strip bent into an arch -- not a front panel plus a
separate rear leg. My initial isometric-only read was wrong; checking it directly rather than
trusting first impression caught that before any geometry was built on the wrong assumption.

## Construction plan (not yet built -- next step)

One connected profile-cage, per the reference package's own `kupong_profile_cage_strategy`
hypothesis, refined by the above:

1. A flat U-shaped cross-section (rounded top corners, U-shaped cutout at the bottom leaving two
   feet) sized from `primary_cage_constraints.json`'s already-vetted fractional box constraints
   (`front_outer_envelope`, `underbody_opening`), which come from the genuinely orthographic
   `front_orthographic` source -- safe to use at this precision per this session's own
   projection-awareness discipline, unlike the C38's all-perspective set.
2. Swept/bent along the side-profile arch path (two legs flaring outward at the ground, curving
   smoothly up into a rounded top) using `depth_to_width` (0.5455, from `side_orthographic`) for
   the overall proportion. The exact curve shape of the arch (how sharply it rounds vs. how
   straight the legs run) is a flagged visual estimate from the side view, not a precise
   measurement -- same honesty standard as every prior taper/curve estimate this project has made.
3. Display recess (shallow inset, front-facing surface only) added after the primary shell passes
   its own review, per the contract's own staging (`construction_intent.surface_plan`: no SubD,
   crease, or bevel until the shell passes front/side/isometric primary-cage review).

## Stage 0: literal box blockout (decision_revision 0)

Started construction. `Shell_HIGH`, one literal box primitive at the official envelope
(69.85 x 38.1 x 57.15 mm -- 2.75 x 1.5 x 2.25 in, `ikea_kupong_official_product_photo`'s
dimensional anchors, not estimated) -- same staging discipline already proven on the Scotch C38
("begin with literal box profiles, do not round/carve/bend before the envelope itself is verified").
Caught a real bug before it propagated: `bpy.ops.mesh.primitive_cube_add(size=1.0)` creates an edge
length of 1.0 (spanning -0.5 to +0.5), not a radius of 1.0 -- scaling by half the target dimension
produced a box exactly half the intended size on the first attempt (34.925 x 19.05 x 28.575 mm).
Caught immediately by checking `obj.dimensions` against the intended numbers rather than assuming
the scale math was right, fixed by scaling by the full dimension instead of half of it. Verified
correct on the second run and rendered front/side to confirm (`box_front.png`, `box_side.png`).

## Reconsidering the sweep topology before building it (documented, not yet executed)

Worked through several competing hypotheses for how the front-facing U-shaped-cutout-with-two-feet
profile relates to the side view's continuous arch, rather than start cutting bmesh geometry against
a guess:

- A swept small tube/blob cross-section bent along the arch path -- rejected: this would produce
  a ring/donut-like silhouette when viewed from directly front or rear, not the solid
  rounded-rectangle-with-U-cutout actually seen in both the front and rear renders.
- The U-shaped-with-feet profile (matching the front-view silhouette) extruded straight through
  depth, with the *entire* extrusion then bent along the arch path (cross-section constant in the
  profile's own local frame, rotating to stay perpendicular to the path) -- this is consistent with
  the identical front/rear silhouettes (both ends of the bend show the same local cross-section) and
  with the top view showing no obvious gap (the notch, local to each cross-section, rotates out of
  a straight-down view once the path curves over the top).

Going with the second hypothesis as the construction target, but treating it as a hypothesis to
verify against renders once built, not a settled fact -- consistent with this project's own
"build, render, compare, correct" discipline rather than resolving ambiguous 3D topology by
reasoning alone.

## Stage 1: front-profile prism (decision_revision 0 -> 1, `BUILD_FRONT_PROFILE_PRISM`)

Replaced the box with the actual front-view boundary -- rounded-rectangle envelope with a
rectangular notch cut into the bottom-middle, leaving two feet -- built as one closed 8-vertex
loop (`edgenet_fill` for the cap, matching the chamfer technique already validated on the
MasterLock/C38), then extruded straight through the full depth (38.1 mm). Sharp corners, no
rounding yet -- that's a later, separate decision, same staging as the Scotch C38's front-corner
chamfer coming after its box blockout, not bundled into this one. Notch position/width read
directly from `primary_cage_constraints.json`'s `underbody_opening` fractions (already vetted
against the genuinely orthographic `front_orthographic` source), not re-estimated.

Structurally clean (0 non-manifold, 0 degenerate; 16 vertices, 10 faces, 2 ngons -- the front and
rear cap faces, expected from `edgenet_fill` on an 8-sided notched boundary). Rendered and confirmed
against the reference target (`prism_iso.png`, `prism_front.png`): the silhouette now matches the
front/rear reference renders' rounded-rect-with-U-notch outline directly, not just by construction
intent -- this is prism A of the two-hypothesis reasoning above, correctly built as a straight
extrusion with no bend yet.

Caught the same object-identity risk this project has hit before with a different symptom: my
first draft deleted the existing object and created a brand-new one with the same name, which
would have silently bypassed the persistent-ID layer setup (`persistent_ids.ensure_layers`) that
`_bm_from_object`/`_write_back` rely on. Caught before running by re-reading `mesh_ops.py`'s actual
implementation rather than assuming delete-and-recreate was safe; fixed by clearing the existing
object's geometry in place (`bmesh.ops.delete`) and rebuilding inside the same bmesh/object instead.

## Stage 2, not yet started: carve the side-view arch into the prism

`Shell_HIGH` currently reads correctly from front and rear but is still a straight rectangular
block from the side (no taper/arch at all). Next: carve the side-view A-arch silhouette into this
prism's currently-flat top/side edges -- via a series of bisect cuts approximating the arch curve
(the same faceted-curve technique already used for the rear shoulder rounding on the Scotch C38),
removing material outside the arch envelope while leaving the front/rear notch profile untouched.
`depth_to_width` (0.5455, from the genuinely orthographic `side_orthographic` source) sets the
overall proportion; the exact curve shape is a flagged visual estimate from the side-view render,
same honesty standard as every other unmeasured curve this project has built.

## Stage 2 actually built (decision_revision 1 -> 2 -> 3 -> 4), then found to be the wrong shape

Built the taper as a solid-block narrowing: bisected above the notch and tapered the outer Y-extent
inward toward the peak (`TAPER_ARCH_ABOVE_NOTCH`), then did the same within the two individual feet
below the notch (`TAPER_LEGS_BELOW_NOTCH`). Rendering after the first pass showed exactly the
scope limit already flagged before building it (no leg separation, since the leg region was
untouched) -- expected, not a surprise. Rendering after the second pass showed a real, unflagged
defect instead: a visible flare/kink right at the seam between the two passes, because the leg
taper's own end value (0.68 keep-fraction) didn't match the upper taper's start value (1.0,
untouched) at the shared boundary. Fixed with a third corrective decision
(`FIX_TAPER_SEAM_DISCONTINUITY`) replacing both passes' Y-extent values with one continuous
function of height -- confirmed smooth under render, no more seam.

**But that render then exposed a much bigger problem than the seam.** With the seam fixed, the side
silhouette reads as one smooth, solid, cone-like taper (`fixed_side.png`) -- and comparing it
directly against the reference's actual side view shows this is the wrong *class* of shape
entirely, not just imprecise. The reference's two "legs" aren't the outer edges of a solid block
narrowing inward -- there's real, visible background/daylight showing *through* the object between
the front leg and rear leg in the lower-middle height range, exactly like a real physical A-frame
stand or easel. That directly confirms what the isometric reference render showed early in this
run's research (a distinctly thin rear leg with a visible gap behind a thicker front panel) --
which I had provisionally reconciled as "one continuous shell, just thickness-tapered," but the
side-view comparison now shows that reconciliation was wrong. The object is genuinely **hollow
through the middle in Y** (front wall and rear wall, open space between them at mid-height), not a
solid mass that merely narrows in cross-section.

**Everything built so far in stage 2 is the wrong construction and needs real correction, not
polish.** Recorded honestly rather than left implied by silence: the current `Shell_HIGH` is a
solid tapered block, structurally clean and internally consistent, but visually wrong against the
reference in a way overlaying the seam-fix render exposed clearly. Not reverting it yet -- it's a
legitimate, useful intermediate state (correct front/rear silhouette, correct overall envelope) to
carve the hollow into, not throwaway work. Next real step: cut through the middle-Y material in the
upper/leg height range (leaving the front and rear walls standing, open between them), using the
same bisect-isolate-then-extrude/delete technique already validated on the MasterLock sockets and
the C38 cavity -- not yet attempted this run.
