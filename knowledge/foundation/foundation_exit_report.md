# Foundation exit report

**Updated:** 2026-08-10

**FOUNDATION STATUS: PARTIAL**

**READY FOR HELD-OUT MODELING: YES — benchmarks B and D passed; six references remain reserved**

This report reflects all listed repository evidence through the 2026-08-10 completion audit. It is not a claim that the complete professional-modeling curriculum is finished.

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

Approximately 156 controlled/reproduction cases are now recorded:

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
- Five Blender-native diagnostic visual passes and strict stage-gate attempts in `runs/2026-08-10_visual-passes/` and `runs/2026-08-10_stage-quality/`.
- Four clean/pinched/uniform/wavy surface specimens in `runs/2026-08-10_surface-diagnostics/`.
- Fifteen expanded typed-operation/registry/transaction cases in `runs/2026-08-10_expanded-typed-ops/`.
- One semantic selected-region render/stale-region case in `runs/2026-08-10_semantic-region-render/`.
- Seven documentation-crawl/session-learning assertions in `runs/2026-08-10_learning-system/`.
- One multi-channel transaction rejection stress case with eight assertions in `runs/2026-08-10_transaction-rollback/`.
- One actual brush-sculpt retopology handoff and one deformation-density comparison in `runs/2026-08-10_sculpt-retopo-deformation/`.
- One packed tangent-normal/PBR GLB round trip with source and imported-state verification in `runs/2026-08-10_pbr-normal-export/`.
- Nine secondary-modifier cases for Screw, Remesh, Decimate, Triangulate, three smoothing workflows, Curve, and Lattice in `runs/2026-08-10_secondary-modifiers/`.
- One Blender runtime-API lifecycle case covering context/data, RNA types, dependency-graph evaluation, handlers, timers, and message bus in `runs/2026-08-10_blender-runtime-api/`.

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

The visual channel now includes solid, evaluated-wireframe, world-normal, depth, and component-mask
passes tied to scene/camera metadata. Two blank/face-retaining wireframe failures are preserved.
Strict forward stage transitions reject weak evidence without mutating persistent Blender state.
Professional readiness aggregation currently fails hard surface/reference/generalization gates,
preventing clean technical meshes or synthetic IoU from being misreported as professional quality.

Evaluated-surface diagnostics now sharply separate a local sphere pinch and repeated cylinder
waviness from their controls using scale-normalized Laplacian concentration and sign oscillation.
They remain candidate evidence because intentional hard cap transitions also score strongly; this
limitation is measured and exposed through the typed evaluated-state response.

The protocol 0.2 mutation registry now includes thirteen additional selection-driven operations,
including bridge, spin, loop-cut equivalent, bisect, symmetry, split, and separate. A real
transaction preserved surviving IDs and assigned all new loop-cut IDs; separate rollback restored
the source and removed its created object. BMesh return-key and symmetrize-direction failures remain
visible rather than being counted as first-try success.

Persistent face regions can now be rendered against base-cage context and stale IDs are rejected
before output. An edge-on false-positive image is preserved; final validation requires substantial
target/context color pixels. Contour, negative-space, landmark, and component errors can now become
localized priority tickets rather than only global metrics.

Approved-root local documentation crawling now follows links, deduplicates canonical/content
duplicates, and reports queue exhaustion versus page-limit truncation. Session mining processed
165 real decisions without auto-promoting findings; one repeated bevel candidate was replayed on a
different independently clean asset and marked replay-validated. A literal expected/observed string
comparison failure is preserved.

Transaction rejection now restores geometry, transforms, UVs, materials, modifier state,
semantic/custom metadata, selection, and active-object state while leaving the decision revision
unchanged. It also retains operation-created-object removal. Snapshot cleanup ordering and Blender
5.2 UV-collection API failures are preserved in the run report rather than hidden.

The actual brush-sculpt source now has an independently clean low-cage handoff, and a controlled
70-degree bend shows quantitatively that adequate axial loops preserve changing form better than a
sparse cage. This closes the introductory handoff/deformation evidence gap but not production
anatomy, rig weighting, or multiple organic shape-family transfer.

A packed Non-Color tangent normal texture, normal-map shader chain, roughness, UVs, bounds, and
triangulated surface now survive a GLB round trip. Independent verification keeps the editable
source clean while explicitly failing the seam-split imported glTF mesh as editable topology; the
delivery result is not confused with the source asset.

All nine secondary modifiers named by the curriculum now have controlled Blender 5.2 evidence.
Direct latest Manual child-page fetches returned HTTP 402, so the source record distinguishes
official indexed excerpts from exhaustive study. Corrective Smooth/Curve/Lattice production
transfer and all second-shape claims remain open.

The modeler-relevant API block now also covers context/data authority, Mesh/Object/Modifier RNA,
dependency-graph evaluation, handlers, timers, message bus, and registration cleanup. Background
execution does not yield asynchronous notifications, so registration lifecycle is credited but
automatic event delivery is not.

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

Nine complete official Blender lessons were ingested through the approved-root pipeline: Modeling
Introduction, Extrude, Bevel Tool, UV Unwrapping, Intro to Sculpting, and Planning the Facial
Retopology, Three Point Lighting, Snow - Stylized Character Retopology Live #2, plus Intro to
Shading. They provide 11,617.988 seconds of real video/audio and 119 decoded frame samples
(`runs/2026-08-10_online-lessons/`). The first four use CC BY 3.0 Wikimedia mirrors; the sculpt
retopology, and lighting lessons are free official Blender Studio sources with 650 authored-caption segments. Local
machine transcription/caption sidecars supplied 4,838 timestamped segments where creator captions were absent. Important
claims were checked against decoded frames, current official documentation, and Blender 5.2
experiments. Machine wording remains fallible and is not treated as an authoritative quotation.
The UV lesson produced an authored-seam tangent-bake test; the sculpt lesson produced a seven-stroke
continuous-surface test and retained a false-`FINISHED` failure; retopology planning transferred to
a sparse-versus-adequate articulation-density test; three-point lighting transferred to a grazing
surface-review rig that reveals a localized dent 2.57× more strongly than broad frontal light. The
earlier six-second project fixture remains pipeline-only evidence.

The advanced Snow live lesson adds patch delimitation, loop tracing, density reduction, functional
eyelid/inner-mouth structures, and pole-placement reasoning. Its different-shape hose transfer held
topology and a 92-degree bend constant while moving one identical five-pole pair: bend-zone mean
deviation increased 3,437.77x when the pair sat inside articulation. Two invalid deformation-axis
setups are retained. This does not substitute for a rigged facial expression test.

The official Intro to Shading lesson was bounded to what its inspected frames support: material
slots, world state, render engines, and viewport contexts can change appearance independently. Its
different-shape transfer adds a typed conservative classifier for geometry, normals, material,
lighting, and bevel-profile intervention signatures. Five controlled defects classified correctly,
all were visibly measurable, and 5/5 meshes passed fresh verification after OpenGL-exit,
empty-collection, and inward-winding failures were rejected. Mixed-cause production transfer remains
unmeasured.

The articulation transfer now includes a real two-connected-bone Armature setup on a manually
authored organic limb. With identical smooth weights and an 82-degree pose, a 21-ring purposeful
joint cage reduces joint-zone mean deviation from an 11-ring cage's `0.01887370` to `0.00300313`
against a 47-ring rigged reference (6.28467x); joint maximum falls from `0.06306881` to
`0.01436530`. All three posed evaluated meshes pass fresh verification. Rejected camera and cap
presentations remain documented. This is weighted joint evidence, not a full character or facial
expression claim.

The source registry is normalized to explicit URL/local path, creator, type, trust tier, version, topics, access booleans, status, and rejection reason. Approved-root document ingestion, approved-host web fetching, structured skill retrieval, append-only skill telemetry, explicit uncertainty, multi-view regression checks, component-graph checks, and rebuild pressure are implemented with unit tests. Runtime and cross-session evidence remains sparse.

A later quality rebuild rejected the original held-out sword's primitive-like visible result despite
its passing automated score. The replacement uses 19 profile/section/lathe/helix-authored semantic
components without mesh primitive operators, improves normalized front IoU from 0.8285 to 0.8369,
and passes fresh-process evaluated verification on 19/19 UV-bearing closed meshes. Because the same
reference had already been used, this is corrective production evidence rather than another
held-out generalization pass. See `runs/2026-08-10_profile-authored-sword/`.

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

1. Production-quality organic form sculpting and full-character/facial articulation. A controlled
   weighted two-bone joint now passes, but multi-stroke mechanics and this limb are not claimed as a
   professional character form or expression rig.
2. Production transfer of seam-authored UV/high-to-low baking and a named external-engine
   validation. A real controlled Cycles Selected-to-Active tangent bake now passes on a flared
   housing, replacing the earlier synthetic-map-only evidence.
3. Multi-day retention and broader real-session use of context-aware knowledge retrieval.
4. Production transfer of surface-defect cause classification. Candidate localization, grazing-light
   observability, and five controlled intervention signatures now pass, but mixed real defects remain.
5. Broader held-out visual modeling across additional shape families without benchmark-specific
   builders. Benchmark B passed at 0.8285 IoU and transfer benchmark D passed at 0.6766 IoU; six
   supplied references remain reserved for broader generalization evidence.
6. Advanced external instruction now includes one long-form retopology live study; local transcription and
   authored-caption ingestion are functional, but rigged facial expression transfer, production
   sculpt/retopology, and mixed-cause production surface diagnosis remain.

## Exit decision

The foundation remains **PARTIAL**. External visual instruction, a genuine held-out visual and
technical pass, and one successful cross-family transfer now exist. Multi-day retention and
independent professional judgment remain below the gate.

## Highest-value next step

Execute a rigged facial expression or multi-axis joint/twist transfer with corrective shapes and
independent surface/topology review. On a later calendar day, also run the retention
quiz; elapsed-time evidence cannot be manufactured in this session.
