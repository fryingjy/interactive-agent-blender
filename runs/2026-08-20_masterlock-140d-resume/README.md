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

## Status

In progress, honestly assessed, not advanced past stage 12. Next concrete step: construct the two
shackle sockets (clean quad topology, no boolean, sized to the shackle's 6 mm diameter plus a small
visible clearance, shallow recess only — not a through-hole, since the internal locking mechanism is
explicitly out of evidence and out of scope) as one verified `DecisionTransaction`, then the front
corner chamfer as a separate decision. No claim of "done," "fixed," or "clean" beyond what these
renders actually show.
