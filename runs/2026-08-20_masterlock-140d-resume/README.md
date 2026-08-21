# MasterLock 140D — resuming the stalled reference-driven build

This is the project's single highest-priority open gap: no validated skill has ever fired during a
real reference-driven build carried through to human review. The mallet and mug-handle-join builds
(2026-08-20) proved technique on known/authored forms; this is the first attempt at the actual
reference-driven case since the magnifying-glass purge.

## What this run is, and isn't

Not a new build. `runs/2026-08-16_reference-gathering-masterlock-140d/` reached stage 12
(connected-body construction) with `decision_revision: 11` — real typed-transaction history, not
batched/scripted shortcuts — then stopped without being purged or rejected; it simply has no formal
status anywhere in `knowledge/foundation/benchmark_readiness.json` or the curriculum docs.
`masterlock_current.blend` here is an exact copy of that stage-12 state (`brass_body`: 20 verts, 1
Bevel modifier, `Smooth by Angle`; `steel_shackle`: a 6-point BEZIER curve, `bevel_depth=3.0`).

## The mandatory first check: material-lit rendering

Every stage_XX evidence file in the original run directory is flat/solid Workbench shading. The
magnifying-glass, mallet, and mug-handle-join builds all had real defects invisible in flat shading
that only appeared under material lighting — so the existing stage-12 evidence could not be trusted
as clean without actually checking it that way, which had never been done.

`view_front_material.png`, `view_iso_material.png`, `view_side_material.png` (via
`tools/render_blend_beauty.py`, `material` mode) plus `wireframe_brass_body_front.png` and
`wireframe_steel_shackle_front.png` (via `blender_ops/render_passes.py`'s `render_diagnostic_pass`)
are the first material-lit and wireframe views this build has ever had.

**Result: no shading defects found.** `steel_shackle`'s wireframe is an evenly-gridded quad tube
with no pinching; `brass_body`'s wireframe shows exactly the sparse two-loop-cut band the stage-12
README described, correctly positioned. This rules out the failure mode that sank the magnifying
glass and needed fixing on the mallet and mug.

## Real gaps found by comparing against the reference photos directly

Checked against `masterlock_140d_front.jpg` / `masterlock_140d_official.jpg`, not assumed clean
because the topology passed:

1. **No socket at the shackle/body junction.** The reference shows a visible round collar where the
   steel shackle enters the brass body — a real material/component boundary. The current render
   shows the shackle tube's rounded end-cap simply resting flush on the flat top face (its lowest
   bezier point sits exactly at `z=16`, the body's top surface) with no recess at all. This matches
   what `reference_to_blockout_contract.json` already declared as an unbuilt relationship ("shackle
   legs seat into two top sockets") — confirmed still outstanding, not a new finding, but now
   confirmed under real lighting rather than assumed from the informal stage notes.
2. **Missing front corner chamfer.** The reference has a large, deliberate 45° diagonal facet across
   the front-left body corner — a distinct design element, not a small edge bevel. The current body
   has only small uniform bevels on all corners; that facet doesn't exist. This one was not named in
   `reference_plan.md`'s remaining scope — found only by re-comparing the render against the photo
   just now.

Exact geometry queried live from the saved file for the socket work: body is `40 x 16 x 32 mm`
centered at the origin (top face at `z=16`); shackle legs are at `x=-13.5` and `x=13.5`, `y=0`,
`bevel_depth=3.0` (6 mm diameter, matching the official spec).

## Why construction stops here this session

Building the socket correctly means cutting a real circular opening into a flat ngon-bounded face
and rebuilding clean quad topology around it, without a boolean — booleans are a proven failure
class in this project (the magnifying-glass neck/ring join, the scrapped Shrinkwrap+Bridge
cylinder-join reproduction). That is genuinely nontrivial bmesh work, not a same-session edit
alongside a full research-and-comparison pass, and this project's own history (six rounds to get
`extrude_selection` right; two iterations each for the mallet's shading fix and the mug's
cross-section-shear fix) shows this class of operation deserves its own focused, iterative attempt
rather than being rushed to close out a session.

## Socket construction (decision_revision 11 -> 12)

Built through a real `DecisionTransaction` (`ADD_SHACKLE_SOCKETS`), not a raw script edit outside
the tracked system. Technique: `bisect_plane` only, never inset+bevel or boolean --

1. Local frame cuts isolate a square region around each socket center, restricted each time to just
   that region's own current geometry (an early attempt that passed the whole top plane let the
   cuts ripple across the entire top face).
2. 12 tangent-plane bisects around the target radius carve a regular 12-gon hole. An earlier attempt
   used `inset_individual` + vertex-bevel instead; that silently clipped a corner off the
   *neighboring* ring faces too, because bmesh vertex-bevel affects every face touching an edge at
   the target vertex, not just the one face you meant to round. Pure bisect has no such side effect.
3. The resulting 12-gon's vertices are projected exactly onto the target circle (a bisect polygon is
   circumscribed, slightly larger than the true circle otherwise).
4. Extrude the circle face down 2 mm for the recess floor, then explicitly delete the original face
   -- `extrude_face_region` does not consume it, and leaving it in place produces non-manifold edges
   (the exact bug already diagnosed once in `mesh_ops.extrude_selection`'s own docstring; re-found
   here independently on first attempt, fixed the same documented way).

First attempt (`SOCKET_RADIUS=3.5`) was structurally clean but visually too subtle to read as a
collar against the shackle's own 3 mm tube radius; second attempt confirmed a real process mistake
along the way -- a debug script that modified geometry in memory but never called
`save_as_mainfile`, so two render passes silently re-rendered the same untouched file and looked
identical, which could easily have been misread as "the parameter change had no effect" if not
caught. Final version uses `SOCKET_RADIUS=4.2`, which reads clearly as a distinct collar in the iso
render, matching the reference photo's junction. `brass_body` carries no SubD modifier, so this
region's flat n-gon wedges (the frame material between the circle and the outer square, from the
tangent cuts) carry no shading risk -- the concern that makes n-gons dangerous elsewhere in this
project doesn't apply to a planar, non-subdivided face.

Fresh check after commit: 0 non-manifold edges, 0 degenerate faces, 0 loose vertices. Full test
suite unaffected (233 passed).

## Status

Sockets built and verified. **Not yet done**: the front corner chamfer (the second gap found against
the reference, a 45-degree facet, still not built) and a fresh full-view human review of this
socket work specifically -- the renders here are my own inspection, not a substitute for that. No
claim of "done," "fixed," or "clean" beyond what these renders actually show.
