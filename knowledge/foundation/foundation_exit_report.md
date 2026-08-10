# Foundation exit report

**Updated:** 2026-08-10

**FOUNDATION STATUS: PARTIAL**

**READY FOR HELD-OUT MODELING: NO**

This report reflects repository evidence through `runs/2026-08-10_visual-comparison/`. It is not a claim that the complete professional-modeling curriculum is finished.

## Evidence summary

### Official documentation

Studied Tier A material includes:

- Subdivision Surface modifier.
- Bevel Edit Mode operation.
- Bevel modifier.
- Mirror modifier.
- Boolean modifier.
- Solidify modifier.
- Empties/Image Empty reference workflow.
- Mesh Editing operator index.
- Parts of the BMesh operators API.

`manual_modeling_walk.md` now maps every major modeling branch to official sources, evidence, and explicit open work. This closes the prior navigation gap but does not claim exhaustive study of every child page. Retopology, real brush sculpting, complex UV/export work, and less common modifier/API options remain incomplete.

The accessible Bevel modifier Manual is labeled Blender 4.5 LTS, while the newest lab ran in installed Blender 5.2.0 LTS. Records preserve that version distinction.

### Controlled experiments

Approximately 110 controlled/reproduction cases are now recorded:

- Roughly 27 prior operator and modifier-order cases.
- Ten standalone Bevel/Mirror variants in `runs/2026-08-10_modifier-foundation/`.
- Twelve standalone Boolean/Solidify variants in `runs/2026-08-10_boolean-solidify-foundation/`.
- Six curved Solidify second-shape variants in `runs/2026-08-10_solidify-transfer/`.
- Seven cylindrical Bevel/Mirror second-shape variants in `runs/2026-08-10_bevel-mirror-transfer/`.
- Ten Array/Shrinkwrap/Simple-Deform/retopology variants in `runs/2026-08-10_array-deform-retopology/`.
- Thirteen contextual topology/SubD specimens in `runs/2026-08-10_topology-subd/`.
- Ten UV/material/sculpt/production records in `runs/2026-08-10_uv-material-sculpt/`.
- Nine modeler-relevant BMesh/API records in `runs/2026-08-10_bmesh-api/`.
- Three fixed-frame visual variants compared across front, side, and top in `runs/2026-08-10_visual-comparison/`.
- One actual Sculpt Mode brush mutation and two export/import round trips in `runs/2026-08-10_sculpt-export/`.

Prior experiments cover dissolve/delete, bridge/fill/grid fill, bisect, spin, split/separate, symmetrize, slides, shading, and four modifier-order pairs. Project history also contains production use of extrude, inset, bevel, subdivision, booleans, curves, and retopology.

The standalone modifier lab added:

- Bevel `NONE` versus `ANGLE` limiting on triangulated planar faces.
- Bevel segment-count density comparison.
- Excessive Bevel width with Clamp Overlap enabled/disabled.
- Mirror exact seam, below-threshold seam failure, larger-threshold repair, and Bisect behavior.

The Boolean/Solidify lab added:

- Exact Difference, Union, and Intersect volume/topology comparisons.
- Manifold-solver Difference comparison.
- A reproduced tangent-groove Boolean failure with 90 n-gons and 18 degenerate faces.
- Solidify Fill Rim on/off and Offset -1/0/+1.
- Unapplied versus applied non-uniform-scale thickness measurement.

The curved Solidify transfer confirmed the scale warning on a different shape, compared five thickness modes, disproved two simplistic mode-ranking hypotheses, and exposed the need for closest-surface/normal-projected thickness metrics.

The cylindrical Bevel/Mirror transfer reproduced the Merge Distance dependency on a curved seam, showed unapplied Z scale doubling the measured world-space bevel band, and disproved the universal form of the earlier Mirror/Subdivision order rule: both orders were manifold on the exact-seam half-cylinder.

The Array/deform/retopology lab confirmed additive array offsets and local-scale effects, reproduced a wrong-direction Shrinkwrap no-op, exposed a Simple Deform API amount-reset pitfall, showed low-density Twist creating four degenerate faces, and conformed a 42-vertex cage to a 1,984-vertex target. Its first two failed designs remain documented and were corrected through stronger controls.

The topology/SubD lab compared pole valences, flat versus curved triangle/n-gon contexts, edge-spacing variation, support-loop width, cylindrical routing, and loop termination. It quantitatively showed that all-quads can still have poor density, while triangles/poles on flat surfaces can remain planar; the two closed support specimens independently verified clean.

The UV/material/sculpt lab quantified the non-uniform-scale unwrap warning, reproduced node-versus-material metadata divergence and orphan slots, exercised Multires and Voxel Remesh, and validated a minimal production-organization audit. Remesh retained populated UV data in Blender 5.2, but semantic correspondence remains unproven and is not credited as production-ready UV preservation.

The BMesh/API lab covered ownership/write-back, lookup-table requirements, duplicate and degenerate cleanup, triangulation mappings, dissolve selection scope, normal repair, custom UV data, and selection flushing. It preserved a broad Limited Dissolve over-deletion and two API-assumption crashes rather than counting operator calls as success.

The visual-comparison lab fixed camera framing from the reference bounds and improved mean three-view silhouette IoU from 0.739 to 0.979 while reducing normalized contour error by about 90%. Every view improved and the corrected evaluated mesh independently verified clean. Because the reference and correction parameters share one synthetic lab generator, this is capability evidence, not held-out modeling evidence.

The interactive sculpt/export lab used a real `VIEW_3D` context and Draw brush, moving 248 of
2,562 vertices with measurable displacement. OBJ and GLB were exported then re-imported with
matching bounds, triangulated surface coverage, UV presence, and material presence. A failed GLB
raw-count assertion is preserved: glTF legitimately triangulated polygons and split attribute
vertices, so format-invariant verification replaced exact raw-count equality.

All seven Bevel/Mirror assertions and all nine Boolean/Solidify assertions passed. See the respective run reports and saved `.blend` scenes for evaluated measurements.

### Failure cases

Meaningful failures or limitations include:

- Bridge-loop wire-edge filtering causing a silent no-op.
- Grid Fill overlap failure on an unsuitable hole.
- Rip operator context failure in headless mode.
- Mirror-before-Subdivision producing non-manifold evaluated geometry in the original flat-seam stack, while a later curved exact seam remained manifold in both orders.
- Bevel-before-Solidify being a no-op on a single plane.
- Mirror seam outside Merge Distance leaving eight boundary/non-manifold edges.
- Excessive Bevel width with Clamp Overlap producing nearly collapsed edges despite remaining manifold.
- Tangent torus/cylinder Boolean Difference producing 90 n-gons, 18 degenerate faces, and a zero-length edge while remaining manifold.
- Solidify with Fill Rim disabled leaving eight boundary/non-manifold edges.
- Unapplied non-uniform Z scale doubling requested Solidify world thickness.
- Wrong-direction Shrinkwrap projection leaving every source vertex unchanged.
- Low-density 180° Simple Deform Twist producing four degenerate faces.
- Setting both Simple Deform `angle` and `factor` silently resetting the mode amount to zero in the lab helper.

Failures remain visible and are not counted as successes merely because Blender returned without an exception.

### Retrieval and knowledge use

- `quizzes/quiz_001.md` contains 13 answers; `quiz_002.md` adds 15 fresh mechanism/evidence answers in a second same-day pass.
- Modifier-order findings cover all four planned pairs, not two.
- One stack-order skill has been promoted with experimental evidence.
- Several project skills have prior runtime use, but cross-asset and second-shape validation is still sparse.

Structured retrieval returned the expected top skill in five of five context-rich cases. One retrieved material-slot skill was then used in Blender as a single mutation, reducing measured orphan slots from one to zero with revision-linked telemetry and independent verification. Multi-day retention and broader production runtime use remain unmeasured. The prior low-confidence area—automated pinching/curvature diagnosis—remains open.

An inspectable strategy policy now ranks primary representation, component boundaries, edit mode,
and repair-vs-rebuild independently. Its declared benchmark passed 10/10 cases and preserves a real
CLI import-context failure and fix. Because cases live beside the runner, this is policy-level
regression evidence rather than held-out judgment.

### Video and structured training

No complete external video lesson has been studied. Historical attempts could not access YouTube modalities and correctly did not claim video understanding. Legal local ingestion is now implemented and exercised on a project-owned six-second MP4 with a real video stream, audio stream, WebVTT captions/transcript, and six timestamped frames (`runs/2026-08-10_video-ingestion/`). This validates modality handling, not expert curriculum knowledge. User-provided or otherwise permitted external lessons remain future evidence.

The source registry is normalized to explicit URL/local path, creator, type, trust tier, version, topics, access booleans, status, and rejection reason. Approved-root document ingestion, approved-host web fetching, structured skill retrieval, append-only skill telemetry, explicit uncertainty, multi-view regression checks, component-graph checks, and rebuild pressure are implemented with unit tests. Runtime and cross-session evidence remains sparse.

No paywalled course is claimed as lesson-level study; only accessible curriculum/overview text was inspected.

## Stronger areas

- Closed-loop transaction and recovery infrastructure.
- Persistent geometry identity and live state probing.
- Core mesh operations used in production and controlled labs.
- Subdivision and contextual topology fundamentals.
- Modifier-order reasoning across four tested pairs.
- Standalone Bevel/Mirror fundamentals.
- Standalone Boolean/Solidify fundamentals, Boolean cross-asset runtime transfer, and Solidify curved second-shape transfer.
- Honest failure recording and independent technical verification.

## Largest remaining gaps

1. Real production retopology with deformation-aware transfer.
2. Multi-stroke form sculpting, complex UV/textures, and target-engine export evidence.
3. Multi-day retention and broader real-session use of context-aware knowledge retrieval.
4. Visual surface judgment beyond silhouettes, especially pinching/highlight flow, landmarks, and negative space.
5. Held-out modeling that tests strategy and visual loops without benchmark-specific builders.
6. An external permitted video/tutorial lesson studied through the validated local-ingestion path.

## Exit decision

The foundation remains **PARTIAL**. Experiment count and one completed quiz are meaningful evidence, but breadth, repeated retrieval, runtime use, second-shape transfer, and visual judgment remain below the gate.

## Highest-value next step

Complete systematic Manual/API breadth and the retopology/sculpt/UV/material foundation labs, then run repeated retrieval and visual-surface evaluation. Keep them separate from held-out benchmark assets.
