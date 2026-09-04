# Review and repair

Automated comparison measures silhouette, landmarks, component masks, negative spaces, topology,
and state. It does not certify product form or professional acceptability. Human rejection remains
first-class evidence and is never overwritten by a passing metric.

## Diagnose two dimensions

Every correction records both the visible symptom and the upstream root cause.

Symptoms accepted by `knowledge_engine.human_review` are `proportion`, `component_shape`,
`component_relationship`, `negative_space`, `depth_overlap`, `silhouette`, `surface_highlight`,
`topology`, and `construction_strategy`.

| Root cause | Meaning | Correct response |
| --- | --- | --- |
| `REFERENCE_FAILURE` | Wrong target or variant | Replace/rebind the source set |
| `INTERPRETATION_FAILURE` | Wrong 3D explanation of valid images | Reopen evidence and hypotheses |
| `REPRESENTATION_FAILURE` | Wrong shape family or assembly graph | Rebuild the affected component |
| `PROPORTION_FAILURE` | Correct representation, wrong dimensions | Bounded all-view refit |
| `COMPONENT_FAILURE` | Missing, misplaced, or wrongly connected part | Revisit correspondence/assembly |
| `DEPTH_FAILURE` | Third dimension contradicts secondary views | Recalibrate or refit depth |
| `SURFACE_FAILURE` | Major form is sound but curvature/highlights fail | Local cage or shading repair |
| `EXECUTION_FAILURE` | Blender did not realize the valid plan | Roll back and correct the typed operation |
| `EVALUATOR_FAILURE` | The comparison itself is misleading | Repair calibration/evidence, not geometry |

Upstream reference, interpretation, and representation failures cannot be fixed by accumulating
local geometry patches. If the representation remains valid, prefer the smallest localized repair;
otherwise rebuild the affected component from the last accepted checkpoint.

## Human review record

```json
{
  "review_result": "reject",
  "reviewer_type": "human",
  "reviewer_id": "reviewer identifier",
  "asset_id": "asset identifier",
  "scene_revision": 12,
  "failure_types": ["proportion", "negative_space"],
  "regions": [
    {"target": "main body", "failure_type": "proportion", "view": "front", "severity": 0.9}
  ],
  "severity": {"proportion": 0.9, "negative_space": 0.7},
  "notes": "Concrete observed defect and why it matters."
}
```

The reviewer identifies what is wrong and need not prescribe an operator. A review is bound to the
scene revision; a stale ticket triggers recapture instead of a blind edit.

```text
human or automated mismatch
-> revision-bound localized ticket
-> inspect base cage, evaluated surface, reference evidence, and render
-> classify root cause
-> bounded refit, local repair, or explicit component rebuild
-> remeasure every relevant view
-> fresh review
```

`tools/record_external_visual_review.py` validates and retains a user-authored review. Generated
HTML boards and pre-model approval gates are not part of the default workflow.

## Mandatory evidence channels

Inspect separately:

- raw editable cage and persistent IDs;
- evaluated modifier surface;
- fixed-camera silhouette and negative space;
- solid/MatCap surface read and wireframe;
- component placement and assembly boundaries;
- topology/manifold/degeneracy metrics;
- source hashes, camera calibration, and per-view fit residuals.

Smooth shading, all-quads, a manifold result, or a high aggregate score cannot substitute for a
correct form. Use Smooth by Angle, crease, support loops, or bevel only where the intended surface
requires them. Keep modifiers live and high/low variants in separate collections.

## Bounded correction policy

1. Freeze the current accepted state and evidence.
2. Name the failed component, view, symptom, and root cause.
3. Change one causally relevant variable or representation.
4. Inspect the exact changed region and all relevant views.
5. Accept only measured improvement without material multiview regression.
6. Roll back failed edits transactionally.
7. Escalate repeated local failure to a family or assembly-graph change.
8. Preserve the general lesson and negative evidence; do not preserve generated run media in Git.

The project is improving only when these loops produce visibly better unfamiliar assets and transfer
to an unrelated prop—not when they merely increase test, operator, source, or tutorial counts.
