# Question-driven reference research

## Outcome

The reference-workflow video principle now changes executable behavior. Unknowns are represented as
property-scoped questions with their trigger, impact, exact queries, inspected candidates,
provenance, accept/reject decision, reason, resolution, and reversible modeling constraint.

The Bialetti reference-only exercise records three questions and seven candidates. Two official
evidence links are accepted and five candidates are rejected rather than silently mixed into the
board. The authoritative 3-cup envelope is now 15 x 8.5 x 15.5 cm. No direct same-revision boiler
underside was found, so the underside remains simple, unmarked, separately revisable, and excluded
from fidelity scoring.

## Controls

- Returning the resolved high-impact envelope question to `OPEN` changes the disposition to
  `TARGETED_RESEARCH` and emits its two exact queries.
- Linking accepted evidence to a nonexistent `ReferenceItem` fails the reference audit.
- Deferring an unknown without a modeling constraint raises a validation error.
- The strict Blender modeling-stage gate rejects reference evidence whose question-driven research
  check is false.

The board remains model-free. Machine readiness still does not replace the explicit pending human
review required before the equal-budget target-only versus structured-reference build.

## Validation

- Question-driven verifier: 12/12 checks pass.
- Retrieval regression: 12/12 positive contexts and 4/4 abstention contexts pass; runtime history
  and generic workflow overlap cannot manufacture semantic relevance.
- Repository suite: 117 tests and 12 subtests pass.
- Pyflakes, compileall, repository audit (575 tracked files), JSON parsing, and diff checks pass.

## Reproduction

```powershell
python tools/verify_question_driven_reference_research.py
blender --background --factory-startup --python tools/run_stage_gate_lab.py
```
