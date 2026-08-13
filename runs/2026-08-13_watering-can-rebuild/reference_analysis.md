# Reference analysis: watering can

**Status: all v2/v3 rebuild attempts (`.blend` files, build scripts, renders) were deleted on
2026-08-13 per explicit user instruction -- unsuccessful, no trace kept, matching the
adjustable-wrench and boombox precedent. This document is retained in full because the reference
measurements, the recorded taper-direction conflict, and the discovered detail refinements below are
genuine, reusable knowledge, independent of any specific failed build. `references/` (the organized
reference board) and `reference_empties.blend` (a modeling aid, not a model attempt) are also
retained.**

Originally written applying `docs/REFERENCE_COLLECTION_PROTOCOL.md` retroactively against the v3
rebuild, since the build itself happened before this document was written.

## Reference set (by purpose)

| Purpose | Source | Reliability |
| --- | --- | --- |
| Primary-form | `reference/reference_iso_beauty.png` | HIGH -- isolated neutral render, no material/color noise |
| Orthographic | `reference/reference_{front,side,top}_beauty.png` + matching `_mask.png` | HIGH -- same isolated neutral pass, alpha-clean silhouettes confirmed hard-edged (no shadow contamination) |
| Dimension | none | LOW -- no real-world dimension available; all proportions are relative, scaled to a plausible ~17.6cm assumed overall height, not an anchored measurement |
| Construction | none dedicated -- inferred from silhouette only | LOW -- spout/handle attachment points are inferred from where their silhouettes merge into the body's, not from a labeled assembly reference |
| Technique (topology, not shape) | user's live demo file, `4192_autosave.blend` | HIGH for technique, explicitly NOT for proportions (user's own correction: "my model in blender isnt meant to be accurate but moreso to show you topology stuff") |

No manufacturer drawing, dimensioned source, or exploded/construction reference exists for this
asset -- confidence on exact proportions is capped at MEDIUM even where the silhouette measurement
itself is HIGH-confidence, because the object could still be a mis-scaled or mis-proportioned
CC0 asset relative to a real product (unverifiable without a dimensional anchor).

## Recorded conflict: vessel taper direction

```
CONFLICT:
Direct quick visual read of reference_side_beauty.png / reference_front_beauty.png said
"wide at the rim (under the lid), narrow at the base" -- the generic bucket assumption, and what
the v2 build used.

Five independent measurements said the opposite ("narrower at the rim, wider at the base"):
  1. reference_front_mask.png dense alpha-channel row profile, y=240..479, strictly monotonic
     width growth (14px -> 231px), no local maximum -- checked for a missed peak, none found.
  2. Confirmed the alpha transitions are hard-edged (0->185->255 within 2px), ruling out a soft
     ground-contact shadow inflating the lower rows.
  3. reference_front_beauty.png independent color-threshold-against-background measurement,
     same monotonic growth pattern, same magnitude.
  4. Precise dot markers plotted at the exact measured (xmin,y)/(xmax,y) coordinates for two rows,
     zoomed in: the dots visibly land on the true silhouette boundary, and the lower pair is farther
     apart than the upper pair.
  5. reference_top_beauty.png shows two concentric circles -- a wider outer ring visible around a
     narrower inner circle. For an opaque frustum viewed from directly above, that signature is only
     possible if the base is wider than the rim (the rim can't fully occlude a wider base beneath
     it); a normal wide-rim bucket would show only the rim's own circle from directly above.

POSSIBLE CAUSE OF THE VISUAL MISREAD:
The lid's rounded dome sits directly above the vessel and is the most visually prominent, highly
curved element in the frame. It appears to visually "anchor" an impression of width at the top of
the object, even though the actual vessel wall below it (less visually salient, no strong shading
break) has a larger absolute pixel extent at its own base than the dome or the rim does. This was
not a one-time misread -- it recurred on at least four separate look-again attempts in this session,
including on a scale-matched side-by-side overlay that itself likely had an uncorrected alignment
artifact (probably unequal crop margins skewing the visual centerline) rather than being real
countervailing evidence.

CURRENT DECISION:
Vessel is narrower at the rim (R_TOP = 0.0633m) and wider at the base (R_BOT = 0.085m), ratio 0.745.

CONFIDENCE: HIGH for direction (5 independent, non-redundant methods agree, including one --
the top-view ring signature -- that is not a pixel-counting method and is close to unfalsifiable for
this specific question). MEDIUM for the exact ratio (0.745 comes from one measurement method, not
independently cross-checked at the same precision).

WHAT WOULD FURTHER RESOLVE IT:
A second differently-lit or differently-rendered reference pass of the same asset, or (best) the
source GLTF's own bounding radius at rim vs. base read directly -- not permitted under this
benchmark's isolation rule, so not pursued.
```

## Modeling brief (retroactive)

```
OBJECT: modern minimalist metal watering can (Poly Haven watering_can_metal_01, CC0)

PRIMARY COMPONENTS: vessel (body), lid (dome + knob), spout, handle

SECONDARY COMPONENTS: rim seam (vessel-to-lid boundary), spout tip flare, knob boss

PRIMARY PROPORTIONS (all HIGH confidence on ratio, MEDIUM on absolute scale):
  - vessel: R_TOP=0.0633m (rim) : R_BOT=0.085m (base) : wall_height=0.139m
  - dome+knob: 0.037m rise above the rim (~21% of total front-view bbox height)

KNOWN DIMENSIONS: none anchored (no manufacturer/dimensional source) -- LOW confidence on absolute
  scale, only on ratios.

UNKNOWN DIMENSIONS: exact spout/handle attachment depth into the vessel wall (both read as
  overlapping/hidden in every view, never a visible seam); exact dome cross-section curve (only
  visually estimated, not measured pointwise).

CRITICAL SILHOUETTES: rim narrower than base (see conflict above); spout emerges roughly mid-wall
  height, angled ~20 degrees above horizontal, ending in a flattened paddle tip (measured tip
  offset: -0.249m x, +0.136m z from vessel center); handle spans from just under the rim to low on
  the wall near the base, bulging out to ~0.155m from center at its widest.

CRITICAL NEGATIVE SPACES: gap inside the handle loop (open, wire-thin in the reference -- not a
  solid strap); no other enclosed negative space on this object.

CRITICAL DETAILS: rim seam reads as a genuine manufactured fold (Bevel+WEIGHT, not crease -- has
  visible width in the reference); dome/knob/spout-taper read as fully soft-formed with no visible
  seam (no Bevel or crease at all, not even a defaulted-to crease -- see edge_crease.md's own
  ring-loop-crease failure mode this build re-discovered).

REFERENCE CONFLICTS: taper direction (resolved above, HIGH confidence).

MODELING RISKS: absolute scale is unanchored: if this asset is ever compared against a truly
  dimensioned reference later, only the ratios in this brief should be trusted, not the meter values.

CONFIDENCE: HIGH on shape/topology decisions, MEDIUM on absolute scale.
```

## Discovered refinements (targeted detail crops, protocol's iterative loop)

Per the protocol's `COLLECT -> MODEL -> DISCOVER UNKNOWN -> TARGETED SEARCH -> UPDATE REFERENCES ->
CORRECT MODEL` loop: generating close-up crops from the existing isolated renders (no new source
needed) surfaced two real shape details v3 does not yet have. Recorded here rather than applied
immediately -- v3 is still awaiting direct user review, and these are refinements, not defects that
invalidate that review.

- **Spout tip is a slanted flat disc, not a symmetric rounded flare.** `references/details/
  spout_tip_closeup.png` shows a flat, angle-cut oval face (like a coin sliced on the bias), not the
  paddle-with-rounded-top v3 currently builds. LOW-effort fix: change the tip ring's cap face to a
  single flat plane oriented at an angle to the tube axis, rather than scaling the ring itself.
- **Dome crest is asymmetric and notched, not a plain symmetric dome.** `references/details/
  rim_seam_closeup.png` shows a diagonal notch/step cut into the crown's silhouette near the knob,
  not visible in v3's rotationally-symmetric dome. This is a real secondary-form detail, not just
  shading -- would need the dome's ring construction to stop being perfectly axisymmetric at the
  very top.
- Rim seam itself (the horizontal step where the lid meets the vessel) is confirmed as a genuine
  visible ledge with real width -- corroborates the Bevel+WEIGHT choice already made for the vessel
  rim in v3, not a needed change.

## Per-reference metadata

| File | Type | Purpose | View | Reliability | Dimensional value | Detail value | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `references/primary/reference_isometric_beauty.png` | isolated neutral render | primary-form | iso | HIGH | none | overall gestalt | HIGH shape, LOW scale |
| `references/orthographic/reference_{front,side,top}_beauty.png` + masks | isolated neutral render | orthographic | front/side/top | HIGH | proportions only, hard-edge-verified (no shadow contamination) | taper, spout, handle, dome | HIGH |
| `references/details/rim_seam_closeup.png` | crop of side beauty | detail | side | HIGH | none | rim step confirmed real (Bevel-appropriate) | HIGH |
| `references/details/spout_tip_closeup.png` | crop of side beauty | detail | side | HIGH | none | tip is a slanted flat disc, not v3's flare | HIGH (not yet applied) |
| `references/details/knob_closeup.png` | crop of iso beauty | detail | iso | HIGH | none | knob shape | MEDIUM |
| `references/details/handle_attachment_closeup.png` | crop of iso beauty | detail | iso | HIGH | none | wire-thin handle confirmed | HIGH |
| `references/uncertain/taper_direction_verification_dots.png` | analysis artifact, not a source | -- | front | -- | -- | proof artifact for the taper conflict above | -- |

No `dimensions/`, `materials/`, `context/`, or `inspiration/` entries -- none exist for this CC0
asset, left empty deliberately.

## Primary / secondary / tertiary forms

- **Primary**: vessel (tapered body), lid dome, spout, handle.
- **Secondary**: rim seam, knob boss, spout tip flare/disc, handle attachment points.
- **Tertiary**: dome crest notch (discovered, not yet applied -- see refinements above), any surface
  imperfections (none visible at this render resolution).

## Negative space

- The open loop inside the handle (a real gap between the wire and the body, confirmed thin-wire in
  the reference, not a solid strap).
- No other enclosed negative space -- the vessel is a simple closed vessel+lid+spout form.

## Failure-modes checklist, checked against v3

- Single-image overfitting: avoided -- front/side/top cross-checked, plus the top-view ring
  signature was the deciding piece of evidence for the taper conflict.
- Perspective tracing: not applicable -- orthographic reference renders.
- Incorrect scale: real, unresolved risk -- no dimensional anchor; v3's ~0.176m total height is an
  assumed plausible scale, not measured.
- Detail-first modeling: avoided -- vessel/spout/handle (primary) built and corrected before
  pursuing the tip-disc/crest-notch tertiary refinements above.
- Reflections/shadows mistaken for geometry: checked and ruled out (hard-edge alpha verification in
  the recorded conflict above).

## Search strategy: deliberately not executed for this asset, and why

Same reasoning as the telephone rebuild's brief: this is a CC0 Poly Haven asset
(`watering_can_metal_01`), not a real manufactured product with a findable manufacturer drawing, and
this project's own held-out-benchmark isolation rule prohibits using anything beyond the isolated
neutral render as modeling guidance here. A generic web search for "watering can dimensions" would
return an unrelated real product's specs. Deliberate, recorded skip.

## What this recorded conflict is worth to the project

This is now the second time in this project a quick visual glance was wrong and repeated,
corroborated measurement caught it (the first being the boombox/wrench "automated pass, human
review overturns it" pattern -- this is the inverse: a human-style quick glance was wrong, and
*measurement* corrected it). Both directions of failure are now on record: neither "trust the
automated number" nor "trust the first glance" is safe on its own; corroboration across independent,
non-redundant methods is what actually resolved this one.
