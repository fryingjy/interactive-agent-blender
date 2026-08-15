# Level 14 synthesis: cross-referencing the 16(20)-run batch against the 9-stage reasoning chain

## Task and method

`docs/BLENDER_MODELING_CURRICULUM_V2.md`, Level 14 ("Professional modeling judgment"), lists a
9-stage reasoning chain a professional artist runs through on a real build:

```
reference interpretation -> blockout decision -> representation choice -> topology decision
-> modifier decision -> detail decision -> surface/shading decision -> mistake -> correction
```

and flags that the videos processed under the extended-curriculum push (named there in shorthand
as `blenderbros-subd-hardsurface(-2)`, `blenderbros-subd-hive-controller`,
`blenderbros-tertiary-details`, `blenderbros-decals-workflow`, `blenderbros-curvy-organic`,
`blenderbros-5-best-tricks`, `cgcookie-hardsurface-intro`, `cgvoice-amateur-mistakes`,
`crnt-boolean-triangle`, `elementza-clean-topology`, `grant-abbitt-beginners`,
`gnomon-bryant-momo-koshu`, `jl-mussi` / `jl-mussi-5-tips` / `jl-mussi-easy-once-you-learn`,
`mcglasham-subd`, `pzthree-retopology`, `rileyb3d-advanced-hardsurface`, `subd-3dprint`) had never
actually been cross-referenced against this specific 9-stage framework -- "processed" had been
silently treated as "fully extracted for this level's goal." This document is that dedicated
synthesis pass: no new videos were watched, no new extraction was performed. Every item below was
already sitting in an existing `knowledge_items.json`.

**Directory-name check.** All 20 directories the curriculum doc's shorthand list resolves to exist
exactly under `runs/2026-08-14_video-study-*/`, including both `blenderbros-subd-hardsurface` and
`blenderbros-subd-hardsurface-2` as separate directories, and all three `jl-mussi*` variants. No
listed name failed to resolve.

**A note on scope vs. the assigned reading list.** The task instructions asked to read each run's
`knowledge_items.json` **and** `brief.md`. None of these 20 directories contain a `brief.md` --
each one instead holds `knowledge_items.json` plus a raw-source file (`transcript_full_text.txt`,
`gemini_analysis.txt`, or `transcript_raw.json`/`transcript_consolidated.txt`). `brief.md` appears
not to be a file this pipeline generation produced for any of these runs. All 20
`knowledge_items.json` files were read in full; the raw transcripts were not re-read, since the
knowledge items already carry direct quotes/timestamps and are the intended unit of extracted
knowledge. This is flagged here rather than silently substituted.

**Volume reviewed (corrected by independent corpus audit):** 90 knowledge items across the 20 runs
(all `PRINCIPLE` / `PROCEDURE` /
`DECISION` / `FAILURE` / `VISUAL_CUE` types combined). Counts per run: subd-hardsurface 6,
subd-hardsurface-2 4, subd-hive-controller 6, tertiary-details 5, decals-workflow 3, curvy-organic
7, 5-best-tricks 5, cgcookie-hardsurface-intro 1, cgvoice-amateur-mistakes 5,
crnt-boolean-triangle 2, elementza-clean-topology 4, grant-abbitt-beginners 1,
gnomon-bryant-momo-koshu 6, jl-mussi 5, jl-mussi-5-tips 5, jl-mussi-easy-once-you-learn 6,
mcglasham-subd 5, pzthree-retopology 5, rileyb3d-advanced-hardsurface 6, subd-3dprint 3.

The original synthesis text said 87 because those three runs were each understated by one item.
`runs/2026-08-15_level14-synthesis-audit/level14_synthesis_audit.json` independently hashes and
loads all 20 authoritative files, checks all 90 items' minimum schema/source ranges, and records the
effect of each reconciled item. Two had already been discussed below despite the count typo; the
third adds a real representation-choice decision and is now included explicitly.

Below, each of the 9 stages gets its own section listing the items that are genuine evidence for
*that specific stage* (an item is cited under more than one stage where it truly earns it -- e.g.
an item that is simultaneously a mistake and its own correction, or a reference-driven topology
call). The closing section gives the honest strong/thin/missing verdict and names what kind of new
source would actually fill the gaps.

---

## 1. Reference interpretation

**This is the thinnest stage in the entire batch -- close to absent.** Almost none of these 20
videos keep a reference photograph on screen while narrating how an ambiguous visual cue in it was
read into a specific geometric decision. That is expected: these runs are technique/topology
breakdowns, not the reference-driven build studies the curriculum's separate Level 5 track is
supposed to cover. Only one item genuinely closes the loop from "what the reference shows" to "what
I built":

- **elementza-clean-topology** (`AOW1tBl9VLk`): "The specular highlight expected on the final
  shaded surface (from the reference, or from the intended form) is the deciding factor for where
  topology edges should be placed -- identify where the highlight needs to run first... before
  adding any further support topology." This is the one item in the batch where a *reference-derived
  expectation* (where should the shine fall) is stated as the input that drives a downstream
  decision (where the edges go), rather than a rule about mesh mechanics in isolation.

Two more items touch reference use but stop short of interpreting a specific photo into a specific
decision -- included here for completeness, not as strong evidence:

- **jl-mussi** (`tRZh0K8R8mQ`): prefers studying a physical copy of the reference object over
  photos alone, since handling it and watching light play across it "reveals shape information
  static images do not" -- a principle about *which kind of reference source* to use, not an
  applied interpretation of one.
- **cgvoice-amateur-mistakes** (`8HTlZIcqFR0`): snaps a human T-pose reference mesh beside the prop
  in orthographic view to check whether handles/reach points feel human-scaled -- reference used as
  a *validation check* on an already-made design, not as the source of the design decision itself.

## 2. Blockout decision

Present but narrower than it looks -- most of these are really "sequencing" rules (what order to
work in) rather than the proportion-judgment call ("is the blockout right yet, how do I know") that
"blockout decision" is meant to capture.

- **rileyb3d-advanced-hardsurface** (`jbx5xz0uj7s`): blocks out the overall primary form with a
  Lattice cage (scaled to the bounding box, moved as a low-resolution proxy) rather than moving
  individual mesh vertices, specifically to shape the whole silhouette in one pass before detailing.
- **blenderbros-tertiary-details** (`3wJ81Ua7o_w`): deliberately traces a freehand organic
  silhouette at a very low vertex/segment count first and confirms proportions and quad
  connectivity at that resolution before adding any support loops -- reconciling two independently
  high-res-traced sections later is harder than simplifying both down first.
- **elementza-clean-topology** (`AOW1tBl9VLk`): at the very start of a build, before any
  subdivision, deliberately searches for the largest possible quads that are still even in size with
  each other -- these become the shape-defining polygons everything else is built from, and
  unevenness at this stage compounds through every later subdivision.
- **blenderbros-subd-hardsurface** (`xUEs7cszlb0`): a DECISION-level call to default beginners to a
  Boolean+n-gon blockout workflow over SubD, citing the creator's own build-time comparison (~9
  minutes vs. ~40 minutes for the same model) and the added cognitive load of thinking topology-flow
  while blocking out.
- **mcglasham-subd** (`HfTdQNECvtU`): works outside-in during blockout -- handle every cut that
  touches a corner or an outer edge first, and only then start cutting holes in the middle of a
  face (which still get their own inset boundary before cutting).

## 3. Representation choice

More evidence than the curriculum doc's own hint suggested it might have, though most of it is
implicit -- a technique video stating "this trick is better because of property X," retroactively
readable as a mesh-vs-curve-vs-modifier-vs-shader tradeoff, rather than an artist narrating a live
decision between named alternatives for a specific part. One item genuinely does the latter:

- **mcglasham-subd** (`HfTdQNECvtU`) is the strongest single item in this stage across the whole
  batch: an explicit DECISION to reject Boolean-modifier-driven geometry as the underlying
  representation for a hard-surface cut and rebuild it as native quad topology instead, with named
  reasoning -- "boolean cuts... give you severely limited geometry and are virtually useless in
  animation, texturing, deformation, transparency" and don't transfer reliably to other software or
  subsurface scattering. This is close to a textbook "why mesh over modifier-driven" moment.
- **jl-mussi-5-tips** (`PHpxiQaH27o`), "Screw that cylinder": chooses a flat half-profile edge strip
  driving a Screw modifier (a live, parametric/curve-adjacent representation) over a standard
  Cylinder mesh primitive, explicitly because a baked-in primitive's segment count can't be changed
  non-destructively once other modifiers (e.g. Boolean) are stacked on top.
- **blenderbros-curvy-organic** (`3_RkY_mtlC4`): chooses a Bevel *shader* node (Input > Bevel into
  the Normal socket) over a physical Bevel modifier for concept/render-only work on dense curved
  boolean intersections, reasoning that physical bevels "frequently cause shading errors and
  geometry collisions" there -- but flags this only works when real-geometry export isn't required.
  A genuine shading-representation-vs-actual-geometry tradeoff, explicitly scoped.
- **gnomon-bryant-momo-koshu** (`xS2Bv7-cDe8`), panel seam: builds the seam as a single open 1D
  edge path driving Screw(angle 0) + Solidify rather than modeling a cutter mesh directly, so the
  seam stays redesignable by moving a couple of path vertices instead of re-cutting topology.
- **gnomon-bryant-momo-koshu** (`xS2Bv7-cDe8`), braided cable sleeve: builds the sleeve as a
  Poke+Triangulate-to-Quads+Wireframe lattice mesh attached to a curve via Cablerator, so the curve
  drives deformation along the cable path rather than the sleeve being hand-modeled along it.
- **pzthree-retopology** (`FgfMVkkSNfQ`): chooses a Multires modifier over a plain Subdivision
  Surface modifier specifically so fine sculpted detail can sit on top of a still-editable low-poly
  cage, instead of sculpting directly on a raw voxel-remeshed mesh with no clean underlying topology
  -- a real mesh-plus-multires-vs-sculpt representation call, though narrower than a full
  sculpt-vs-hard-surface-mesh decision.
- **jl-mussi-easy-once-you-learn** (`cbXWWE8-X0M`): explicitly rejects carving complex panel gaps
  directly into one continuous curved shell because that spreads density and pinching through the
  parent surface; separates the panel and gives that part its own Solidify-above-SubD stack instead.
  This is a direct continuous-vs-separate construction decision and was missing from the original
  representation-choice list.

## 4. Topology decision

**The single most densely evidenced stage in the batch**, alongside mistake/correction. A
representative (not exhaustive) selection:

- **blenderbros-subd-hardsurface** (`xUEs7cszlb0`): keep region edge/corner counts as multiples of
  four for clean quad reconnection; keep quads/n-gons roughly even in size specifically on curved
  surfaces (flat surfaces tolerate large n-gons fine); route support loops parallel to/around a
  feature rather than letting them diverge across a corner; avoid "diamond" terminating quads (three
  sharp corners, one wide) and abrupt small-to-large polygon jumps.
- **elementza-clean-topology** (`AOW1tBl9VLk`): establish the largest even quads first (also cited
  under blockout); manually re-balancing one locally imbalanced area just relocates the imbalance to
  its neighbor rather than resolving it -- the actual fix is re-examining the initial blockout, not
  more local nudging; topology redirection (knife-cut/merge) should be reserved for closing down and
  fine-tuning a shape once its primary form is set, "rarely, extremely rarely" the right tool for
  defining primary form.
- **jl-mussi-easy-once-you-learn** (`cbXWWE8-X0M`): support loops running *parallel* to a curved
  surface's own curvature visibly pinch the specular highlight, while loops running *perpendicular*
  to it (following the curve's profile) don't; a "diamond/pole corner reroute" technique (dissolve +
  diagonal knife cut + dissolve) redirects a pinching loop from curvature-parallel to
  curvature-perpendicular at a corner; a deliberate 3-way/5-way pole ("topology stopper") near a
  detail stops a later loop cut from wrapping the whole circumference; applying a level-1
  Subdivision Surface modifier auto-converts an irregular knife-cut mix of triangles/n-gons into
  pure quads.
- **rileyb3d-advanced-hardsurface** (`jbx5xz0uj7s`): "topology redirect" via Knife + Ctrl+X dissolve
  to continue existing quad edge-flow across a boolean-cut boundary, described as an essential but
  slow-to-develop skill; the real acceptance test for a redirect (or for tolerating a resulting
  n-gon) is whether the *subdivided* result looks clean, not whether the raw cage has zero n-gons.
- **mcglasham-subd** (`HfTdQNECvtU`): rebuilds a boolean-style cut as inset + delete + F-fill +
  control loop, all-quads; works outside-in (also cited under blockout); after adding a support loop,
  press R then F repeatedly until it straightens, as a general check for predictable SubD curvature.
- **jl-mussi** (`tRZh0K8R8mQ`): keep cylindrical/radial segment counts divisible by four for even
  symmetry lines across all three axes.

## 5. Modifier decision

**Also densely evidenced.** Selection:

- **jl-mussi-5-tips** (`PHpxiQaH27o`): Screw modifier as a live-adjustable cylinder generator (cited
  above); Array modifier driven by an Empty's rotation for N-fold radial symmetry (with the
  order-of-operations gotcha that transforms must be applied first or the array output is garbled);
  Ctrl+L "Copy Modifiers" plus right-click "Copy/Paste Driver" to propagate modifier-parameter edits
  (e.g. Solidify thickness) across Alt+D linked duplicates, since linked duplication alone only
  shares mesh-edit data, not modifier settings.
- **rileyb3d-advanced-hardsurface** (`jbx5xz0uj7s`): Lattice modifier for blockout (cited above),
  including bumping its Strength above 1.0 if the mesh visibly lags the cage; Shrinkwrap-to-a-saved
  pre-cut reference-object copy to reconform a silhouette dented by a later detail cut.
- **pzthree-retopology** (`FgfMVkkSNfQ`): Multires vs. plain SubD for sculpt detail (cited above);
  weighted-bevel setup (tag edges with Bevel Weight 1, Bevel modifier limit method "Weight", Outer
  Miter "Arc" not the default); multiple gentle-ratio Decimate passes (~0.4-0.5 each) instead of one
  aggressive pass, which was found to break the mesh apart worse.
- **gnomon-bryant-momo-koshu** (`xS2Bv7-cDe8`): Shrinkwrap (position) + Data Transfer (custom
  normals, "Nearest Face Interpolated") stacked together to attach a floating hardware piece with
  matching shading, since Shrinkwrap alone leaves a dark seam; Screw(angle 0)+Solidify for a
  procedural panel-seam cutter (cited above); Bevel modifier placed *above* Solidify in a cutter's
  stack specifically to get rounded interior corners in the final boolean cut.
- **blenderbros-subd-hardsurface-2** (`X1IgEb5dyKc`): switching a Bevel's corner/miter setting to
  "Arc" to fix pinched shading at convex corners; "Surface Slide" bevel option to make bevel geometry
  follow curvature instead of projecting flat.
- **blenderbros-curvy-organic** (`3_RkY_mtlC4`): dissolving redundant intermediate bevel loops
  before re-subdividing, since multi-segment bevels multiply again under a level-3/4 SubD and bloat
  density; MESHmachine's Offset Cut to clear buffer clearance before beveling a dense boolean seam.
- **subd-3dprint** (`SpYVIKsb294`): Edge Crease (Shift+E) before applying SubD to hold sharp/flat
  regions without separate bevel geometry; "On Cage" edit-mode display toggle to preview where edits
  will land on the subdivided result; explicit DECISION of SubD level 4 over level 5 for a 3D-print
  target, trading marginal smoothness for a saner vertex count.

## 6. Detail decision

Well evidenced, and includes the batch's clearest example of an explicit, reasoned "how should this
part be represented at the detail level" call:

- **blenderbros-tertiary-details** (`3wJ81Ua7o_w`): explicit DECISION to reserve real modeled
  SubD/boolean geometry for primary/secondary shape-defining details only, and represent tiny
  tertiary details (buttons, logos, labels) with decals/textures instead, "matching standard
  game-asset production practice" -- the clearest single detail-decision item in the whole set.
  Same run: pinching near a mesh boundary under SubD is called an inherent limitation rather than
  always a defect, with an explicit judgment-call framing ("is this something I'd stress about? not
  particularly") and a caution to check more than one matcap before deciding it's worth fixing.
- **blenderbros-subd-hardsurface-2** (`X1IgEb5dyKc`): triangles/n-gons don't need to be forcibly
  eliminated on a flat surface, or even a non-flat one, if the actual subdivided shading result
  already reads clean -- "the deciding test is the rendered/subdivided shading result, not a blanket
  rule against non-quads."
- **blenderbros-decals-workflow** (`411bX85VLh8`): bright/high-contrast accent details pull the eye
  and should be placed deliberately and sparingly, sometimes needing a second balancing accent
  elsewhere; secondary/tertiary detail materials generally read better dialed down (darkened,
  decal alpha lowered to ~0.2) so the detail is perceptible without competing with primary
  shape-defining highlights -- "the key's not to shout, the key's to whisper."
- **cgvoice-amateur-mistakes** (`8HTlZIcqFR0`): large uninterrupted flat/coplanar surfaces read as
  synthetic; breaking a monolithic panel into stepped depth layers (inset panels, recessed lines,
  angled vents at distinct shelf levels) makes it read as more mechanically functional.
- **gnomon-bryant-momo-koshu** (`xS2Bv7-cDe8`): DECALmachine's Project function reshapes a flat decal
  card's own geometry to conform to compound curvature instead of leaving it floating/clipping at the
  corners; a reusable kitbash hardware piece gets a vertex-group with weights stepped from 1.0 (outer
  flange) to 0.2 (rigid core) so later deformation only affects the contact skirt.

## 7. Surface/shading decision

Well evidenced, closely intertwined with topology and modifier decisions (as expected -- shading is
usually the *symptom* that drives the topology/modifier call):

- **blenderbros-subd-hardsurface-2** (`X1IgEb5dyKc`): Bevel corner/miter -> Arc fixes convex-corner
  pinching (also a mistake/correction pair, see below); Surface Slide for curvature-following bevels;
  manual loop-grab-and-stretch as an alternative pinch fix to knife-based topology redirect.
- **pzthree-retopology** (`FgfMVkkSNfQ`): weighted-bevel Outer Miter must be Arc, not the
  Sharp/default -- flagged in the item itself as the *third* independent source converging on this
  exact rule (alongside blenderbros-subd-hardsurface-2 and this video), i.e. a load-bearing,
  cross-validated shading rule.
- **jl-mussi-easy-once-you-learn** (`cbXWWE8-X0M`): support-loop-direction-vs-curvature-pinch
  principle (cited above under topology -- it is simultaneously a shading-decision item since the
  entire test is "does the highlight break").
- **blenderbros-curvy-organic** (`3_RkY_mtlC4`): a uniformly convex surface produces one flat,
  "blobby" highlight band; a shallow concave channel flanked by rounded shoulders breaks it into
  multiple distinct highlight bands that read as more deliberately manufactured; the Bevel
  shader-node fake-rounding approach (cited above under representation choice).
- **gnomon-bryant-momo-koshu** (`xS2Bv7-cDe8`): Data Transfer with interpolated custom normals to
  eliminate the dark shading seam Shrinkwrap alone leaves at an attached part's contact boundary.
- **cgvoice-amateur-mistakes** (`8HTlZIcqFR0`): a mathematically perfect 90-degree edge reads as
  visually dead under scene lighting because it has no surface area to catch a highlight -- even a
  1-segment bevel gives the shader something to reflect.
- **elementza-clean-topology** (`AOW1tBl9VLk`): highlight position as the deciding factor for edge
  placement (cited above under reference interpretation -- genuinely dual-purpose).

## 8-9. Mistake -> correction

**The best-evidenced pairing in the batch**, confirming the curriculum doc's own suspicion. These
are FAILURE-type items that name a concrete break and its concrete fix in the same item:

- **blenderbros-subd-hardsurface-2** (`X1IgEb5dyKc`): convex-corner Bevel pinching under SubD ->
  switch the Bevel's corner/miter setting to Arc, described as "really important," a required fix
  step not an optional tweak.
- **blenderbros-tertiary-details** (`1Z6aEL8uGlA`): a Bevel modifier width sized for the object's
  overall scale overshoots and mangles geometry on a small cut/panel/array element, creating tangled
  edge connections at corner points -> manually shrink that Bevel's width to match the detail's scale
  (down to ~0.2, or ~0.001 for very small keypad-button bevels). Same run: Mirror modifier folds a
  piece onto itself instead of mirroring outward, because Mirror mirrors around the object's *origin*
  and that origin was relocated earlier by a `P > Selection` boolean-cutter separation -> reset the
  origin to geometry (Object > Set Origin > Origin to Geometry) before mirroring.
- **blenderbros-decals-workflow** (`411bX85VLh8`): mirroring a radial/regular array of decals fails
  silently (objects don't appear, or appear misaligned) on the same origin-state gate as above,
  confirmed here for decal objects specifically -> Shift+S > Origin to Geometry, then retry.
- **crnt-boolean-triangle** (`EY6C1SnGVFg`): running Symmetrize on an object with unapplied
  location/rotation produces broken symmetry -- "that mistake I did here before then I realized I
  didn't apply the location and rotation" -> apply transforms (Ctrl+A) before symmetrizing. A
  first-person, directly-narrated hit-and-caught mistake, not just an abstract warning.
- **jl-mussi** (`tRZh0K8R8mQ`): pulling beveled vertices too close together produces SubD pinching
  even when the base cage still looks fine at that stage -- the mistake is visible only downstream of
  the action that caused it, which is itself a useful judgment-training data point (check the
  subdivided preview, not just the cage).
- **jl-mussi-5-tips** (`PHpxiQaH27o`): a Bevel that looks wonky despite correct-looking edge
  selection and geometry is very often caused by flipped face normals, not a geometry problem ->
  check the Face Orientation overlay first, select the flipped faces, Mesh > Normals > Flip, before
  troubleshooting the bevel itself further.
- **mcglasham-subd** (`HfTdQNECvtU`): the entire video is a paradigm-level mistake/correction pair --
  boolean-modifier cuts are diagnosed as unreliable/"finger painting" for anything beyond a quick
  sketch, then corrected by rebuilding the same cut as native inset+fill+control-loop quad topology
  (also cited under representation choice -- this is the batch's clearest case where a mistake and
  its correction are simultaneously a representation-choice reversal).
- **pzthree-retopology** (`FgfMVkkSNfQ`): saving a .blend with Multires and Subdivision Surface both
  present in certain broken states can make the file fail to reload -> if this happens, append
  everything into a fresh scene rather than continuing to try to open the original file. A single
  aggressive Decimate pass (e.g. straight to 0.1) breaks the mesh apart worse than several gentler
  passes -> use multiple ~0.4-0.5-ratio passes instead.
- **cgvoice-amateur-mistakes** (`8HTlZIcqFR0`): boolean-uniting two curved primitives without
  matching vertex resolution/alignment first leaves dense, closely-packed n-gons at the junction;
  attempting to bevel that junction afterward collides the new bevel vertices with the unaligned
  neighbors, producing a tangled overlap instead of a clean fillet -> the real fix is reducing/
  aligning the cutter's vertex count and topology *before* the boolean runs, not trying to bevel the
  damage away afterward (a knife-cut + merge-by-distance + single support ring + loop-slide-disabled
  bevel procedure is given for after the fact once alignment is fixed).
- **subd-3dprint** (`SpYVIKsb294`): SubD level 5 looked marginally smoother but produced an
  unnecessarily large vertex count for a print target -> dialed back to level 4, "still super smooth"
  at a realistic vertex count.

---

## Closing assessment

**Strong (well-evidenced, many independent items, several cross-validated across multiple runs):**
topology decision, modifier decision, detail decision, surface/shading decision, and
mistake -> correction. All five have 5-10+ genuine items apiece, and several rules recur
independently across unrelated runs (the Bevel-miter-must-be-Arc rule appears in three separate
runs; the Shrinkwrap+Data-Transfer attach combo and the origin-must-be-reset-before-mirroring
failure each appear in more than one run too). Mistake -> correction is, as the curriculum doc
suspected, the single deepest-covered pairing in the batch -- nearly every FAILURE-type item names
both the break and a concrete fix in the same entry, several as first-person "I hit this, I caught
it, here's the fix" narration rather than abstract warnings.

**Moderate (present, but narrower or more implicit than the label suggests):** blockout decision
and representation choice. Blockout has five real items, but nearly all of them are actually
*sequencing* rules (what order to cut/subdivide/detail in) rather than the proportion-judgment call
the stage name implies ("is the blockout right yet, and how do I know"). Representation choice
turned out to have more candidate items than the curriculum doc's own hint predicted it might --
eight items genuinely reason about mesh vs. curve vs. modifier-driven vs. shader-fake vs. sculpt for
a specific part. Two are especially explicit alternative-based construction calls:
mcglasham-subd rejects Boolean-driven geometry for native topology based on deformation, UV, and
cross-software consequences; jl-mussi-easy-once-you-learn rejects carving a panel into one curved
shell in favor of a separate Solidify/SubD part to contain density and pinching. The remaining items
are mostly "this trick beats the naive approach because of mechanical property X," which is real
evidence but a shallower form of the reasoning the stage is meant to capture.

**Thin to the point of near-absence:** reference interpretation. Across all 90 items in all 20
runs, exactly one item (`elementza-clean-topology`) actually closes the loop from "here is what the
reference shows" to "here is the specific geometric decision that observation produced." Everything
else adjacent to reference use in this batch is either a preference about *which kind* of reference
source to use, or a validation check run *after* a design decision was already made -- not an
artist reading an ambiguous or occluded shape cue out of a specific photograph and turning it into a
specific build choice on camera. This matches this project's own separate finding (curriculum Level
5 note, and the 2026-08-14 external assessment referenced in `docs/RESEARCH_ROADMAP.md`) that the
target reference-to-model capability itself remains unmet -- the gap isn't a coincidence of which 20
runs got cross-referenced here, it's the same gap this project has already flagged at the
curriculum-design level.

### What would actually fill the thin stages (not more of the same)

- **Reference interpretation** needs a source that keeps a reference photo (or a small reference
  set) visible on screen for extended stretches *while the artist verbally reasons about ambiguous
  or occluded geometry* -- "the reference doesn't show the back so I'm assuming X because Y," "this
  fillet reads as roughly this wide because of how the highlight breaks here," "the photo is shot at
  a slight angle so I'm correcting my read of this proportion before I block it out." A generic
  hard-surface speed-build with a reference pinned in the corner does not do this; what's needed is
  closer to a narrated case study or critique/breakdown video (the kind CG Cookie or Blender Studio
  sometimes publish as "how I read this reference") than another technique tutorial. The existing
  Blender Stack Exchange case study (curriculum item #11, processed separately, not in this batch)
  is worth a targeted re-read specifically for this angle before searching for new sources, since it
  was never checked against this framework either.
- **Representation choice** would benefit less from another hard-surface tutorial (this batch
  already has plenty of those) and more from a source that puts two or three representations of the
  *same* part side by side and narrates the tradeoff explicitly -- e.g. a video or article building
  one pipe/cable/handle both as a curve-with-bevel and as manually-extruded mesh and comparing
  editability/render cost/export behavior, or a sculpt-vs-hard-surface-SubD decision case for an
  organic-to-mechanical transition zone (the only item touching this now, pzthree's Multires-vs-
  voxel-remesh call, is narrow and modifier-scoped rather than a full sculpt/mesh tradeoff
  discussion). CG Boost's curves/procedural content (curriculum Level 11) or Blender Secrets'
  narrower technique-comparison videos are more likely candidates than another full hard-surface
  build-along.
- **Blockout decision** would benefit from a source that spends real screen time on the
  proportion-judgment moment itself -- "here's how I know the blockout is close enough to start
  detailing" against a reference, ideally with a case where the artist revises the blockout after
  judging it wrong -- rather than more sequencing rules about cut order, which this batch already
  covers adequately.

---

## Addendum (2026-08-15, same session): a first search attempt against the reference-interpretation gap

Following this synthesis' own recommendation, searched YouTube for a genuine narrated
reference-critique/breakdown video and checked the two best-looking candidates directly, rather
than assuming a title match would deliver the content:

- **CRNT DESIGNERS -- "How I Modeled Sci-Fi Crate From Reference In Blender"** (`CLvm1722EXY`,
  10:13, channel already used in this project via `crnt-boolean-triangle`). Checked via Gemini
  video-understanding with a prompt specifically asking it to report honestly if the video turned
  out to be generic technique demonstration rather than stretch thin moments into strong claims.
  Result: the video has **no spoken narration at all** -- a silent timelapse with on-screen hotkey
  overlays and background music. There is nothing to extract; reference interpretation requires the
  artist to reason out loud, and this source cannot provide that regardless of what its geometry
  actually shows.
- **Michael McDowell -- "Blender: Modeling With References"** (`Mu_Z5Itw2aI`, 14:32). Has full
  narration (auto-generated transcript read in full, ~12,700 characters). Result: entirely generic
  tool-and-setup instruction using a banana as a placeholder example ("press G to move," "add a
  Mirror modifier," "use proportional editing") -- the reference image itself is never actually
  interpreted; the closest it comes is confirming two reference photos' proportions look
  "approximately the same" before nudging one image a few pixels to align them, which is a
  reference-*alignment* check, not an interpretation of ambiguous geometry. No claim extracted.

**Both results are negative, and both are recorded here rather than silently discarded** so a
future pass does not re-spend a search on either video. This is itself informative: two
plausible-sounding, well-titled candidates in a row failed to contain the target content, which
supports (rather than merely repeats) this document's own claim that generic "how to model from
reference" tutorials are the wrong genre for this gap -- what's needed is closer to a critique
session or narrated case study than a tutorial, and those appear to be rarer/harder to find via
straightforward keyword search than technique tutorials are. Next attempt should consider named
critique-format channels/series (art critique livestreams, portfolio-review content) rather than
searching modeling-tutorial keywords again.
