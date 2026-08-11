# Retrieval quiz 003 — later-day transfer check

**Date:** 2026-08-11

**Conditions:** Fresh questions answered in a new goal continuation after checking quiz 002's
format and date; its answers were not copied into this pass. No study notes were pasted into the
quiz prompt. The assistant still has ordinary conversation/repository context, so this is
cross-calendar-day self-retrieval evidence, not a closed-book independent exam or controlled
cognitive study.

## 1. Why must a typed Loop Cut reject a selected path that crosses triangles?

A loop cut promises traversal through compatible quad flow, not arbitrary subdivision of every
selected edge. A triangle breaks the opposite-edge relationship and changes routing. The helper
must validate two opposite selected edges in each traversed quad before mutation; otherwise it can
add topology while falsely reporting semantic success.

## 2. When is Bisect a better choice than a freehand Knife path?

Use Bisect when the design intent is one exact infinite plane, such as trimming a housing at a known
cross-section. It provides explicit plane point/normal and side clearing. Freehand Knife is better
for a deliberate local path, but depends on view, snapping, occlusion, and confirmation state.

## 3. Why is Fill invalid for a Bisect that clears neither side?

Without Clear Inner or Clear Outer, the cut is an internal edge loop rather than an open boundary.
There is no hole to cap. Requiring side clearing prevents a successful call whose “fill” parameter
has no meaningful geometric target.

## 4. What must be inspected before trusting a silhouette IoU score?

Inspect both binary masks and their foreground bounds. A light-gray background can be classified as
foreground and produce a mathematically valid but meaningless score. Then check local contour,
landmarks, and negative space because global overlap can hide semantic mismatches.

## 5. Why is a strong single-view profile match still limited evidence?

It constrains only the visible projection. Hidden depth, back-side construction, perspective,
ergonomics, and multi-view consistency remain hypotheses. If the same image drove extraction and
evaluation, the result is same-reference evidence rather than unseen generalization.

## 6. How should pole placement be judged on a deforming form?

Judge the evaluated posed surface, not valence in isolation. Place redirections away from major
creases and articulation when possible, preserve density around motion, and compare error or
highlight continuity under the intended pose against a denser reference or controlled alternative.

## 7. Why can a technically clean mesh still fail surface review?

Manifoldness and nondegeneracy do not measure waviness, pinching, bevel hierarchy, normal errors,
material response, or lighting artifacts. Geometry, normals, material, lighting, and bevel profile
need separate controlled interventions when the visual cause is uncertain.

## 8. What distinguishes a geometry defect from a lighting defect in a controlled diagnosis?

A geometry intervention should change the evaluated surface or its curvature signature across
neutral views. A lighting intervention changes highlight visibility without changing geometry. If
multiple interventions improve the symptom, classify the evidence as conflicting rather than
forcing a single cause.

## 9. Why is a material slot not proof that the intended material is used?

Slots are only available assignments. Polygons may reference another index, an orphan slot may be
unused, and viewport `diffuse_color` may disagree with the connected shader node. Verify polygon
indices and the actual node path used by the target render/export pipeline.

## 10. What is the critical color-space invariant for a tangent-space normal bake?

The normal image must be treated as Non-Color data. Interpreting vector components through an sRGB
transfer curve changes their numeric meaning and can create false shading even when the bake itself
completed successfully.

## 11. Why do raw glTF vertex counts differ from Blender’s editable mesh counts?

Export can triangulate polygons and split vertices at UV, normal, material, or other attribute
boundaries. Verify format-invariant evidence—bounds, surface coverage, materials, UV presence, and
expected triangulation—not exact editable counts.

## 12. What does Shrinkwrap contribute to retopology, and what does it not decide?

It conforms a chosen low cage to a target surface. It does not choose silhouette, density,
deformation loops, pole placement, or detail isolation, and the wrong projection direction may do
nothing. Those remain modeling decisions requiring posed/evaluated checks.

## 13. When should a region be rebuilt instead of patched again?

Rebuild when repeated repairs fail, topology quality degrades, complexity grows, and measured visual
gain remains small. The decision should use region-local history and pressure, not frustration or a
fixed action count alone.

## 14. Why must rollback include more than vertex positions?

An artistic mutation can alter UVs, materials, modifiers, semantic IDs, selection, transforms,
active object state, or create objects. Restoring geometry alone leaves a false scene revision and
can corrupt later decisions. Rollback must restore all transaction-owned state atomically.

## 15. What makes a failed operation useful learning evidence?

Record the actual precondition, observed effect, correction, and a rerun on a different shape or
state. Do not erase the failure or promote a rule from the exception alone. A retained failure is
valuable only when it changes diagnosis, operation contracts, or future verification.

## 16. Why should tertiary detail wait until silhouette and primary proportions pass?

Detail makes an incorrect foundation more expensive to change and can distract visual judgment.
Primary silhouette and component ratios dominate recognition; secondary forms establish structure;
tertiary detail should only refine a credible base.

## 17. When is separate-object construction preferable to one continuous mesh?

Use separate objects for physically separate parts, independent materials/modifiers/transforms,
repeatable components, or clearer editability. Use continuity where curvature or deformation truly
requires shared flow. Component decomposition is a strategy decision, not a universal topology rule.

## 18. What evidence is required before calling a video “learned” in this project?

Actual accessible frames plus audio/captions/transcript must be inspected; the modeling reason must
be extracted; the principle must be reproduced on a different shape; a failure case must be tested;
and the result must change a skill or executable decision. A link, title, or passive archive does
not qualify.

## 19. Why does modifier order require pair- and topology-specific testing?

Every modifier consumes the previous evaluated output. A rule that holds for a flat seam may reverse
or disappear on an exact curved seam. Test the relevant pair on the relevant topology and measure
the resulting surface rather than promoting slogans such as “Mirror always goes first.”

## 20. What remains unproven after this retention pass?

Independent expert judgment, low-intervention professional quality across multiple unseen shape
families, multi-view reference modeling, production organic/facial work, and long-term retention over
weeks remain open. A later-day self-quiz strengthens retention evidence but cannot satisfy those
broader gates.

## Self-evaluation

- 20/20 answers state a mechanism and a context, consequence, or verification condition.
- Questions 1-3 and 18 include knowledge learned after quiz 002, so this is not a copy of the prior
  answer set.
- Calendar separation is genuine: quiz 001 is dated 2026-08-08, quiz 002 is dated 2026-08-10, and
  this pass is dated 2026-08-11.
- The result remains self-administered and should not be presented as independent proficiency proof.
