# Topic coverage matrix

Honest status as of 2026-08-07. ✓ = substantially done, ~ = partial, ✗ = not done. VIDEO is ✗ across
every row for a structural reason, not per-topic laziness: YouTube is confirmed unreachable from
this environment (see `source_registry.json`, source `youtube-general`) and every video source in
the directive's curriculum is YouTube-hosted. This is stated once here rather than repeated as a
caveat on every row.

| TOPIC | DOCS | VIDEO | EXPERIMENT | FAILURE_CASE | QUIZ |
|---|---|---|---|---|---|
| Mesh fundamentals (verts/edges/faces, normals, selection) | ~ | ✗ | ~ (implicit, throughout project history) | ✗ | ✗ |
| Extrude | ~ (used extensively, not freshly doc-read this session) | ✗ | ✓ (pre-existing, this project) | ✓ (pre-existing: ID-theft bug, clear_ids_in_open_bmesh) | ✗ |
| Inset | ~ | ✗ | ✓ (pre-existing) | ✓ (pre-existing: off-center inset limitation) | ✗ |
| Bevel | ✓ (fresh read this session) | ✗ | ✓ (pre-existing) | ✓ (pre-existing: ID interpolation, segments=1 corner-ID loss) | ✗ |
| Loop cut / Subdivide | ~ | ✗ | ✓ (pre-existing: subdivide_selection) | ✓ (pre-existing: mismatched-resolution n-gons, SoapDish rim) | ~ (Q3: correct concept, honestly flagged low confidence on automated pinch detection) |
| Merge / Merge by Distance | ~ | ✗ | ✓ (pre-existing + fresh: curve bevel-cap weld fix this session) | ✓ (pre-existing + fresh: curve cap seam bug) | ✗ |
| Dissolve (verts/edges/faces) | ✗ | ✗ | ✓ (fresh this session) | ~ (behavior differs by element type, documented, not a "failure" per se) | ✓ (Q2, Q13) |
| Delete (VERTS/EDGES/FACES/FACES_ONLY contexts) | ✗ | ✗ | ✓ (fresh this session) | ✗ | ✓ (Q2) |
| Bridge Edge Loops | ✗ | ✗ | ✓ (fresh, 2 real failures + root causes + working case) | ✓✓ (is_boundary/wire-edge gotcha; already-connected no-op) | ✓ (Q11) |
| Fill (triangle fan) | ✗ | ✗ | ✓ (fresh this session) | ✗ | ✗ |
| Grid Fill | ✗ | ✗ | ✓ (fresh, real limitation found) | ✓ ("Connecting edge loops overlap" on a multi-segment grid hole) | ✓ (Q12) |
| Bisect | ✗ | ✗ | ~ (fresh, clear_inner/outer not yet tested) | ✗ | ✗ |
| Spin | ✗ | ✗ | ✓ (fresh this session) | ✗ | ✗ |
| Split vs Separate | ✗ | ✗ | ✓ (fresh, real distinction confirmed) | ✗ | ✓ (Q9) |
| Symmetrize | ✗ | ✗ | ✓ (fresh, incl. one caught+fixed enum-value mistake) | ✓ (enum value error) | ✗ |
| Vertex/Edge Slide | ✗ | ✗ | ✓ (fresh this session) | ✗ | ✗ |
| Rip | ✗ | ✗ | ✗ (attempted, failed) | ✓ (rip.poll() requires real mouse/viewport context, unusable headless) | ✓ (Q13) |
| Normals / face orientation | ~ | ✗ | ✓ (pre-existing + fresh confirmation) | ✗ | ✗ |
| Shade Smooth/Flat | ✗ | ✗ | ✓ (fresh this session) | ✗ | ✗ |
| Topology fundamentals (poles, edge flow) | ~ (implicit via project's own valence/pole judgment work) | ✗ | ✓ (pre-existing, SoapDish/SpeakerEnclosure) | ✓ (pre-existing) | ✓ (Q1, Q6, Q10) |
| Subdivision Surface modifier | ✓ | ✗ | ✓ (pre-existing, SoapDish milestone) | ✓ (pre-existing: mismatched-resolution n-gons) | ✓ (Q3, Q4) |
| Boolean modifier | ✗ | ✗ | ✗ | ✓ (pre-existing: groove-cut cleanup skill) | ✓ (Q8) |
| Mirror modifier | ✗ | ✗ | ✗ | ✗ | ✓ (Q7) |
| Modifier stack order (Mirror/Bevel/Boolean/Subdiv/Solidify pairs) | ✗ | ✗ | ✓ (all 4 directive-listed pairs: Mirror+Bevel, Boolean+Bevel, Mirror+Subdivision, Solidify+Bevel) | ✓✓✓ (Mirror+Bevel: seam-carving artifact; Mirror+Subdivision: 16 non-manifold edges, genuinely broken in the wrong order; Solidify+Bevel: wrong order makes Bevel a no-op) | ✓ (Q4, Q7) |
| Retopology fundamentals | ✗ | ✗ | ~ (pre-existing: Mug retopo session, not curriculum-driven) | ✗ | ✗ |
| Reference blockout | ✓ (Image Empty page) | ✗ | ~ (pre-existing, gadget v1/v2 -- v1 rejected, v2 measured) | ✓ (pre-existing: v1's eyeball-then-check failure, root-caused and fixed in v2) | ✓ (Q10) |
| Curve objects (bevel_depth, taper_object) | ~ (API-level, not the dedicated Manual page) | ✗ | ✓ (pre-existing, curve_ops.py this session) | ✓ (pre-existing: cap-weld bug) | ✗ |

## Honest summary

This is genuine, real progress on the reproduction/failure-case axes -- roughly 15 operations got a
fresh, verified Blender reproduction this session, several with real, non-obvious failure modes
found and root-caused (bridge_loops + wire edges, grid_fill's overlap limit, rip's context
requirement). It is **not** a completed foundation gate. DOCS coverage is shallow (a handful of
Tier A pages, not the systematic full-manual walk the directive describes), and VIDEO coverage is
zero across the board for a real, structural, already-investigated reason.

**QUIZ update**: `quizzes/quiz_001.md` answered the directive's 10 example questions plus 3
session-specific ones, from understanding rather than by re-reading the operator cards while
composing. One honest low-confidence result surfaced, not smoothed over: correct conceptual
understanding of support-loop spacing and pinching (Q3), but explicitly low confidence on
automated pinch detection, consistent with `evaluated_defect_regions`'s own documented limitation
in code. See `foundation_exit_report.md` for the overall honest PASS/PARTIAL/FAIL status.
