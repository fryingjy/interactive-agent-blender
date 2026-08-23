# Failure taxonomy: root cause, not just symptom

Added 2026-08-23 in response to explicit user direction: the project was patching geometry when
the actual problem was upstream interpretation, and had no way to tell the two apart. This doc
adds a **root-cause** classification that sits upstream of, and is distinct from, the existing
**symptom** classification in `docs/HUMAN_VISUAL_REVIEW_PROTOCOL.md`.

## Two different questions

- `docs/HUMAN_VISUAL_REVIEW_PROTOCOL.md`'s `failure_types` (`proportion`, `component_shape`,
  `component_relationship`, `negative_space`, `depth_overlap`, `silhouette`, `surface_highlight`,
  `topology`, `construction_strategy`) answers **"what looks wrong in the render?"** It is
  enforced in code today, via `knowledge_engine.human_review.validate_external_visual_review()`.
- This taxonomy answers **"which stage of the reasoning pipeline produced that wrong render?"**
  One visual symptom can come from more than one root cause -- a render that "looks like the wrong
  proportion" could be a bad measurement, a bad representation choice (e.g. modeling a swept
  profile as a stack of separate primitives), or a correct plan executed with the wrong Blender
  operator. Patching the geometry fixes none of those unless the actual root cause is identified
  first.

Every future correction (a rejected human review, a repair ticket, a self-caught mismatch) should
be tagged with **both**: the visual symptom (existing enum, unchanged) and the root cause (this
taxonomy). The symptom says what to look at; the root cause says what to actually change.

## The nine root-cause categories

Verbatim from the project owner's direction:

| Category | Meaning |
| --- | --- |
| `REFERENCE_FAILURE` | Wrong object/version identified -- the reference material itself doesn't depict the thing actually being built, or depicts the wrong variant/revision of it. |
| `INTERPRETATION_FAILURE` | Incorrect 3D shape inferred from a 2D image -- the reference was the right object, but the mental model of its 3D form built from it was wrong. |
| `REPRESENTATION_FAILURE` | Right general object and right 3D understanding, but the wrong *modeling representation* was chosen for it (e.g. primitive-stacked instead of profile-swept, separate instead of continuous, when the reference actually shows the other). |
| `PROPORTION_FAILURE` | The representation is right; the ratios or dimensions within it are wrong. |
| `COMPONENT_FAILURE` | A component is missing, misplaced, or has the wrong continuity/connection relationship to its neighbors. |
| `DEPTH_FAILURE` | The front silhouette is fine; the depth (Y-axis / third dimension) is wrong. |
| `SURFACE_FAILURE` | The basic form is correct; highlights, curvature, or shading read wrong. |
| `EXECUTION_FAILURE` | The intended construction was correct on paper; the actual Blender operation/tool call executed it incorrectly. |
| `EVALUATOR_FAILURE` | A metric or render falsely reported success -- the check itself was wrong, not the model. |

## Reading the categories as a pipeline

The first three categories (`REFERENCE`, `INTERPRETATION`, `REPRESENTATION`) are **upstream** --
they happen before a single vertex is placed, in reference gathering and 3D reasoning. The next
four (`PROPORTION`, `COMPONENT`, `DEPTH`, `SURFACE`) are **downstream** -- they happen during or
after modeling, given that the upstream reasoning was already sound. `EXECUTION` is a pure
tool-use bug, independent of whether the plan was right. `EVALUATOR` is a bug in the judge, not
the work.

This ordering matters because upstream failures cannot be fixed by downstream repair. Rescaling a
component (a `PROPORTION_FAILURE` fix) cannot correct a shape that was represented as the wrong
kind of surface to begin with (a `REPRESENTATION_FAILURE`) -- that requires rebuilding the
component with a different construction method, not adjusting its dimensions. Classifying which
category actually failed, before touching geometry, is the whole point of this taxonomy: it is
what stops a correction from silently becoming a downstream patch over an upstream mistake.

## How this taxonomy gets used

1. **Historical audit** (2026-08-23): every documented failure/correction findable in `runs/` and
   `knowledge/foundation/foundation_exit_report.md` is being classified against these nine
   categories, to find out empirically whether this project's real failures cluster upstream or
   downstream. See the audit findings once complete (this section will be updated with a pointer
   to that report).
2. **Going forward**: any repair ticket, self-caught mismatch, or human-rejection record should
   name its root-cause category alongside its existing symptom `failure_type`, so the fix targets
   the actual failed stage instead of the nearest visible symptom.
3. **Pipeline design**: the in-progress reference-reasoning pipeline (competing 3D hypotheses,
   cross-view predicted-consequence testing, component-aware reference analysis, explicit
   construction-method justification before modeling) is aimed specifically at the upstream three
   categories, since those are the ones no amount of downstream repair can fix after the fact.
