# Controlled reproduction: Shrinkwrap+Bridge cylinder join vs. naive Boolean Union

Phase C of the 2026-08-17 continuation directive, following the Phase B independent review in
`runs/2026-08-17_real-video-connecting-cylinders-review/`. Reproduces the Priority-1 captured
technique (source `IS2LPVNp6SE`, McGlasham "Connecting Cylinders" #15) on neutral geometry: a
"body" cylinder with a "spout" cylinder joined to its side at a right angle, built via
`tools/run_cylinder_join_lab.py`.

## Experiment design

- **QUESTION**: does the captured recipe (loop cut / collar ring -> vertex group -> Shrinkwrap
  Project -> apply -> delete interior -> join -> Bridge Edge Loops -> Subdivision Surface) produce
  a manifold, clean-topology joint in current Blender (5.2)?
- **CONTROL**: the same two cylinders joined with a Boolean Union modifier instead -- the naive
  alternative the source explicitly warns against.
- **TREATMENT**: the captured recipe, built via explicit bmesh ring construction (not interactive
  slide operators, which do not reliably run in `--background` mode) rather than through this
  project's typed operator surface, which does not yet expose Shrinkwrap/vertex-group/join
  primitives (see `docs/...` Section 17 guidance: don't add typed operations before they're needed).

## Result: treatment measurably beats the naive alternative

| | Treatment (Shrinkwrap+Bridge) | Control (Boolean Union) |
|---|---|---|
| Evaluated faces | 896, all quads | 1360, all quads |
| Non-manifold edges | **0** | **24** |
| Boundary edges | 0 (fully closed) | 24 (not closed) |
| Pole valence | 3 (x32, cap rings), 16 (x2, cap centers) -- both from the far ngon end caps, unrelated to the joint | 3, 5, 6, 8, 11, 16 -- scattered, irregular |

The Boolean control produced a real, measured topological defect (24 non-manifold edges) that the
Shrinkwrap+Bridge treatment did not. This is independent, quantitative confirmation of the same
conclusion the Phase B video review already established (booleans as disposable measurement
patches, not final topology) -- from a different method (a controlled experiment on this project's
own geometry, not more video review), matching Priority 1's "compare against a naive alternative"
requirement.

## Two real bugs found and fixed during this run -- not blind parameter guessing

**Bug 1 (real, fixed): wrong Shrinkwrap projection axis.** The Spout cylinder's tube geometry runs
along local X, but its object was never rotated (unlike the tutorial, which duplicates and rotates
the actual object) -- the axis was baked directly into vertex coordinates instead. Its Shrinkwrap
modifier was initially configured with `axis="Z"` (copy-pasted from the Body cylinder, whose tube
genuinely does run along local Z), which projects perpendicular to the tube's actual length instead
of along it. Fixed to `axis="X"`, matching Spout's real local frame.

**Bug 2 (real, root-caused, not fully resolved): partial angular coverage.** After the axis fix, a
dihedral-angle sweep of the base control cage (`f1.normal.angle(f2.normal)` across every manifold
edge) still showed several edges at 167-173 degrees -- a genuine sharp fold, not healthy curvature
(healthy SubD-safe edges in this same mesh sit around 20-40 degrees). Tracing the flagged edges'
coordinates back to the source geometry: Body's collar ring is a full 360-degree circle around its
own axis, but Spout's tube only extends in one direction (+X), covering roughly half of that circle
angularly. Shrinkwrap Project leaves a vertex at its original position when its projection ray finds
no hit -- so the half of Body's ring nearest Spout conforms correctly, while the far half stays
essentially where it started, and the boundary between "conformed" and "unmoved" is a hard fold.

This is a real limitation of *this test rig's geometry*, not evidence against the technique: a
first attempt at increasing mutual overlap (bringing both collars from the tube's midline out to
`near=+-0.5` down to a much deeper `near=+-0.15`) held the defect at roughly the same severity
rather than fixing it, which is itself informative -- it means the fix isn't "more overlap," it's
what the source's own recipe already includes and this reproduction deliberately left out for a
first pass: a seam-sharpening control loop (Linear interpolation, elevated smoothing factor) added
*after* the bridge, exactly the technique already captured as a separate PROCEDURE item in
`runs/2026-08-17_video-study-mcglasham-subd-primitives-and-connections/knowledge_items.json`.

**What did NOT happen, for the record**: an earlier attempt to fix Bug 2 by guessing at the overlap
parameter (`near=0.5` -> `near=0.25` for both, no diagnostic basis) made the shape collapse into an
unrecognizable pinched wedge -- a real regression, caught immediately from the render, reverted, and
replaced with the dihedral-angle measurement above instead of another guess.

## Visual evidence

`treatment_iso.png` / `treatment_front.png`: a clean, mostly-smooth elbow shape with one visible
minor crease at the inner corner of the joint, matching the diagnosed dihedral-angle finding above.
`control_iso.png` / `control_front.png`: the Boolean Union result, matching the diagnosed
non-manifold-edge count -- visually smoother than expected from that count alone (Subsurf hides some
topological messiness under shading), a useful reminder that mesh-health metrics and shaded
appearance can each miss what the other catches, which is exactly why both were checked.

## Status and next step

This is `EXPERIMENTALLY_TESTED`, not `TRANSFER_VALIDATED` -- reproduced once on the geometry built
specifically for this test, not yet on a second, different shape. Per `docs/KNOWLEDGE_SYSTEM.md`,
the underlying knowledge item status is unchanged (still `CAPTURED`). Concrete next step: add the
seam control loop (the specific step this pass deliberately omitted) and re-measure the same
dihedral-angle sweep before attempting a second transfer target (a different radius ratio or join
angle, per this project's own transfer-test rule: change the shape while preserving the same
underlying joining problem).
