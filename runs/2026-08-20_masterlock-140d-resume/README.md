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

## Front corner chamfer (decision_revision 11 -> 12) and a rebuild after a real defect

Closed the second gap found against the reference: a narrow (~3.5 mm) flat facet at the front-left
vertical corner. A close crop of the reference photo confirmed it's a genuine third facet (a small
manufacturing chamfer), not just a specular highlight on a normal box corner -- and considerably
narrower than first guessed ("large 45-degree facet" was an overstatement from the initial read).

Getting a *watertight* cut here took real diagnosis, all against a mesh with a pre-existing
delicate detail right at that same corner (the stage-12 recessed front seam band, only 0.15 mm
wide): `bisect_plane(..., clear_outer=True)` deletes the cut-off material but does not fill the
newly exposed boundary with a face -- found live as non-manifold edges even on the simple
pre-socket mesh, nowhere near the sockets. `bmesh.ops.edgenet_fill` on the returned `geom_cut`
edges closes it correctly, including the small notch where the cut crosses the seam band.

**Rebuilding the sockets on top of the chamfer surfaced a second, more serious defect**, this one
purely visual: a diagonal shading crease across the otherwise flat front face, in the material
render only -- 0 non-manifold edges, 0 degenerate faces, perfectly planar vertices, every
structural check clean. Root cause, found by direct inspection rather than assumption: the socket
frame's X-direction bisect cuts were restricted to "the whole top plane" but not to the local
socket area, so they reached all the way to the front/back wall's *shared* boundary edge at
y=+-8 and split it -- splitting a shared edge splits it for every face using it, not just the top
face, silently fragmenting the front and back walls into 7-8 sided flat n-gons. A second,
independent bug compounded it: `shade_smooth_by_angle` bakes custom split normals at the moment
it's called rather than living as an updating modifier on this object, so even after any fix, new
bmesh geometry keeps stale normals until it's explicitly re-applied.

Both are now fixed at the root: the frame cuts run Y-direction first (safe by position, since
y=+-5 never reaches y=+-8), *then* X-direction restricted to the resulting middle band, which no
longer touches the wall boundary at all; and `object_ops.set_smooth_by_angle` is re-applied inside
both construction steps, immediately after `_write_back`, not deferred as an afterthought. Verified
directly: `brass_body`'s front and back walls are clean 4-vertex quads again.

## Status

Chamfer and sockets both built and committed through real `DecisionTransaction`s
(`decision_revision` 11 -> 12 -> 13), structurally clean (0 non-manifold, 0 degenerate, 0 loose
verts) and, this time, actually verified clean under material rendering after the fixes above --
not assumed clean from a passing structural check. Full test suite unaffected (233 passed).

**Not yet done**: a fresh full-view human review of this specific work -- the renders here are my
own inspection, not a substitute for that. No claim of "done," "fixed," or "clean" beyond what
these renders actually show.

## Fresh measured silhouette comparison against the reference photo

The last IoU numbers on file for this build (stage 08, `silhouette_iou: 0.8618`) predate today's
chamfer and socket work entirely. Re-ran the same methodology (`tools/compare_reference_render.py`,
`uniform-bbox` alignment, against the same `stage_06_front_segmentation/reference_silhouette.png`)
on the current geometry rather than assuming construction progress also means measured progress.
Two mask-detection pitfalls hit along the way, both already-documented failure modes in this
project's own history, re-found independently: `--reference-mask-mode auto` treated the whole
segmented-reference image as foreground (the exact bug stage 06's own README already flagged once,
"incorrectly treated the whole image as foreground"), and `--candidate-mask-mode light-background`
did the same to the candidate render, because `render_blend_beauty.py` renders with
`film_transparent=True` -- the white background an image viewer shows is composited alpha, not the
actual light RGB a background-threshold check needs. The render script's own comment already says
the alpha channel *is* the exact silhouette; using `--candidate-mask-mode alpha` fixed it.

| Metric | Stage 08 (pre-chamfer/socket) | Current | Direction |
| --- | ---: | ---: | --- |
| Silhouette IoU | 0.8618 | 0.8583 | flat (-0.0035) |
| Negative-space IoU | 0.7190 | 0.7188 | flat (-0.0002) |
| Bounding-box error | 0.00371 | 0.00442 | flat (+0.00071) |
| Symmetric contour error | 0.00740 | 0.00775 | flat (+0.00035) |

Honest reading: today's work did not move these numbers, and shouldn't have. The chamfer is a
corner facet within the existing bounding envelope, and the sockets are a recess into the surface
-- neither changes the outer silhouette a front-view outline measure can see. This construction was
detail/surface work, not a proportion or component-shape correction, and the measurement confirms
that rather than being contradicted by it. The actual bottleneck this table cannot move on is still
what `docs/CURRENT_STATE_GAP_MATRIX.md` already names: proportion and component fidelity, which
these two decisions never touched.

Full report: `silhouette_comparison/comparison.json`.

## Why the negative-space gap (0.719 IoU) should not be chased by narrowing the shackle

`negative_space_iou` (0.719) trails `silhouette_iou` (0.858) by a wide enough margin to be worth
investigating on its own -- stage 06's README already flagged it once ("the shackle opening remains
the material localized mismatch") and it never actually closed. Measured the row-by-row outer and
inner (hole) width of both masks directly: at the arch's widest row, the candidate's negative-space
width is ~20% wider than the reference's, versus only ~8% wider on outer width -- a real,
disproportionate mismatch, not noise.

The obvious-looking fix is to narrow the shackle legs. **Did not do this.** The current leg
centerlines (`x = +/-13.5mm`) aren't a photo-fitted guess -- they're set to reproduce the official
21mm clearance specification exactly, and `reference_manifest.json` explicitly labels the photo
this comparison is measured against as `front_right_oblique`, `projection: PERSPECTIVE`, not
orthographic. `docs/REFERENCE_COLLECTION_PROTOCOL.md` is direct about this exact situation:
"Photographs are not orthographic drawings... Use photographs for visual evidence and
orthographic/dimensional sources for proportions. Do not directly trace a perspective photograph as
if it were an orthographic projection." Narrowing a dimensionally-anchored shackle to better match
one perspective-distorted photo's pixel silhouette would be trading a verified real-world
measurement for a worse one, in the direction the pixel metric happens to reward.

This is a real limit of the current reference set, not a construction defect: a true front-on
orthogonal photo (or a second corroborating angle) would be needed before the negative-space gap
could be diagnosed as shape error versus perspective artifact with any confidence. Recorded here so
a future session doesn't rediscover the same tempting-but-wrong fix.

## Human review board

`review_board/review_board.html` -- a self-contained (embedded images, no external requests)
primary-form review package: both reference photos, front/side/3-4 model renders, per-object MatCap
and wireframe evidence, the measured-comparison table and silhouette overlay above, known
uncertainties, and 8 structured review questions (not "does this look good"). Matches
`docs/HUMAN_VISUAL_REVIEW_PROTOCOL.md`'s stance that a human rejection is first-class evidence never
overwritten by a passing metric -- this package is the input to that review, not a substitute for
it. No review has been recorded against it yet.
