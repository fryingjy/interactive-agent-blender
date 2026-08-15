# Structured retrieval abstention calibration

**Status:** PASS for deterministic retrieval regression; not a long-term cognitive-retention pass.

## Failure discovered

The skill store previously returned every skill with any positive weighted overlap. New unrelated
tickets therefore produced false planner hints:

| Unrelated ticket | Incorrect top result before correction | Score |
| --- | --- | ---: |
| camera focal-length/perspective mismatch | SubD boundary-resolution skill | 1.5000 |
| reference color-grade/white-balance mismatch | reference-strategy skill | 4.1700 |
| overlapping UV islands/texel density | material-slot assignment skill | 3.3416 |
| armature elbow/weight-paint collapse | Boolean cleanup skill | 1.7321 |

These were not merely untidy search results. A planner should research or abstain when no applicable
skill exists rather than route a camera, UV, or rigging problem into unrelated geometry guidance.

## Correction

`StructuredSkillStore.search()` now defaults to a calibrated score floor of 4.0 and documents how
exploratory callers can explicitly lower it. Runtime success and Blender-version affinity can rank
only candidates that independently clear the semantic floor. A broad workflow match must also be
supported by either a meaningful query match or a specific typed context channel; this prevents
generic `reference modeling` overlap from routing color grading into geometry strategy. The CLI
exposes `--min-score`, and negative thresholds are rejected. A declarative 19-case regression set
covers direct and paraphrased positive contexts plus five unrelated-ticket abstention controls.
Positive cases also require at least a 1.0 top-result margin.

## Evidence

- 14/14 positive contexts retrieved the intended top skill.
- 5/5 unrelated contexts returned no skill.
- All 14 positives exceeded the frozen 1.0 top-result margin; minimum observed margin: 3.6742.
- The current repository-wide pass contains 130 tests and 12 subtests; Pyflakes, compileall,
  repository audit, JSON parsing, and diff checks pass.

## Boundary

The original cases were authored after inspecting the then-current store; paired regression cases
were added as new reference skills entered the store. They are
frozen regression evidence, not held-out proof. This closes a concrete false-positive behavior and
improves executable retrieval safety. It does not prove independent expert judgment, week-scale
retention, or successful runtime use on another held-out prop.
