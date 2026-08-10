# Foundation exit report

**Updated:** 2026-08-10

**FOUNDATION STATUS: PARTIAL**

**READY FOR HELD-OUT MODELING: NO**

This report reflects repository evidence through `runs/2026-08-10_modifier-foundation/`. It is not a claim that the complete professional-modeling curriculum is finished.

## Evidence summary

### Official documentation

Studied Tier A material includes:

- Subdivision Surface modifier.
- Bevel Edit Mode operation.
- Bevel modifier.
- Mirror modifier.
- Empties/Image Empty reference workflow.
- Mesh Editing operator index.
- Parts of the BMesh operators API.

Coverage remains unsystematic across the full mesh-editing branch, Boolean and Solidify standalone behavior, broader modifier families, retopology, sculpting, UVs, materials, and the modeler-relevant Python/BMesh surface.

The accessible Bevel modifier Manual is labeled Blender 4.5 LTS, while the newest lab ran in installed Blender 5.2.0 LTS. Records preserve that version distinction.

### Controlled experiments

Approximately 37 controlled/reproduction cases are now recorded:

- Roughly 27 prior operator and modifier-order cases.
- Ten standalone Bevel/Mirror variants in `runs/2026-08-10_modifier-foundation/`.

Prior experiments cover dissolve/delete, bridge/fill/grid fill, bisect, spin, split/separate, symmetrize, slides, shading, and four modifier-order pairs. Project history also contains production use of extrude, inset, bevel, subdivision, booleans, curves, and retopology.

The standalone modifier lab added:

- Bevel `NONE` versus `ANGLE` limiting on triangulated planar faces.
- Bevel segment-count density comparison.
- Excessive Bevel width with Clamp Overlap enabled/disabled.
- Mirror exact seam, below-threshold seam failure, larger-threshold repair, and Bisect behavior.

All seven encoded assertions passed. See `modifier_foundation_report.json` for evaluated measurements and `modifier_foundation_lab.blend` for the scene.

### Failure cases

Meaningful failures or limitations include:

- Bridge-loop wire-edge filtering causing a silent no-op.
- Grid Fill overlap failure on an unsuitable hole.
- Rip operator context failure in headless mode.
- Mirror-before-Subdivision producing non-manifold evaluated geometry in the tested stack.
- Bevel-before-Solidify being a no-op on a single plane.
- Mirror seam outside Merge Distance leaving eight boundary/non-manifold edges.
- Excessive Bevel width with Clamp Overlap producing nearly collapsed edges despite remaining manifold.

Failures remain visible and are not counted as successes merely because Blender returned without an exception.

### Retrieval and knowledge use

- `quizzes/quiz_001.md` contains 13 answers produced from understanding.
- Modifier-order findings cover all four planned pairs, not two.
- One stack-order skill has been promoted with experimental evidence.
- Several project skills have prior runtime use, but cross-asset and second-shape validation is still sparse.

Repeated retention has not yet been measured. The prior low-confidence area—automated pinching/curvature diagnosis—remains open.

### Video and structured training

No complete video lesson has been studied. Historical attempts could not access YouTube modalities and correctly did not claim video understanding. Local or user-provided legal video ingestion remains a future capability, not completed evidence.

No paywalled course is claimed as lesson-level study; only accessible curriculum/overview text was inspected.

## Stronger areas

- Closed-loop transaction and recovery infrastructure.
- Persistent geometry identity and live state probing.
- Core mesh operations used in production and controlled labs.
- Subdivision and contextual topology fundamentals.
- Modifier-order reasoning across four tested pairs.
- Standalone Bevel/Mirror fundamentals.
- Honest failure recording and independent technical verification.

## Largest remaining gaps

1. Systematic current Blender Manual coverage rather than isolated pages.
2. Standalone Boolean and Solidify documentation/labs.
3. Retopology curriculum and transfer tests.
4. Sculpt, UV, materials, and production/export foundations.
5. Modeler-relevant Python/BMesh documentation block.
6. Repeated retention and context-aware knowledge retrieval.
7. Visual surface judgment, especially pinching/highlight flow.
8. Second-shape and cross-asset validation of learned guidance.
9. Legal local video/tutorial ingestion with honest modality records.

## Exit decision

The foundation remains **PARTIAL**. Experiment count and one completed quiz are meaningful evidence, but breadth, repeated retrieval, runtime use, second-shape transfer, and visual judgment remain below the gate.

## Highest-value next step

Run the next second-shape modifier lab on curved/cylindrical geometry, including non-uniform-scale Bevel behavior and Mirror/SubD seam evaluation, then use the result to validate or narrow the new standalone guidance.
