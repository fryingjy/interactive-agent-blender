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

## Follow-up: isolated variable test of the fold's cause -- hypothesis rejected

Bug 2's diagnosis (partial angular coverage: `PROJECT` mode leaves a vertex exactly where it started
when its ray finds no hit) implied a specific, testable prediction: switching `wrap_method` from
`PROJECT` to `NEAREST_SURFACEPOINT` (which always finds *some* point on the target regardless of ray
direction) should measurably close the fold. Tested as an isolated variant
(`treatment_nearest_surface_variant`, everything else held constant) with a proper measurement added
to the script itself (`max_dihedral_angle_degrees`, run pre-Subsurf on the base cage) instead of an
ad hoc one-off check:

| | PROJECT (treatment) | NEAREST_SURFACEPOINT (variant) |
|---|---|---|
| Max dihedral angle | 173.0 deg | 163.6 deg |
| Median dihedral angle | 27.4 deg | 82.1 deg |

The prediction is **rejected**. The worst-case fold barely improved (173 -> 163.6, still a near-hard
crease), and the median angle got much worse (27.4 -> 82.1) -- the whole ring became uniformly
tighter/more strained, not just the localized fold. `variant_nearest_surface_iso.png` confirms this
visually: a hard fin-like flap at the joint, a more obvious defect than the original PROJECT-mode
pinch, not a fix. Wrap method alone does not explain or resolve this fold.

This means the earlier root-cause hypothesis (ray-miss on a partially-overlapping ring) was
incomplete. The more likely explanation, not yet tested: a single flat 360-degree ring is the wrong
starting shape for a joint where the target only wraps around part of that circle -- no shrinkwrap
mode can cleanly relax a full circle onto a surface it partially misses by design, regardless of
projection rule. A proper fix likely needs the collar's *shape* to change (e.g. an inset cut roughly
matching the target's footprint before the loop is even created), not just its shrinkwrap parameters
-- closer to how real hard-surface tutorials actually cut T-junction holes, and a materially bigger
change than this pass's scope.

## Live cross-validation (2026-08-17, after the live Blender connection came up)

Once a live typed-modeler connection became available mid-session (see the connectivity note
below), the same `treatment` blend was loaded live via `restore_checkpoint` and checked with this
project's own purpose-built diagnostic tool, `get_evaluated_defect_regions` -- independent of the
headless dihedral-angle script. It flagged 147 candidate defect tickets, and the 20 most severe all
cluster at the same seam positions (y around +-0.47-0.48) the headless dihedral-angle sweep already
identified. Two independently-implemented measurements (a from-scratch angle sweep in the lab script,
and this project's own live diagnostic tool) agree on where the defect is. `render_diagnostic_pass`
(live, solid shading) reproduced the same visible pinch as the headless `render_blend_beauty.py`
output -- `live_diagnostic_solid.png`.

**Connectivity note, unrelated to the modeling result but worth recording**: the live connection was
not initially available. The third-party Blender Connector addon's own bridge process
(`mcp__Blender__*` tools) accepted TCP connections but never responded to any request in this
session -- confirmed to be a bug in that specific bridge, not in Blender or its addon, by connecting
directly to the addon's raw socket (port 9876) with a plain Python script and getting immediate,
correct responses to `get_scene_info` and `execute_code`. Used that same working raw-socket path to
inject and start `blender_ops/modeler_server.py` (port 9878) directly inside the already-running
Blender process, which this project's own `mcp__modeler__*` tools talk to directly and which then
worked immediately and reliably.

## Status and next step

This is `EXPERIMENTALLY_TESTED`, not `TRANSFER_VALIDATED` -- reproduced once on the geometry built
specifically for this test, not yet on a second, different shape, and with one identified defect
still open after two genuine (not guessed) diagnostic attempts. Per `docs/KNOWLEDGE_SYSTEM.md`, the
underlying knowledge item status is unchanged (still `CAPTURED`). The Boolean-vs-Shrinkwrap
comparison itself stands (0 vs 24 non-manifold edges) regardless of this open fold. Concrete next
step: redesign the collar as a footprint-matched inset cut rather than a flat full ring, before
attempting a second transfer target on a different shape.
