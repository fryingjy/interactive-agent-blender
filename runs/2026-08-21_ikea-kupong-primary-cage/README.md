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

Not yet started. This is real, substantive reference-analysis work worth its own record before the
construction pass -- matching this project's established practice of not cramming a nontrivial new
bmesh construction into the same turn as the research that informs it.
