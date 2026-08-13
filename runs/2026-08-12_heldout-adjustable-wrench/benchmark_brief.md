# Held-out benchmark: vintage adjustable wrench

Frozen 2026-08-12, before download or any neutral-reference rendering.

## Source

Poly Haven CC0 `adjustable_wrench` ("Adjustable Wrench" by Mateusz Sadek, donated, CC0). Source
geometry will be isolated to neutral reference renders only, the same way every other held-out
family in this project has been handled -- construction will use pixels/measurements only, never
the source topology, object names, modifiers, materials, or construction.

## Why this asset

- P0 category fit: hand tool / mechanical part.
- Genuinely different shape family from every prior held-out asset this session (boombox removed;
  camera, telephone, watering can, desk lamp are the remaining set) -- an elongated, single-plane
  tool with a jaw mechanism and adjuster wheel at one end and a plain handle at the other, not a
  revolved container, an articulated multi-joint assembly, or a flat panel product.
- Bounded scope: unlike the desk lamp, this is not multi-jointed/articulated, so it is a reasonable
  size to complete end to end in one session rather than another multi-day benchmark.
- Directly exercises the capability just built and validated retroactively
  (`tools/verify_reference_view_orientation.py`) on a genuinely new, previously-unseen reference for
  the first time -- this is the actual test of whether that tool changes real workflow behavior, not
  just documents a lesson.

## Contract, frozen before any reference inspection

- Construction rule: the wrench's jaw, adjuster housing, shaft, and handle must be built as
  continuous, connected, all-quad geometry where they form one physically continuous part (matching
  this project's established "edit mode, not primitive assembly" lesson from the boombox/camera
  corrections). Separate objects are reserved for genuinely separate, distinct-material or
  serviceable parts only (e.g. a wooden handle vs. a steel head, if the reference shows a visible
  material break there; the adjuster wheel/worm screw if it reads as a distinct inserted part).
- **Step 0, before any landmark measurement or construction**: run
  `tools/verify_reference_view_orientation.py` against the neutral references with the intended
  in-plane build axis, and do not proceed with construction on an axis it flags as inconsistent.
- Landmarks (jaw opening, adjuster position, shaft length/taper, handle end) will be measured from
  the reference row/column profile via `tools/measure_reference.py`, not eyeballed.
- Visual gates (normalized silhouette IoU against the isolated reference, comparison method matching
  `tools/compare_alpha_multiview.py`) will be declared immediately after the reference is measured,
  before any candidate geometry is built, and not adjusted afterward except by rejecting a candidate
  and building a better one.
- Fresh-process independent verification (no non-manifold edges, no degenerate faces, no loose
  vertices, positive volume) is required before any pass is claimed.
- This benchmark is not claimed as professional-quality or expert-accepted regardless of outcome;
  automated gates passing is not the same as visual fidelity, per this project's own boombox
  evidence.
