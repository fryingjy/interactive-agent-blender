# Reference interpretation contract

Reference interpretation is the conversion of visible evidence into explicit, reversible modeling
decisions. It is not image collection, tracing, a prose description, or a claim that hidden geometry
is known. Its operational output is a validated `SceneDecomposition` that records what is seen, what
is inferred, what remains unknown, why a construction strategy is plausible, and how those claims
change the next planner decision.

## Capability taxonomy

| Capability | Required question | Structured location |
| --- | --- | --- |
| Visual-form inference | What primary, secondary, and tertiary masses define identity? | `primary_forms`, `secondary_forms`, `tertiary_forms` |
| Component inference | Which recognizable parts exist and how do they relate? | `components`, `relationships` |
| Depth order | What projects, recedes, nests, or sits in front? | `depth_order` |
| Overlap | Which contours occlude or cross others? | `overlap`, `relationships[type=overlaps]` |
| Symmetry | Which forms are mirrored, radial, or deliberately asymmetric? | `symmetry` |
| Continuity | Which boundaries must preserve one continuous surface? | `continuous_surfaces` |
| Separation | Which parts move, differ in material, show seams, or are separately manufactured? | `separate_parts`, component evidence |
| Negative space | Which holes, gaps, reveals, loops, and clearances carry identity? | `negative_spaces` |
| Material boundary | Is a visible boundary geometric, material-only, reflected, or unresolved? | `material_boundaries`, `ambiguities` |
| Construction hypothesis | Which editable representation best preserves the evidence? | `construction_hypotheses`, candidate/rejected strategies |

Camera/projection assumptions, thickness, landmarks, repetition, known/estimated dimensions, and
explicit unknowns complete the directive-required artifact. Every important claim uses one status:

- `OBSERVED`: directly visible in an identified view or source;
- `STRONGLY_INFERRED`: not directly visible, but supported by multiple observations or construction
  evidence;
- `WEAKLY_INFERRED`: plausible but not safe to harden into geometry;
- `UNKNOWN`: evidence is absent or contradictory.

`OBSERVED` and `STRONGLY_INFERRED` claims require concrete evidence text. High-impact supported
claims require a modeling consequence. Important weak/unknown claims block blockout and become
research questions. Contradictory supported modeling signals also block blockout instead of silently
overwriting one another.

## Runtime effect

`SceneDecomposition.to_modeling_brief()` is the bridge into the existing strategy selector. Only
supported claims can set representation signals such as path-following form, smooth continuity,
symmetry, repetition, deformation, watertight union, or independent component identity. The planner
then records the selected representation and component policy in its decision contract.

```text
reference observation
-> typed claim + evidence status
-> blockout-readiness gate
-> evidence-derived ModelingBrief
-> strategy score changes
-> planner operation/component policy changes
-> later Blender and visual verification (still required)
```

The policy contract is reproduced by
`tools/run_reference_interpretation_contract_lab.py` and independently checked by
`tools/verify_reference_interpretation_contract.py`. The dated run proves policy behavior across two
declared object families. It does not prove image understanding, Blender execution, held-out transfer,
or reference fidelity.

## Reference-to-blockout contract

Before geometry work, emit the machine-readable bridge with
`SceneDecomposition.to_reference_to_blockout_contract()` or
`tools/build_reference_to_blockout_contract.py`. It preserves the target, source-board identity,
supported and unresolved claims, component hierarchy, negative/depth/symmetry evidence,
dimensional anchors, candidate/rejected strategies, confidence, and one explicit selected strategy.
If several candidates remain, an author must select one explicitly; the exporter never chooses based
on an incidental list order. This is a planning/traceability record only: it cannot waive a separate
human authorization or certify a later blockout's visual fidelity.

## Secondary-view strategy resolution

`knowledge_engine.component_strategy.resolve_component_strategy()` handles a narrower but
load-bearing ambiguity: two constructions can share an exact front silhouette while disagreeing in
depth. It requires explicit continuous and separate candidates, fixed-frame view metrics, and built
object/connectivity evidence. A primary-view tie returns `TARGETED_REFERENCE_RESEARCH`; it cannot
be resolved by a generic strategy prior. A same-variant side, top, or oblique view must clear both
an absolute fit gate and a declared margin before the planner adopts a component policy.

The Blender 5.2 experiment in `runs/2026-08-15_secondary-view-component-strategy/` transfers this
mechanism from a rectangular to a 16-sided radial housing. Both controls score `1.0` from the front;
top-view evidence rejects the separate faceplates at `0.711577` and `0.695574`. A fresh process
verifies that the selected candidates are truly one object/one connected component. This is
controlled reconstruction evidence, not automatic photographic inference or a held-out prop pass.

## Modeling rule

Low-confidence regions must stay cheap to revise. A single candidate strategy is not certainty: keep
its claim IDs, preserve rejected alternatives and reasons, compare bounded representatives when the
choice is consequential, and revisit interpretation when multi-view or human review contradicts the
model.
