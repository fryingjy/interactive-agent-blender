# Foundation exit report (interim, not final)

**FOUNDATION STATUS: PARTIAL**

This is an honest interim checkpoint after one focused session of foundation-gate work, not a
claim that the gate is complete. Per the directive's own rule ("Mark YES based on demonstrated
understanding," not source count), this report marks the gate NOT yet passed.

## Coverage

**Official modeling manual coverage:** Shallow. Fetched and read: Subdivision Surface Modifier,
Empties (Image reference workflow), Editing Mesh Objects (operator index), Bevel. Not yet
systematically walked: the full mesh-editing branch, modifier root beyond Subsurf, sculpting
root, UV root, materials root.

**Official mesh-editing coverage:** Partial. See `topic_coverage_matrix.md` -- roughly 15
mandatory operations got a fresh, real Blender reproduction this session (dissolve/delete,
bridge/fill/grid_fill, bisect, spin, split/separate, symmetrize, slides, rip, shading). Several
already had strong pre-existing coverage from this project's prior work (extrude, inset, bevel,
subdivide, merge_by_distance) via real production use, not curriculum study.

**Official modifier coverage:** Weak outside Subdivision Surface (well-covered via SoapDish) and
Boolean (well-covered via a real, promoted skill from prior work). Bevel modifier (the
non-destructive version, distinct from the Bevel tool), Mirror, Solidify, and stack-order pairs
are not yet studied or tested.

**Python/BMesh documentation coverage:** Partial. Read the bmesh.ops API page (truncated, not the
full page) plus cross-referenced a WebSearch for grid_fill's real signature. Have not
systematically covered bpy.context/bpy.data/evaluated_get/handlers/timers as a block, though this
project's own code already uses several of these correctly (evaluated_probe.py, modeler_server.py
event handlers) from prior empirical work, not fresh doc study this session.

**Structured courses studied:** 0 lesson-by-lesson. CG Cookie's course overview page was read
(real curriculum structure, author credentials, review consensus) but actual lesson content is
paywalled/login-gated and video-based -- genuinely inaccessible, not skipped.

**Videos studied:** 0, structurally, not from lack of effort. See `source_registry.json`'s
`youtube-general` entry: YouTube is confirmed unreachable from this environment via two
independent tools (Browser, WebFetch), both redirected to a Google bot-check page. This affects
every video source in the directive's curriculum equally (Blender Studio Fundamentals, CG Cookie
lessons, Blender Secrets tips). Not attempted to bypass -- prohibited regardless of purpose. No
video source in this report claims `video_frames`/`audio`/`captions`/`transcript` access it does
not have.

**Experiments completed:** ~19 distinct reproduction experiments this session (dissolve_verts,
dissolve_edges, dissolve_faces, delete VERTS context, delete FACES_ONLY context, bridge_loops x3
attempts, triangle_fill, grid_fill x3 attempts, bpy.ops.mesh.fill_grid simple case, bisect, spin,
split, separate, symmetrize, vertex_slide, edge_slide, rip (failed), face-normal recalc,
shade_smooth) plus several more already-verified from this project's prior sessions (extrude,
inset, bevel corner-ID behavior, subdivide resolution-mismatch, curve bevel-cap weld).

**Failure-case experiments:** A genuine, real handful, not manufactured: bridge_loops on
wire-edge rings filtered by `is_boundary` (silent no-op, root-caused to is_boundary requiring
exactly 1 face), grid_fill on a multi-segment grid hole ("Connecting edge loops overlap", a real
Blender-reported error, not silent), rip's `poll()` failure in headless context, one caught+fixed
Python enum-value mistake (symmetrize direction).

**Topics with strong retrieval:** Bevel corner-ID behavior, bridge_loops' is_boundary gotcha,
grid_fill's real limitation, split-vs-separate distinction, rip's headless-context limitation --
each has a concrete, falsifiable, tested finding, not a vague impression.

**Topics still weak:** Everything sculpt/UV/materials-adjacent (not touched at all), modifier
stack-order interactions (not tested), Bevel modifier vs Bevel tool distinction, full mesh
fundamentals doc coverage, any quiz-style retrieval check (not attempted).

**Candidate skills:** None newly promoted from this session's experiments (the reproduction work
this session was foundational/exploratory, not yet distilled into the project's `knowledge/skills/`
executable-skill format). The grid_fill limitation and bridge_loops gotcha are strong candidates
for a future skill entry once tested on a second case, per this project's own promotion
discipline (CANDIDATE requires more than one data point before EXPERIMENTALLY_TESTED).

**Contradicted claims:** None yet identified against this project's prior documented knowledge.

**Rejected/weak sources:** `youtube-general` (Tier D by inaccessibility, not by content quality --
unreachable), `blenderguru-donut-v5-page` (link wrapper, no independent written content).

**Known knowledge gaps:** Sculpting, UV unwrapping, materials, modifier stack-order rules,
retopology as a deliberate curriculum (only ad hoc prior use), Bevel modifier specifically,
quiz-based retrieval validation (not attempted at all).

## READY FOR HELD-OUT MODELING: NO

Not because nothing was learned -- real, falsifiable, tested findings exist and are recorded
above and in `knowledge/foundation/operator_cards/`. Because the gate's own checklist (systematic
manual walk, modifier stack-order testing, quiz-based retrieval checks, 25+/10+ experiment
targets) is only partially met. This report should be revisited and extended in a future session
rather than treated as final.
