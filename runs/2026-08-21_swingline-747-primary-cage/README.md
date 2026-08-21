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

## Stage 1: anvil/staple-channel recess (decision_revision 0 -> 1, `CUT_ANVIL_RECESS`)

Cut the recessed channel into `BaseShell_HIGH`'s top surface -- 4 vertical bisects isolating the
rectangular region (candidate geometry re-collected fresh before each cut, avoiding the shared-edge
fragmentation bug class already hit twice on this project), then lowering the isolated top verts
by 2.5 mm. Position/size are flagged visual estimates from `74718_product_elevation.jpeg` and
`747_open_mechanism.jpg` (12%-88% of the base's length from the rear, centered, 40% of the width) --
no orthographic source exists for this prop, so no more precision than that is claimed.

Structurally clean (0 non-manifold, 0 degenerate). Verified visually, not just via the health check --
matching this session's clearest lesson from the KUPONG run. The first render (assembled, iso) mostly
hid the recess behind the taller lever object, so rendered the base in isolation (`base_only_iso.png`,
lever hidden) specifically to see it clearly, rather than accepting an inconclusive check. It reads
correctly: a clean, visible shallow channel running the base's length, matching reference intent.

Not yet built: the lever's front nose taper, and the separate `AnvilPlate`, `MagazineRail`,
`HingePin`, `Latch`, `Spring`, `RubberBasePad` components this prop's `reference_plan.md` calls for
once the primary cages are correct.

## Stage 3: lever crown, a second real bug chain (found before committing this time)

Rounded `TopLeverShell_HIGH`'s top cross-section into the domed "crown" every reference photo shows
(currently a flat-topped box). First attempt committed clean (0 non-manifold/degenerate) but a direct
vertex dump -- done proactively this time, per the coordinate-space lesson two sections up -- showed
the Z values weren't monotonic toward center at all, and didn't match any of the intended per-step
targets past the first cut. Rejected the commit's premise rather than trust the clean health check;
reverted the blend file to the last git-committed state (this attempt had not yet been git-committed)
and diagnosed with a step-by-step script instead of debugging blind.

**Root cause, found by tracing one bisect at a time**: moving a shared boundary vertex after the
first cut leaves the "inner" region no longer flat -- it's linearly interpolated between the two
symmetric drop points already made. Every later step's matching condition (`z ≈ original flat top`)
therefore never matched anything again, so those steps silently moved zero vertices while still
reporting a clean commit. Fixed by moving whatever vertex each bisect actually creates at its own Y
position, not requiring it to match the untouched original height.

**A second, purely conceptual bug surfaced once the mechanics were fixed**: the drop-fraction
direction was backwards -- built so the *center* dropped the most and the *edges* stayed near full
height, the opposite of an actual crown (tallest at center, rounding down toward the sides). Also
extended the same "true edge" fix already needed once on the hinge throat: the taper originally
stopped short of the box's real edge vertices, which would have left a flush sliver at the sides
identical in kind to the earlier front-tip sliver -- closed by moving the true edge vertices to the
deepest drop directly, not just the interior cut points.

Final state verified two ways again: a direct vertex dump (symmetric, monotonically decreasing from
13.66 at the center ridge to 6.36 at the true edges) and an isolated render (`lever_crown_iso.png`)
that reads as a genuine rounded dome cross-section, not a flat box or an inverted dip. Structurally
clean, decision_revision 5 -> 6.

**Compounding pattern worth naming explicitly**: this is the second construction in this same run
where the first attempt committed clean and only a deliberate, skeptical direct inspection (not
trusting the health check or a render glance) caught that the actual geometry didn't match intent.
Adopting direct vertex verification as the default check for every multi-step taper/bisect
construction on this project going forward, not an occasional extra step reserved for when something
already looks suspicious.

## Stage 2: a real coordinate-space bug, found by direct inspection, not by trusting a render

Attempted the hinge throat next (`OPEN_HINGE_THROAT`, tapering the lever's underside up from the
rear hinge toward the front, per `reference_plan.md`'s flag that the cover/base throat "is a
critical negative space [that] must survive every blockout"). It committed clean and the render
looked plausible at a glance -- but two views (`throat_side.png`, an end-on view that can't show a
taper varying along that same axis at all, and `throat_iso.png`, where the gap was too subtle to
read confidently) weren't good enough evidence, so a proper front elevation was rendered next.

That still didn't resolve it cleanly, so the actual vertex data was inspected directly rather than
keep reasoning from renders -- and that's what found the real bug: `mesh_ops._bm_from_object` reads
`bpy.data.objects[name].data` directly, which Blender always stores in **local** (object-space)
coordinates, but both `CUT_ANVIL_RECESS` and `OPEN_HINGE_THROAT` computed their target positions in
**world** space and applied them directly to local vertex coordinates. Concretely:

- `BaseShell_HIGH`'s "recess" was actually a 4.6mm **bump** above the top surface (world Z 18.87 vs.
  the true top at 14.25), not a 2.5mm recess below it. The earlier isolated render
  (`base_only_iso.png`, described at the time as "a clean visible channel") was real geometry, but
  its shading direction was misread -- a raised strip and a recessed groove can look close to
  identical under flat matcap-style lighting without a raking light or a numeric check. Re-rendering
  the corrected version afterward (still `base_only_iso.png`) looks **visually almost identical** to
  the wrong version -- confirming this render style genuinely cannot reliably disambiguate the two on
  its own. Worth remembering for future stages: a shallow depth feature needs either raking light,
  a wireframe/cross-section check, or direct vertex inspection, not just a solid-shaded glance.
- `TopLeverShell_HIGH`'s hinge taper never applied at all in the first attempt -- the world-space Z
  target never matched any local vertex Z, so the intended "move" step silently selected nothing.
  `PERFORM_RESULT` and the health check both looked clean because the topology from the X-bisects
  was still valid; only a direct vertex dump caught that the Z edit was a no-op.

**Two more layers surfaced while fixing this, each caught the same way -- by inspecting actual
vertex positions rather than trusting the previous fix's clean commit:**

1. A first fix attempt (`FIX_COORDINATE_SPACE_BUG`) converted world targets to local by subtracting
   the object's own origin offset -- correct in principle, but it needed to match vertices the
   *original bug* had already placed at the raw world-intended numbers (since that bug treated world
   values as local directly), not at a freshly-recomputed "correct" local position. It ended up
   moving the box's own unrelated front-corner vertex instead of the intended cut points.
2. A second fix (`FIX_LEVER_THROAT_PRECISELY`) matched the verified existing positions directly and
   got the five real taper cuts right (confirmed: `reverted: 2, moved: 10`, matching the two stray
   verts undone and five cuts times two sides) -- but left one small sliver: the *original* buggy
   script's last cut had landed 6.66mm short of the lever's true front edge (the same
   world-used-as-local error, applied to the box's own boundary this time), leaving a thin ungapped
   nub right at the tip instead of a smooth taper to the edge. Closed with one more targeted fix
   (`CLOSE_FRONT_SLIVER`).

Final state verified two ways, not one: a direct world-space vertex dump (base recess floor at world
Z 11.75, correctly below the 14.25 top; lever underside progressing smoothly from Z 14.25 at the
rear hinge up to Z 22.24 near the front, all the way to the true edge) and a front-elevation render
(`fixed_front.png`) that now shows the intended wedge clearly: flush at the rear, opening into a
real visible gap toward the front, matching what `747_open_mechanism.jpg` and the closed-state
photos both show. Five decisions total for this bug (`OPEN_HINGE_THROAT` through `CLOSE_FRONT_SLIVER`),
decision_revision 1 -> 5, all individually committed and health-checked, none silently squashed.

**The generalizable lesson, worth carrying into every future construction script on this project**:
`mesh_ops._bm_from_object`/`_write_back` operate in the object's local space. Any script that creates
an object with a non-zero `location` (as every script in this run has, to place parts at their real
world positions) must either convert world-intended targets to local before touching `v.co`, or
avoid the ambiguity entirely by baking location into the mesh at creation time. Every prior
prop this session (MasterLock, C38, KUPONG) happened not to hit this because their target-writing
code either worked at an object origin of `(0,0,0)` or derived its targets by reading the mesh's own
current values back out (as the KUPONG taper fixes did) rather than computing a fresh world-space
number -- this bug was waiting to happen the first time a script mixed both patterns, and it did.
