# Structured retrieval abstention calibration

**Status:** PASS for deterministic retrieval regression; not a long-term cognitive-retention pass.

## Failure discovered

The skill store previously returned every skill with any positive weighted overlap. New unrelated
tickets therefore produced false planner hints:

| Unrelated ticket | Incorrect top result before correction | Score |
| --- | --- | ---: |
| camera focal-length/perspective mismatch | SubD boundary-resolution skill | 1.5000 |
| overlapping UV islands/texel density | material-slot assignment skill | 3.3416 |
| armature elbow/weight-paint collapse | Boolean cleanup skill | 1.7321 |

These were not merely untidy search results. A planner should research or abstain when no applicable
skill exists rather than route a camera, UV, or rigging problem into unrelated geometry guidance.

## Correction

`StructuredSkillStore.search()` now defaults to a calibrated score floor of 4.0 and documents how
exploratory callers can explicitly lower it. The CLI exposes `--min-score`. Negative thresholds are
rejected. A declarative 14-case regression set covers all six current skills with direct and
paraphrased positive contexts plus the three unrelated-ticket abstention controls. Positive cases
also require at least a 1.0 top-result margin.

## Evidence

- 11/11 positive contexts retrieved the intended top skill.
- 3/3 unrelated contexts returned no skill.
- All 11 positives exceeded the frozen 1.0 top-result margin; minimum observed margin: 2.7500.
- Full suite after correction: 76 tests plus 3 subtests passed.
- Pyflakes, compileall, JSON parsing, repository audit, and diff checks pass.

## Boundary

The cases were authored after inspecting the six-skill store and calibrating the threshold. They are
frozen regression evidence, not held-out proof. This closes a concrete false-positive behavior and
improves executable retrieval safety. It does not prove independent expert judgment, week-scale
retention, or successful runtime use on another held-out prop.
