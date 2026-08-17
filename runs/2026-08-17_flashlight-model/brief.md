# Held-out prop: Maglite 2D flashlight -- primary-form pass, headless pipeline

Requested directly by the user as the held-out prop to test whether this project's current mature
tooling can be driven the same way its other (non-interactive) sessions work: no live Blender GUI,
no socket connection, no addon bootstrap -- everything below ran as `blender --background` subprocess
calls against `tools/run_modeler_command_sequence.py`, the same declarative-JSON-sequence mechanism
already used throughout `runs/2026-08-16_*` work (e.g. the SMEG KLF03 stage scripts). This is a
genuine test of that mechanism on a target this session had never modeled before, not a demo on a
pre-solved case.

## Why a Maglite 2D specifically

A "Flashlight" prop exists once already in this project's history (`runs/2026-08-07_speaker-typed-
protocol`-era work), but that was a basic proof-of-concept revolved cylinder for the decision-
transaction protocol itself, built before this project had any reference-interpretation discipline,
reference-set gating, or headless typed-sequence tooling. The user was told this directly and chose
to proceed anyway, since the capability actually being tested here -- a real photo-and-spec-
referenced build through the CURRENT pipeline -- has never been attempted on this object.

## Reference gathering (real sources, gated)

Two real photographs (Wikimedia Commons, CC-BY-SA, downloaded with explicit user permission since
the in-app browser's screenshot tool was not rendering this session) plus the official Maglite
specification page:

- `references/wikimedia_maglite_01.jpg` -- three-quarter oblique product photo, primary form and
  construction evidence (tail cap shape, knurl band position, switch position).
- `references/wikimedia_maglite_switch_detail.jpg` -- close-up on a color-variant unit, confirming
  the switch's pointed-oval shape and its position at the smooth-barrel/knurl-band boundary.
- `maglite.com/pages/specifications-maglite-2-cell-d-led-flashlight` -- official manufacturer
  dimensions: length 254 mm, barrel diameter 39.67 mm, head diameter 57 mm.

`reference_manifest.json` encodes this as a structured `ReferenceSet` (the same schema
`tools/verify_reference_set_gate.py` audits for every other prop in this project) and **passes the
gate cleanly**: `runs/2026-08-17_flashlight-model/reference_gate_report.json`,
`"pass": true, "disposition": "READY_TO_MODEL"`. Three independent sources, all critical properties
covered by HIGH-confidence claims, a real dimensional anchor, no unresolved conflicts. One low-impact
research question (exact bezel/lens internal step count) was explicitly deferred with a stated
modeling constraint rather than either guessed at or silently left open.

## Build sequence (headless, typed, three stages)

1. **`stage_01_primary_body_sequence.json`** -- `create_revolved_profile` on a 9-point (radius, z)
   profile in cm, anchored to the two official diameters and the official length, proportions for
   the tail/barrel/neck/head zones read by eye from the oblique photo. 32 radial segments. Result:
   288 verts / 576 edges / 288 faces, 0 non-manifold, 0 ngons, 0 degenerate -- clean by construction,
   confirmed via `get_full_state`. Rendered silhouette showed correct overall proportions but a
   visibly faceted (angular, not curved) neck-to-head transition -- expected from only 3 profile
   points across that zone.
2. **`stage_02_smoother_head_sequence.json`** -- rebuilt with 15 profile points, denser through the
   neck/head zone. The silhouette barely changed -- the real fix wasn't more (r, z) points, it was
   recognizing this is a genuinely continuous curved shell that needed the right tool, not more
   manual point-pushing.
3. **`stage_03_subsurf_sequence.json`** -- added a Subdivision Surface modifier (levels 2) and
   `set_smooth_by_angle`, matching this project's own standing rule ("SubD belongs only on
   continuous curved shells whose cage supports it" -- `docs/DEVELOPMENT_PRIORITIES.md`). This is
   what actually fixed the faceting: `stage03_side_silhouette.png` now reads as a genuinely smooth,
   continuously curved flashlight silhouette -- rounded tail, straight barrel, smooth bulbous head.

All three stages ran as one-shot `blender --background --factory-startup --python
tools/run_modeler_command_sequence.py -- --sequence ... --report ... --load ... --save ...`
subprocess calls. No GUI was open at any point. One real operational bug hit and fixed along the
way: relative output paths resolved against the Windows drive root (`C:\`) rather than the working
directory Blender was launched from, silently writing renders to `C:\runs\...` on the first attempt
-- switched to absolute paths for every `--load`/`--save`/`--report`/`output_path` afterward.

## Honest visual comparison against the reference photo

Side by side against `wikimedia_maglite_01.jpg` (mentally rotated 90 degrees, since the reference
photo is oblique/horizontal and the renders are vertical along the revolve axis):

**What matches well:** overall length-to-diameter proportion (anchored directly to real numbers, not
estimated), the head-diameter-to-barrel-diameter ratio (1.44x, matching the official 57mm/39.67mm
ratio exactly since both were used as direct inputs), the general shape language of a straight
barrel widening into a rounded bulbous head.

**What does NOT match closely, stated plainly rather than glossed over:**
- The tail cap on the real unit is nearly flush with the barrel diameter, a subtle, blunt rounded
  end. This build's tail taper is more pronounced/exaggerated than the reference shows -- a
  proportion-reading error from eyeballing the oblique photo, not a tooling limitation.
- The real head's bulb reads as more distinctly spherical, with a clearer secondary neck-in for the
  knurled focus bezel ring right at the front. This build's head is a reasonable but softer
  approximation of that two-stage character.
- No quantitative silhouette comparison (IoU, contour error) was run against the reference photo --
  that would require segmenting the oblique photo's silhouette first (background removal via
  `tools/segment_reference_grabcut.py` or similar), which was not done this pass. The comparison
  above is a stated visual judgment, not a measured one.

## What is deliberately NOT done yet (primary form only, per this project's own blockout-before-
## detail discipline)

The switch button, the knurled grip band, the smooth/knurl surface transitions, the bezel ring,
the lens recess, and the engraved text are all real secondary/tertiary features confirmed in the
reference set but not yet built -- this pass stopped at primary form and silhouette specifically
because that is the gate this project's own accumulated evidence says should be confirmed before
detail work starts (see the same-day Level 14 synthesis and multiple `docs/BENCHMARK_HISTORY.md`
entries on the same lesson).

## What this pass does and does not prove

It proves the headless, non-interactive pipeline works end to end on a genuinely new target: real
gated references, a typed command sequence with zero raw `execute_blender_code` calls, clean mesh
health at every stage, and a silhouette that recognizably reads as the intended object. It does
**not** prove reviewer-accepted resemblance -- per `docs/SYSTEM_CAPABILITY_AUDIT_2026-08-17.md`'s own
standing rule, that requires the human step this session cannot perform on its own: an actual look
at the render by a person, followed by a judgment. That review is the next step, not something to
claim here.
