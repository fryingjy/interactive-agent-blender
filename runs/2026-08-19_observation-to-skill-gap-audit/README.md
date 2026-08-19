# Audit: the runtime-validation evidence was circular, and the fix

Independent audit of HEAD `c2ea043`, focused on whether the recent shift from model-building to
skill-validation is actually producing better modeling behaviour or just better-looking records.

## Finding: all three RUNTIME_VALIDATED skills were validated against their own answer

Every skill declares `planner_hint.trigger_ticket_types`. Grepping those strings across the repo
showed each existed in exactly two places: **the skill's own hint**, and **the runtime-use script
that hand-authored a ticket of that type**.

| skill | trigger type | emitted by any observer? |
| --- | --- | --- |
| `bevel.segments.parity_avoids_corner_triangle` | `multi_edge_corner_bevel` | no |
| `extrude.inset_first.local_containment` | `local_feature_extrusion_on_coarse_surface` | no |
| `topology.loop_cuts.reserve_functional_regions` | `reserve_functional_face_regions` | no |

The observation side of the system emits only `area_outlier` and `high_angle`
(`blender_ops/evaluated_probe.py`). The two vocabularies are **disjoint**. So each "runtime
validation" was: write a ticket whose `type` is copied from the skill's trigger list, put the fix
in the ticket's `operation_params`, watch the planner return that fix, assert it matches. The
planner contributed a dictionary lookup; the knowledge contributed nothing to the mutation, since
`operation_params` came entirely from the ticket.

`tools/audit_observation_to_skill_gap.py` proves the consequence rather than asserting it: build a
cube, introduce a **real** corner triangle with an odd-segment bevel, observe with the project's own
tooling, feed those real observations to the real planner. Result (`observation_to_skill_gap.json`):
defect genuinely present (`3: 1` face), retrieval ranks the repair skill **first**, and the planner
still does **not** select it — it falls through to a generic `LOCALIZE_REFERENCE_MISMATCH` inspect.
`gap_confirmed: true`.

## Corrections applied

**1. A real observation→semantics bridge.** `knowledge_engine/defect_classifier.py` converts base-cage
topology into *named, structurally decidable* defect tickets. `corner_triangle` is exact — a 3-vertex
face with vertices on a 3+-edge corner either exists or does not — deliberately unlike the existing
statistical probe, which documents that it cannot separate defects from healthy curvature. Tickets
carry persistent IDs (so the scene owns the target) and carry **no** repair parameters (so the
classifier cannot recreate the circularity in a new place).

**2. Knowledge now supplies technique parameters.** `planner._skill_guided_ticket_decision` previously
took `operation_params` entirely from the ticket. It now merges `planner_hint.default_operation_params`
underneath the ticket's values: scene-specific facts (target, elements) stay ticket-owned and always
win; technique facts ("bevel segments must be even") come from knowledge. The decision rationale
records which keys knowledge supplied.

**3. A falsified knowledge claim was removed.** The first honest end-to-end run **failed**, and
usefully so. The bevel skill's `recovery` field claimed "re-run bevel_selection with an even segments
value (2 is sufficient to remove the triangle)". Tested directly: re-beveling an already-beveled
corner consumed the original triangle (face 54) but created a **new** one (face 232) plus three
9-gons — the cage went from 6 quads + 1 triangle to 36 quads + 3 ngons + 1 triangle. **The mesh got
measurably worse.** That advice was sitting in the knowledge base as validated recovery guidance and
was simply wrong. The real lesson: *bevel parity is preventive knowledge, not corrective; Bevel is
not idempotent.* The claim is now recorded as FALSIFIED with the evidence, and a matching
`failure_predicate` added.

**4. The loop was redesigned around that lesson.** Because the knowledge is preventive, the
classifier now runs at **verify time, inside the open transaction**, where its finding gates
commit-vs-rollback. `runs/2026-08-19_observed-defect-repair-loop/` closes the loop with nothing
hand-fed: bad bevel attempted → classifier observes `corner_triangle` before commit → retrieval
ranks the skill first → planner acts on the *observed* ticket → `reject_decision` rolls back to the
exact pre-decision state → the same intent is re-performed with the **knowledge-supplied**
`segments: 2` → classifier re-run is clean → commit. All 9 checks pass, the defective geometry is
**never committed**, and `final_corner_solid_iso.png` visually confirms a clean rounded corner.

**5. Overclaimed statuses withdrawn.** `extrude.inset_first.local_containment` and
`topology.loop_cuts.reserve_functional_regions` are demoted to `TRANSFER_VALIDATED`; their
`runtime_usage` entries are marked `success: false` with the reason. Their *transfer* evidence is
real and untouched — only the runtime claim was hollow. Both keep `planner_hint`s (they remain
planner-actionable at TRANSFER_VALIDATED) but now carry an explicit `trigger_vocabulary_status:
NOT_YET_OBSERVABLE` saying why they cannot yet fire from observation.

**6. A regression test makes the mistake impossible to repeat silently.**
`tests/test_skill_trigger_vocabulary.py` fails closed when a trigger type is neither observable nor
explicitly declared unreachable, and forbids `RUNTIME_VALIDATED` on an unreachable vocabulary. It
immediately caught a **fourth** skill (`deformation.topology.uniform_rings_before_shaping`) that I
had not inspected, which is now labelled too. Suite: 217 → 224 passing.

## An important distinction this surfaced

The withdrawn triggers are not all the same kind of thing:

- `corner_triangle` is a **defect** — decidable from geometry. Fixed by building a classifier.
- `local_feature_extrusion_on_coarse_surface` is a **defect-ish judgment** — needs a coarseness
  measure that does not yet exist, but is buildable.
- `reserve_functional_face_regions` is an **intent** — it cannot be observed from geometry *even in
  principle*. It has to come from a task brief or component plan.

So "knowledge changes runtime behaviour" splits into two separate problems, and only the first is now
solved. Skills keyed to intent need the reference/brief side of the planner, not a better probe.

## What is honestly proven, and what is not

Proven: for one structurally-decidable defect class, on a synthetic cube, the system observes a
defect it was not told about, retrieves knowledge for it, lets that knowledge supply the technique
parameter, rolls back rather than compounding the error, and verifies the repair — with visual
confirmation.

Not proven, and explicitly not claimed: that the classifier covers other defect classes; that the
vocabulary generalises; that any of this improves **resemblance to an unfamiliar reference**. The
single highest-value remaining gap is unchanged by this work and is now the sharpest it has been:
**no validated skill has ever fired during a real reference-driven build, because no real
reference-driven build currently exists in the repo.** The frozen magnifying-glass contract
(`runs/2026-08-18_magnifying-glass-reference/contract.md`) is the correct next target.
