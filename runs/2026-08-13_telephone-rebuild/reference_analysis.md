# Reference analysis & modeling brief: vintage telephone wall clock

**Status: the first build attempt (`telephone.blend`, `tools/build_telephone.py`, all renders) was
deleted on 2026-08-13 per explicit user instruction ("the model you're currently making is shitty
and wrong, delete all the test models") -- matching the watering can, wrench, and boombox precedent.
This document, `references/` (the organized reference board), `reference_empties.blend`, and
`scene_decomposition.json` are retained as durable knowledge. The build did pass every fresh-process
mesh check and the scene-decomposition coverage check, and did fix several real bugs found live
(wrong ring-plane orientation on two different tubes, a missing shoulder bridge, an EXACT-solver
Boolean failure, crown faceting from an unrounded 4-sided cross-section) -- none of that made it
visually correct, which is the only verdict that matters. No further attempt is in progress.**

Written BEFORE any Blender construction, per `docs/REFERENCE_COLLECTION_PROTOCOL.md` ("modeling
brief before Blender") -- applying the discipline the watering can rebuild only applied
retroactively, and specifically watching for the exact failure that cost the most time there: a
confident quick glance about which end of a tapered/curved form is larger, taken at face value
instead of cross-checked.

## Reference set (by purpose)

| Purpose | Source | Reliability |
| --- | --- | --- |
| Primary-form | `reference/reference_isometric_beauty.png` | HIGH -- isolated neutral render |
| Orthographic | `reference/reference_{front,side,top}_beauty.png` + matching `_mask.png` | HIGH -- same isolated pass as the watering can's, same pipeline |
| Construction contract | `benchmark_brief.md` (this project's own predeclared rules, written before source download) | HIGH -- authored before candidate modeling, not after-the-fact rationalization |
| Dimension | none | LOW -- no anchored real-world dimension, same limitation as the watering can |
| Construction/assembly detail | none dedicated | LOW -- hinge/latch/hook-switch geometry is inferred from silhouette only, not a labeled teardown |

## Four views cross-checked against each other before writing anything down

Front, side, top, and iso all agree independently (not just a single glance accepted at face
value): a tall, narrow, shallow-depth housing (front view is much wider than side view, confirming
the box is thin front-to-back, not square in plan); a rounded/arched crown at the top of the front
face; a front-face recessed panel holding a circular rotary-dial ring and a small rectangular
number-card holder above it; small hinge pins and a latch visible on the side edge at roughly
mid-height; a wider, shallower base plinth below the main housing; and a handset assembly (two bell-
shaped cradle cups with ball finials, connected by a straight bar/rail that is the actual handset,
plus a hook-switch lever) mounted on that base plinth, extending toward the viewer in the front/iso
views and visible as a raised bar in the top view.

No conflicting read between views on any major proportion -- unlike the watering can, there is no
single dominant curved feature creating a plausible alternate reading, so this cross-check is treated
as sufficient corroboration for the primary/secondary forms without needing pixel-level measurement
before starting. Component-level dimensions (dial ring radius, hinge spacing, bell diameter) will
still need pixel measurement during modeling, not guessed.

## Modeling brief

```
OBJECT: vintage telephone wall clock (Poly Haven vintage_telephone_wall_clock, CC0)

PRIMARY COMPONENTS: main housing (arched-crown box), base plinth, handset (bar between two bell
  cradles), cradle/hook-switch assembly

SECONDARY COMPONENTS: front recessed panel, rotary-dial ring (two concentric rings + finger holes),
  number-card holder, side hinge pins, side latch, hanging cord/hook

PRIMARY PROPORTIONS (MEDIUM confidence -- cross-view agreement, not yet pixel-measured):
  - housing: tall and narrow in front view, shallow in side view (roughly 3-4x taller than deep)
  - base plinth: noticeably wider (front-view) and shallower (vertically) than the main housing,
    a distinct step out at the bottom
  - handset bar: spans roughly the same width as the base plinth, sitting just above/on it

KNOWN DIMENSIONS: none anchored.

UNKNOWN DIMENSIONS: exact dial ring radius and finger-hole count/spacing; exact hinge/latch
  placement; handset bar diameter vs. bell cup diameter ratio; crown arch curvature.

CRITICAL SILHOUETTES: arched crown breaking the housing's otherwise rectangular front profile;
  the housing-to-plinth step (plinth wider, not a continuous taper -- this is a distinct component
  boundary, per `benchmark_brief.md` rule 1, not a single loft); the handset bar reads as a genuine
  removable assembly, separate from the fixed cradle cups per `benchmark_brief.md` rule 2.

CRITICAL NEGATIVE SPACES: the gap between the handset bar and the cradle cups it rests in/near (side
  view shows the bar sitting on top of, not merged into, the bell shapes); the finger holes around
  the dial ring; the hook-switch's own hook shape.

CRITICAL DETAILS: `benchmark_brief.md` rule 4 requires the dial to be built from intentionally
  sparse authored radial loops (12-16 verts), not evaluated smoothness alone; rule 5 requires
  semantic bevel-weight selection on hard manufactured edges (this project's now-established
  Bevel-vs-crease heuristic: a stamped-metal housing with visible panel breaks likely wants Bevel+
  WEIGHT at real seams, not crease, unlike the watering can's soft-formed dome).

REFERENCE CONFLICTS: none found on this pass -- flagged here explicitly so a later contradiction is
  compared against "none expected," not silently absorbed.

MODELING RISKS: absolute scale unanchored (same caveat as the watering can); hinge/latch/hook-switch
  are small enough that their exact shape may only resolve once pixel-measured at construction time,
  not from this brief alone -- per the protocol's own iterative-collection loop, that measurement
  should happen when the question comes up during modeling, not be guessed now.

CONFIDENCE: MEDIUM on primary/secondary structure (strong four-view agreement, no anchor
  dimension); LOW on exact small-detail proportions until pixel-measured during construction.
```

## Targeted detail crops (resolved several "unknown dimensions" from the first pass)

Per the protocol's iterative loop, generating close-up crops from the existing isolated renders
(no new source needed, same reuse-for-a-different-purpose as the watering can's) resolved several
items this brief's first pass had marked LOW-confidence/unmeasured:

- **Dial ring finger holes: 12, evenly spaced** (`references/details/dial_ring_closeup.png`),
  matching `benchmark_brief.md` rule 4's own suggested "12-16 vertices at this scale" almost exactly
  -- a real, count-verified number now, not a guess.
- **Handset bar is NOT a uniform-diameter rod.** `references/mechanism/handset_cradle_closeup.png`
  shows a distinct barrel/bulge in the middle third, tapering to thinner cylindrical ends that
  connect to the bell cradles -- three-segment profile (thin-thick-thin), not a single extrusion.
- **Two additional hook/prong contacts are visible hanging below the handset bar**, near each
  bell, separate from the single side-mounted hook-switch lever seen in the side view -- likely the
  actual electrical hook-switch contacts the handset bar rests on and depresses, distinct from the
  side hook (which may be a cord guide or a second, decorative hook). Flagged LOW confidence on
  which is which; will re-examine at modeling time rather than guess now.
- **Bell cradles are true cone/bell shapes with a ball finial on a thin stem**, mounted to the base
  plinth -- confirms `benchmark_brief.md` rule 3's assumption these are separate parts.
- **Hinges are circular pin holes along the housing's side seam** (2 visible), with a small latch
  lever near the middle one (`references/details/hinge_latch_closeup.png`).

These are now MEDIUM-to-HIGH confidence (count-verified or shape-verified from a clean isolated
crop, not eyeballed from the full-scene view) and should be used directly during construction rather
than re-estimated.

## Per-reference metadata

| File | Type | Purpose | View | Reliability | Perspective | Dimensional value | Detail value | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `references/primary/reference_isometric_beauty.png` | isolated neutral render | primary-form | iso | HIGH | orthographic-ish (fixed benchmark camera) | none (no anchor) | overall gestalt | HIGH for shape, LOW for scale |
| `references/orthographic/reference_front_beauty.png` | isolated neutral render | orthographic | front | HIGH | true orthographic | proportions only | crown, dial, card holder | HIGH |
| `references/orthographic/reference_side_beauty.png` | isolated neutral render | orthographic | side | HIGH | true orthographic | proportions only | depth, hinge/latch, hook | HIGH |
| `references/orthographic/reference_top_beauty.png` | isolated neutral render | orthographic | top | HIGH | true orthographic | proportions only | handset-over-housing layout | HIGH |
| `references/details/dial_ring_closeup.png` | crop of front beauty | detail | front | HIGH (same source, higher zoom) | orthographic | finger-hole count (12) | dial construction | HIGH |
| `references/details/hinge_latch_closeup.png` | crop of side beauty | detail | side | HIGH | orthographic | hinge spacing (relative) | hinge/latch shape | MEDIUM (small, some ambiguity on exact latch geometry) |
| `references/mechanism/handset_cradle_closeup.png` | crop of front beauty | mechanism | front | HIGH | orthographic | bar segment proportions | handset/cradle construction | HIGH |
| `references/mechanism/hook_switch_closeup.png` | crop of side beauty | mechanism | side | HIGH | orthographic | none | hook shape | MEDIUM (identity of this hook vs. the cradle-mounted contacts is unresolved) |
| `benchmark_brief.md` | predeclared construction contract | construction | n/a | HIGH (authored before modeling) | n/a | radial-loop-count guidance | construction rules | HIGH |

No entries in `dimensions/`, `materials/`, `context/`, or `inspiration/` -- none exist for this asset
(no anchored real dimension, no material-specific photography beyond the uniform neutral-gray
override, no usage/context photography, and no separate stylized inspiration source was used). Left
empty deliberately rather than populated with something that doesn't belong there.

## Primary / secondary / tertiary forms

- **Primary** (defines identity/silhouette): main housing box with arched crown; base plinth;
  handset bar; two bell cradles.
- **Secondary** (construction/recognizable design): front recessed panel; dial ring; number-card
  holder; side hinge pins and latch; hook-switch contacts/lever.
- **Tertiary** (small realism detail): individual finger-hole counts/spacing on the dial; ball
  finials on the cradle stems; the barrel-taper profile of the handset bar; the hanging-cord/hook
  detail's exact curve.

Construction order should follow this list top to bottom, per the protocol's "do not spend
excessive time on tiny details before primary/secondary structure is understood."

## Negative space

- Gap between the handset bar and the housing/plinth below it (the bar is elevated on its cradle
  stems, not resting directly on the plinth surface).
- The dial's 12 finger holes -- real punched-through negative space, not a decal/texture.
- The gap inside the hook-switch hook shape.
- No enclosed door/panel opening is implied by any view -- the "recessed panel" reads as a shallow
  inset, not a hinged door with a real interior cavity, despite the hinge pins (those may be
  decorative/functional for a small maintenance hatch too small to resolve from these views; flagged
  LOW confidence, will re-examine at modeling time rather than assume either way).

## Mechanical/product object questions (per protocol section 17)

- **What moves?** The dial (rotates), the hook-switch lever/contacts (the handset bar depresses
  them when hung up), the handset itself (lifts off the cradle).
- **What's structural vs. cosmetic?** Housing, plinth, cradle stems: structural. Ball finials,
  card-holder frame: cosmetic.
- **What's separately manufactured?** Handset bar (a real removable assembly, per
  `benchmark_brief.md` rule 2); dial insert; hook-switch hardware. The main housing and its crown are
  one continuous stamped/cast shell (rule 1).
- **Where are seams/clearances?** Housing-to-plinth step (a real component boundary, not a taper);
  hinge-pin seam on the side edge; handset-to-cradle clearance gap.

## Failure-modes checklist (protocol section 23), checked against this plan

- Single-image overfitting: not applicable -- four views cross-checked, plus targeted detail crops.
- Perspective tracing: not applicable -- all reference renders are orthographic, not photographs.
- Incorrect scale: real risk, unresolved -- no dimensional anchor exists; flagged, not silently
  assumed.
- Mixed product variants: not applicable -- single CC0 source asset, no variant ambiguity.
- Conflicting views: none found (see four-view cross-check above).
- AI-generated reference contamination: not applicable -- source is a real modeled CC0 asset.
- Detail-first modeling: actively avoided -- primary/secondary/tertiary ordering set above before
  any construction.
- Insufficient rear/side/top evidence: not applicable -- front/side/top/iso all present; no rear
  view exists in this benchmark's reference set, but the object reads as front-facing-only
  (wall-mounted), so a rear view has low expected information value here.
- Reflections/shadows mistaken for geometry: checked -- the neutral Workbench cavity/studio pass
  used for these renders does not add a ground shadow (confirmed on the watering can's hard-edged
  alpha; same render pipeline for this asset), so no shadow-as-geometry risk.

## Search strategy: deliberately not executed for this asset, and why

`docs/REFERENCE_COLLECTION_PROTOCOL.md`'s search-strategy and "how the object is made" sections
call for external search (manufacturer drawings, teardown documentation, technical drawings). Not
run here: this object is a CC0 Poly Haven asset (`vintage_telephone_wall_clock`), not a real
manufactured product with a documented manufacturer -- there is no external technical drawing to
find, and this project's own held-out-benchmark methodology (`benchmark_brief.md`'s own "isolated
neutral reference generation" boundary, declared before source download) specifically prohibits
using anything beyond the isolated neutral render as modeling guidance for this asset. Running a
generic web search for "vintage telephone dimensions" would return a real antique product's specs,
which have no verified relationship to this specific 3D asset's actual proportions -- using them
would silently mix an unrelated reference in, exactly the "mixed product variants" failure mode the
protocol itself warns against. This is a deliberate, recorded skip, not an oversight.

## Explicit application of the watering-can lesson

Before treating any single-glance proportion claim in this brief as settled, the plan is: if a
future comparison render disagrees with this brief on a major proportion (not a small detail), stop
and cross-check with at least one other independent method (a different view, a precise pixel
measurement, or a top-down occlusion check like the watering can's ring signature) before trusting
either the glance or the first measurement alone.
