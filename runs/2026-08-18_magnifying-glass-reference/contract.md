# Frozen reference/decomposition/evaluation contract: hand magnifying glass

Frozen 2026-08-18, before any geometry. Per direct instruction: these criteria are not to be
revised after seeing the modeling result.

## Reference set

- **Primary (front-oblique)**: `ref_front_oblique_round_lens.jpg` -- Wikimedia Commons
  `File:Magnifying_glass.jpg`, CC-BY 2.5 / GFDL, 1304x2067. Clean, canonical form: chrome ring
  bezel with a serrated rim, a knurled collar neck, plain black cylindrical handle. This is the
  primary construction reference.
- **Secondary (side profile)**: `ref_side_antler_handle.jpg` -- Wikimedia Commons
  `File:A_magnifying_glass.jpg`, CC-BY-SA 4.0, 3202x1587. Different specific object (organic
  antler handle) -- used only for cross-checking overall silhouette/proportion ratios and the
  ring-to-neck attachment angle, NOT for handle surface detail (the antler's organic texture is
  explicitly out of scope; the build uses a plain hard-surface handle).
- No authoritative dimensioned spec exists for this object category (unlike the AA battery,
  which had an ANSI/IEC standard) -- this is itself a meaningful, honest difference in reference
  quality that the build must work with, not paper over.

## Component decomposition

1. **Handle** (main hard-surface body): plain cylindrical/lightly tapered form, held in the hand.
2. **Ring/bezel** (attached component): holds the lens, connects to the handle via the neck.
3. **Neck** (curved transition + inset/recess/detail region): a distinct, narrower collar between
   handle and ring, visibly knurled/ribbed in the primary reference -- the natural place for the
   inset-before-extrude-containment skill to apply (a real local detail feature on a curved
   transition).
4. **Lens** (not modeled as glass/optical -- represented as a thin flat disk placeholder; material
   work is out of scope for this pass per the standing "primary form before production prep" rule).

## Width / height / depth constraints (estimated from reference photo proportions, not a spec -- flagged honestly)

Measured from `ref_front_oblique_round_lens.jpg` pixel proportions (ring diameter : handle length
approx. 0.81 : 1) and cross-checked against typical known hand-magnifier sizes (this category
commonly runs 15-25cm total length):

- Ring outer diameter: **~90mm** (estimate)
- Neck length: **~20mm** (estimate)
- Handle length: **~100mm** (estimate)
- Handle diameter: **~16-18mm** (estimate, typical comfortable grip width)
- Overall total length (ring top to handle tip): **~210mm** (estimate)

These are estimates from photo proportions and general product knowledge, explicitly not an
authoritative spec. If a real discrepancy in overall proportion shows up during blockout
comparison, this is the correct place to revise the estimate -- but the ratios and component list
above are frozen and not to be changed after seeing the geometry.

## Major landmarks

- Ring outer edge (serrated/beveled rim)
- Ring inner edge (lens seat)
- Neck-to-ring attachment point
- Neck-to-handle attachment point
- Handle far end (butt cap)

## Negative spaces

- The open lens area inside the ring -- the single unambiguous negative-space feature, must read
  clearly as an open circle in every silhouette check.

## Known vs. unknown

**Known**: overall component list, approximate proportion ratios, general form language (round
lens, cylindrical handle, distinct neck).
**Unknown, explicitly**: exact millimeter dimensions (no spec exists), exact neck taper profile,
exact handle cross-section (perfectly circular vs. very slightly faceted for grip).

## Candidate construction strategies

- **Handle**: capped cylinder (profile revolve), matching this project's own `profile_mesh.py`
  conventions.
- **Ring**: a torus-like revolved profile (a small circular cross-section swept around a larger
  circle), not a primitive torus primitive directly, so the rim bevel can be a deliberate, typed
  decision rather than a modifier default.
- **Neck**: grown directly from the handle's own mesh (inset-then-extrude, following the
  RUNTIME_VALIDATED `extrude.inset_first.local_containment` skill and the live-proven
  body-grown-attachment pattern), not a separate object joined afterward -- this is the
  single most direct place validated knowledge should naturally fire.
- **Ring-to-neck join**: connected as one continuous mesh, not a Boolean; if a Shrinkwrap+Bridge
  join is considered, it must be treated as a hypothesis to test, not assumed correct, per the
  scrapped cylinder-join lesson.
- Rejected: full hybrid Boolean approach (no clear need for it on a form this simple); rejected:
  separate unconnected components for handle/ring/neck (the reference reads as one continuous
  physical object, and the connected-mesh approach is what this project has actual validated
  evidence for).

## Evaluation views

- Front (matching the primary reference's own framing)
- Side profile (matching the secondary reference's framing)
- 3/4 isometric
- Top-down (to check the neck's transition width and ring roundness)

## Human-review criteria (checked before any topology/detail work)

- Silhouette matches the reference's ring-to-handle proportion within a reasonable margin
- Ring reads as circular and open (negative space intact, not accidentally filled or pinched)
- Neck is a real, tapered, curved transition -- not a hard step or a visible seam/fold
- Handle length/diameter ratio looks plausible for something meant to be held
- No visible topology defect (droop, pinch, fold) in a shaded render at any of the four
  evaluation views

Do not proceed past blockout to secondary form or detail work until all of the above pass.
