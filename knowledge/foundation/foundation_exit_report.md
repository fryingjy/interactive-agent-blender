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

- `quizzes/quiz_001.md` contains 13 answers; `quiz_002.md` adds 15 fresh mechanism/evidence answers;
  `quiz_003.md` adds 20 fresh mechanism/context answers on 2026-08-11.
- Modifier-order findings cover all four planned pairs, not two.
- One stack-order skill has been promoted with experimental evidence.
- Several project skills have prior runtime use, but cross-asset and second-shape validation is still sparse.

Structured retrieval returned the expected top skill in five of five context-rich cases. One retrieved material-slot skill was then used in Blender as a single mutation, reducing measured orphan slots from one to zero with revision-linked telemetry and independent verification. Cross-calendar-day self-retrieval is now recorded across 2026-08-08, 2026-08-10, and 2026-08-11; independent and longer-horizon retention plus broader production runtime use remain unmeasured. The prior low-confidence area—automated pinching/curvature diagnosis—now has controlled localization/classification evidence plus a mixed five-cause transfer on the connected-quad barrel; unknown real-production diagnosis remains open.

An inspectable strategy policy now ranks primary representation, component boundaries, edit mode,
and repair-vs-rebuild independently. Its declared benchmark passed 10/10 cases and preserves a real
CLI import-context failure and fix. Because cases live beside the runner, this is policy-level
regression evidence rather than held-out judgment.

### Video and structured training

Eleven complete official Blender lessons were ingested through the approved-root pipeline: Modeling
Introduction, Extrude, Bevel Tool, UV Unwrapping, Intro to Sculpting, and Planning the Facial
Retopology, Three Point Lighting, Snow - Stylized Character Retopology Live #2, plus Intro to
Shading, Knife, and Loop Cut. They provide 11,927.510 seconds of real video/audio and 148 decoded frame samples
(`runs/2026-08-10_online-lessons/`). The first four use CC BY 3.0 Wikimedia mirrors; the sculpt
retopology, and lighting lessons are free official Blender Studio sources with 650 authored-caption segments. Local
machine transcription/caption sidecars supplied 4,888 timestamped segments where creator captions were absent. Important
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

The next articulation transfer adds a real three-bone `Upper`/`Lower`/`Twist` chain, smooth weights,
72-degree flex, 18-degree splay, 58-degree distal twist, and a relative corrective shape driven by
explicit local bone-rotation variables. The driver is 0.0 at rest, flex-only, and twist-only, and
1.0 only for the combined pose. Against a dense corrected reference, the low cage's joint mean
error falls from `0.05805965` to `0.01494744` (3.88425x), joint maximum from `0.12682819` to
`0.02697982`, and relative volume error from 12.3923% to 5.1967%. All 3/3 evaluated posed meshes
verify clean. Because reference and low cage share an authored correction hypothesis, this is
mechanism/transfer evidence rather than anatomical discovery or facial-production proof. See
`runs/2026-08-11_multi-axis-corrective/`.

The source registry is normalized to explicit URL/local path, creator, type, trust tier, version, topics, access booleans, status, and rejection reason. Approved-root document ingestion, approved-host web fetching, structured skill retrieval, append-only skill telemetry, explicit uncertainty, multi-view regression checks, component-graph checks, and rebuild pressure are implemented with unit tests. Runtime and cross-session evidence remains sparse.

A later quality rebuild rejected the original held-out sword's primitive-like visible result despite
its passing automated score. The replacement uses 19 profile/section/lathe/helix-authored semantic
components without mesh primitive operators, improves normalized front IoU from 0.8285 to 0.8369,
and passes fresh-process evaluated verification on 19/19 UV-bearing closed meshes. Because the same
reference had already been used, this is corrective production evidence rather than another
held-out generalization pass. See `runs/2026-08-10_profile-authored-sword/`.

A second profile-authored transfer uses the supplied tactical-axe reference to test a different
hard-surface silhouette family. A measured 35-point full-tang contour, exact through-aperture,
separate raised grip scales, exposed edge, and four fasteners produce seven semantic meshes without
mesh primitive operators. Normalized side-profile IoU is 0.942380, aperture/negative-space IoU is
0.771739, and fresh-process evaluated verification passes 7/7 UV-bearing closed meshes. Incorrect
tessellator assumptions, cropped framing, and a gray-background threshold failure are retained.
Because this source was selected during implementation, the result is corrective transfer rather
than held-out evidence. See `runs/2026-08-10_profile-authored-axe/`.

The articulation sequence now also transfers to Blender's official CC0 Human Base Mesh animation
head. A Jaw + bilateral-smile rig drives a relative combined-pose corrective that evaluates to
`0.0` at rest, jaw-only, and smile-only and `1.0` for the combined pose. Mouth-region mean
nearest-surface error falls from `0.00100663` to `0.00048193` (2.08876x), and maximum from
`0.00403267` to `0.00172016`. A fresh-process verifier confirms all three saved heads are closed
and nondegenerate at base/evaluated states, the 123 weighted jaw vertices touch only quads, and the
Armature/driver wiring is intact. The official mesh supplied anatomy/topology and the visible
expression is subtle, so this is mechanism transfer rather than production facial-artistry proof.
See `runs/2026-08-11_facial-expression-transfer/`.

Surface-cause classification now transfers from five isolated enclosure fixtures to five
simultaneous faults on the connected-quad barrel. A state-controlled adaptive matrix repairs
lighting, unnecessary bevel, material assignment, geometry, then normals; mean fixed-view error
falls from `0.10833657` to zero and thresholded changed pixels from 104,319 to zero. The final
clean/repaired image buffers and datablock states match exactly. Fresh verification confirms the
repaired body is one closed 5,376-quad component and independently detects 67 degenerates plus 152
non-manifold edges in the failed blanket-bevel state. Preset-order, Eevee sampling, stale-depsgraph,
and light-cache failures remain preserved. Ground truth was intentionally injected, so unknown
production defects and experienced review remain open. See
`runs/2026-08-11_mixed-surface-diagnosis/`.

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

The held-out vintage telephone wall-clock adds a third unrelated product family under gates frozen before source rendering. Its main housing and handset are separate but internally connected all-quad cages rather than primitive assemblies. Three-view normalized IoU is 0.839997, fresh Blender verification passes, a same-asset tangent-normal badge bake contains 26,290 non-neutral pixels, and Godot 4.7.1 preserves UVs, tangents, normal semantics, and unit scales. Two blockout failures, two neutral-bake failures, and a negative-scale engine failure remain preserved. This strengthens breadth and production handoff but is still automated evidence without independent expert acceptance. See `runs/2026-08-11_heldout-vintage-telephone/`.

The held-out metal watering can adds a fourth unrelated hard-surface/product family under the corrected P0/P1/P2 roadmap. It uses a connected 16-sided vessel cage, connected 12-sided spout cage, and a closed all-quad path-loft handle rather than a stack of radial primitives. Its three-view normalized IoU is 0.900535 and fresh Blender verification passes 9/9 assertions. A selected-to-active tangent normal bake, GLB export, and fresh Godot 4.7.1 import pass; the earlier converted-curve handle remains retained as a non-manifold rejection. This is additional automated transfer evidence, not independent professional acceptance. See `runs/2026-08-11_heldout-watering-can/`.

## Largest remaining gaps

1. Professional hard-surface/SubD judgment, multi-view reference construction, topology strategy,
   production-ready prop workflow, and low-intervention cross-asset transfer remain materially
   incomplete. A held-out stylized boombox passed its automated gates but was rejected on direct
   human visual comparison against the reference (wrong color, wrong proportions, no real
   resemblance) and its evidence was removed entirely rather than kept as a false pass -- the
   clearest evidence in this project that automated silhouette/topology gates are not sufficient. A
   second camera passed automated gates but failed experienced topology-strategy review; the later
   one-component rebuild is corrective. This does not establish breadth or professional acceptance.
2. Production transfer of seam-authored UV/high-to-low baking. The controlled flared-housing bake
   now passes a real Godot 4.7.1 import with explicit package tangents, normal-texture semantics,
   PBR factors, UVs, and scale; it is still not a production asset or human-reviewed render.
3. Longer-horizon/independent retention and broader real-session use of context-aware knowledge retrieval.
4. Unknown real-production surface-defect diagnosis. Candidate localization, grazing-light
   observability, five isolated signatures, and a five-cause adaptive transfer now pass, but the
   transfer used intentionally injected ground truth and has no experienced surface review.
5. Broader held-out visual modeling across additional shape families without benchmark-specific
   builders. The online CC0 boombox passed one predeclared multi-view case at 0.8159 mean IoU with
   15/15 fresh-process scene assertions after primitive-assembly, bevel-damage, and false
   axis-verifier attempts were rejected -- but direct human review then rejected the asset itself as
   not resembling the reference, and it was removed rather than counted as breadth evidence.
   A second CC0 camera reached its automated held-out gates at 0.8717 mean IoU, but experienced
   review rejected the 19-object assembly strategy. Its first post-review one-component correction
   was also rejected because lens-only bevel weighting omitted intended sharp edges and four-sided
   top controls merely looked rounded under SubD. The rebuilt 530-quad cage uses regular 12-edge
   controls, begins from a literal box perimeter rather than a pre-rounded superellipse, and weights
   all 492 semantically intended hard edges, including the four three-segment
   longitudinal corner rails; base, Bevel-only, final SubD, UV/
   material, silhouette, and one-mesh GLB checks pass. Because both stronger construction rules were
   supplied during review, that correction is not relabeled held out.
   Six supplied references remain reserved for broader generalization evidence.
6. Advanced external instruction now includes one long-form retopology live study; local
   transcription and authored-caption ingestion are functional. Retopology fundamentals remain
   active, while production sculpting and advanced organic/facial specialization are deferred.

## Exit decision

The foundation remains **PARTIAL**. External visual instruction, a genuine held-out visual and
technical pass, one successful cross-family transfer, and cross-calendar-day self-retrieval now
exist. Independent/longer-horizon retention and professional judgment remain below the gate.

## Highest-value next step

Run another unrelated held-out hard-surface or curved-SubD prop with the stronger one-object/
connected-component rule predeclared wherever the design permits continuous topology. The previous
second-family camera automated pass was overturned by experienced review, so it does not close the
professional-quality breadth gate. Pair the next run with production texture/bake and named-engine
visual review, exercise the runtime planner throughout, continue
longer-interval retention checks, and seek experienced review when available. Sculpt-heavy and
character benchmarks remain deferred.
