# Swingline 747 Classic stapler — primary cage, stage 0 (reference analysis)

## Why this prop

Moving on from the IKEA KUPONG alarm clock per direct instruction (that build is left mid-construction
with an honestly-recorded, real defect: the arch taper is a solid block where the reference shows a
genuinely hollow structure -- see `runs/2026-08-21_ikea-kupong-primary-cage/README.md`). Picked the
Swingline 747 Classic stapler: Tier-1 item 1 on `docs/PROGRESSIVE_PROP_BENCHMARK_CURRICULUM.md`, the
one Tier-1 prop not yet attempted this session, with a fully verified reference package
(`runs/2026-08-16_reference-gathering-swingline-747/`, `disposition: READY_TO_MODEL`, 7 references,
4 independent sources, re-checked and still passing).

**Flagging the same standing gate this project already addressed once this session**: that prop's own
`reference_plan.md` says "Human visual review of the multi-view board is still required before a
Blender blockout is authorized." The KUPONG build already established the operative precedent for
this session: direct user instruction to proceed authorizes starting a blockout without a prior
approval-board pass -- it does not remove the requirement for reference fidelity or the authority of
a later human rejection. Proceeding on that same basis here, not silently, and not by pretending the
note doesn't exist.

## Applying what this session has actually learned, not just naming it

- **No orthographic source exists for this prop** (`reference_manifest.json`: every item is
  `PERSPECTIVE` or `UNKNOWN`, no `ORTHOGRAPHIC`) -- unlike the KUPONG, which had a real orthographic
  render set. This means every curve/proportion decision here is a flagged visual estimate by
  necessity, never a precise pixel measurement -- the projection-aware discipline built earlier this
  session (`knowledge_engine/representation_hypothesis.py`) would return `UNDECIDABLE` for any
  boundary-linearity claim against any of these sources, and that's the correct call, not a gap to
  work around.
- **Looked at the actual images before writing any construction plan**, not just the manifest's
  metadata -- `74718_product_elevation.jpeg` (clean 3/4 view, red), `747_open_mechanism.jpg` (fully
  open, reveals real internal construction), and two `geometry_sibling` product shots in black and
  blue (cross-referencing the same molded-plastic geometry across color variants, corroborating that
  the shape itself is stable across SKUs, only the shell color/finish changes).
- **The open-mechanism photo changes the construction model in a load-bearing way, the same kind of
  correction the KUPONG's isometric/side comparison forced.** This is not a continuous bent or tapered
  shell at all (unlike the KUPONG). It's a real hinged two-part mechanical assembly: a low base
  housing (with the staple-forming anvil at the front) and a separate top lever/cover, joined by a
  rear pivot, with a spring-loaded staple magazine/channel visible inside the lever through the open
  cutaway. This matches this prop's own `reference_plan.md`, written before this session, which
  already called for two separate cages (`TopLeverShell_HIGH`, `BaseShell_HIGH`) rather than one
  continuous shell -- confirmed against the actual photo rather than taken on faith, the same
  verification discipline that caught the KUPONG's wrong "continuous shell" assumption.

## Construction plan

Following this prop's own pre-written `reference_plan.md` (still sound, cross-checked against the
photos above), staged the same way every prop this session has been staged -- literal box cages
first, verified against reference, before any rounding/detail:

1. `BaseShell_HIGH`: low box cage, official envelope's footprint (190.5 x 63.5 mm, 7.5 x 2.5 in),
   height a flagged visual estimate (the closed-assembly height of 43.18 mm / 1.7 in includes both
   base and lever -- no source gives the base/lever split directly, same class of estimate as the
   Scotch C38's base/shell height split).
2. `TopLeverShell_HIGH`: separate box cage for the lever, hinged at the rear, sized from the same
   visual proportioning.
3. Anvil recess in the base front, staple-channel negative space in the lever -- both via the
   bisect-isolate-then-extrude technique already validated on the MasterLock sockets, the C38 cavity,
   and the KUPONG notch (no boolean).
4. Render and compare against the reference after every single decision, not just at milestones --
   the KUPONG run's clearest lesson: a clean structural health check proves nothing about whether the
   shape is actually right.

## Stage 0: box blockout (both parts)

`BaseShell_HIGH`: 190.5 x 63.5 x 14.249 mm -- length/width exact from the official envelope, height
a flagged visual estimate (33% of the closed-assembly total, no source gives the base/lever split
directly). `TopLeverShell_HIGH`: separate object, 177.165 x 54.61 x 28.931 mm, rear-hinged (its rear
edge aligned with the base's rear edge, its front nose set back from the base's front edge, matching
`74718_product_elevation.jpeg`'s visible base-lip-past-lever-nose relationship) -- length/width
fractions (0.93, 0.86) also flagged visual estimates.

Rendered the assembled pair (`assembly_box_iso.png`) and confirmed the gross proportions read
correctly against the reference before doing any further shaping: low base, taller lever set back
from the front edge, right general mass distribution. Both objects still literal boxes -- no anvil
recess, no hinge cut, no crown/nose shaping yet. That's the next real construction step, deliberately
not started in the same pass as verifying the envelope, per this project's own staging discipline.
