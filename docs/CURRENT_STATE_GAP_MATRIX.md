# Current-state capability gap matrix

Updated: 2026-08-24. The 2026-08-21 ground truth below still holds; two new decisions apply on top
of it. First, `runs/2026-08-23_stylized-longsword/` produced a first blockout and then a real
reference-corrected revision (blade width/taper rescaled to a precisely-measured historical
longsword after the original guess proved oversized), which is genuine evidence that the
reference-correction habit works when applied -- but the project owner also reviewed this and
concluded the deeper bottleneck this matrix already names below (competing 3D interpretation) is
still being under-invested in relative to individual model builds, and separately asked that
weapon-related subject matter be removed from the active modeling curriculum in favor of neutral
manufactured props. See `docs/FAILURE_TAXONOMY.md` for the new root-cause classification this
triggered, and `runs/2026-08-23_stylized-longsword/README.md` for the shelving note.

**Update, same day, later:** the reference-reasoning pipeline described in "Current bottleneck"
below is now actually built (`1d9d071`) and proven on a real fresh neutral prop, not just
diagnosed -- `runs/2026-08-23_stanley-classic-bottle-reference-pipeline/`. The `REFERENCE_ANALYSIS`
gate genuinely required and passed the full evidence chain (component graph, reference-set audit,
component-reference coverage, the 11-pass visual-reconstruction audit), and it caught a real
upstream mistake before any geometry existed: a barrel/waisted body profile was a reasonable first
read of the reference photo, recorded as a genuine competing hypothesis, and rejected by an actual
pixel measurement (`CONTRADICTED` on both tested views) in favor of the correct straight-cylinder
reading. The blockout that followed matched the reference-analysis fractions exactly when
independently re-measured. A second human-review correction (reducing 4 objects to 2, a
`REPRESENTATION_FAILURE` per the new taxonomy) and a real tooling gap (no material-lit render
existed; added and debugged live, `81e815b`/`477ba38`) both got handled and recorded properly
mid-run. This is the first prop this project has taken through blockout under the strengthened
gate, and no new prop starts are paused now that it exists and works.

**Update, 2026-08-24:** Stanley now reaches `SECONDARY_FORMS`. Structured coverage supports distinct
persistent regions on one connected `Vessel` plus the removable `CapCup`; controlled renders drove
a connected shoulder-loop correction and fill/inset repair of the open cap top. This is real
closed-loop progress, but still has no human visual acceptance and is not a ladder promotion. The
run is now frozen at that stage by direct instruction to move on.

**Update, 2026-08-24, tutorial cutoff:** the CG Cookie sci-fi-crate I0 reproduction is retained at
6.8/10 rather than polished indefinitely. It demonstrates a connected one-cube shell, fitted
duplicate/separate assemblies, live unapplied modifiers, render-driven correction, fresh-process
verification, and a successful curved-geometry transfer. Simplified visible forms and 32 evaluated
bumper n-gons keep I0 incomplete; the next work is a different bounded intermediate tutorial with
an unobscured creator-final result.

## Ground truth

- Foundation status remains **PARTIAL**.
- The donut/mug scene is tutorial-following training, not unfamiliar-reference evidence.
- Deleted named-product builds are not active and are not current proof. Their useful failure history
  remains in Git, dated reports, and the source-retention ledger.
- One skill retains non-circular `RUNTIME_VALIDATED` status:
  `bevel.segments.parity_avoids_corner_triangle`. Other runtime claims corrected by the 2026-08-19
  audit remain demoted.
- Current real-reference artifacts are `runs/2026-08-21_reference-aa-battery/` and
  `runs/2026-08-21_reference-scotch-c60/`. The latter is a reversible non-rotational primary-form
  and surface-strategy study, not a finished or human-approved prop.

| Capability | Demonstrated now | Honest state | Highest-value next proof |
| --- | --- | --- | --- |
| Reference-set readiness | Identity, provenance, view, projection, dimensional-anchor, conflict, and question-driven gates | Implemented, but information coverage does not prove understanding | Continue rejecting mixed variants and weak views on every real target |
| Competing 3D interpretation | Independent observations now drive an eleven-pass reconstruction audit; the C60 case rejects disconnected rails and a circular swept tube while retaining an unresolved base-boundary ambiguity | Implemented for boundary linearity, numeric ranges, and boolean states; visual judgments are recorded by the modeler and remain fallible | Add a new evaluator only when a real asset exposes another consequence type |
| Reference → construction | AA/LR6 controls a connected inset terminal; C60 controls one connected U-plan shell, real center channel, rear bridge, rail cross-section strategy, and reversible lower base | Demonstrated on one rotational and one non-rotational primary-form study | Complete the missing C60 hinge/base forms, then test transfer on another unrelated target |
| Typed Blender execution | Persistent-ID selection, transactions, rollback, fingerprints, typed operations, Blender-native diagnostic renders | Strong infrastructure | Demonstrate sustained use through a difficult reference repair without an object-specific builder |
| Visual correction | Controlled solid, MatCap, silhouette, wireframe, normal, depth, and component passes exist; C60 rejects a five-section angular wave and rebuilds it as a nine-section live crease/SubD cage | One real visible correction is retained, but final likeness and repeatability remain unproven | Correct the remaining hub-support and base-perimeter mismatches without overfitting one oblique |
| Topology and shading | Connected-cage operations, explicit sharp intent, physical bevels, crease, SubD, and Smooth by Angle are available | Strong controlled evidence; conditional judgment still limited | Choose among crease, support loops, and bevel from reference-driven surface intent |
| Knowledge changes behavior | Depth-critical multi-view evidence rejected a spike interpretation and produced a passing broad-flange transfer | Demonstrated once | Repeat on unrelated forms before claiming reliable transfer |
| Tutorial/video learning | Range-scoped Gemini analysis, identity checks, independent episode review, reproduction, and transfer records exist | Operational but not a substitute for modeling | Research only after a concrete modeling failure; do not mass-ingest |
| UV/material/export | Controlled UV, bake, PBR, high/low, and export evidence exists | Transfer evidence, not accepted-asset proof | Apply production preparation after a reference model passes major-form review |
| Human review | Rejection records and review schemas exist; human rejection overrides metrics | No current AA/LR6 or C60 approval | Obtain human review after visual correction, without pre-approval boards or HTML gates |
| Professional autonomy | No repeated set of unfamiliar, production-ready, human-approved assets | Not achieved | Complete multiple unrelated targets through interpretation, repair, production, and retention |

## Current bottleneck

The primary limitation is no longer Blender connectivity. It is deciding what a reference implies
in 3D, predicting what each interpretation would look like from other views, choosing a construction
that preserves editability, and revising that interpretation after renders expose a mismatch.

The C60 run now exercises that bottleneck once, but its hinge support and lower perimeter remain
coarse and it has no human acceptance. The next work is to correct those observed regions, keep the
unresolved molding/groove boundary reversible, and then test the same reasoning chain on another
unrelated target. Broad infrastructure or tutorial accumulation remains lower value unless a real
modeling failure exposes a specific missing capability.

**2026-08-23 update:** the execution-safety prelude and gate-enforcement pass below are now built
and verified (real pytest coverage, plus a live dry run against the actual C60 reconstruction
data confirming the gate now genuinely blocks without it and passes with it -- not a synthetic-only
check). Landed: `blender_ops/coordinate_frames.py` + `coordinate_safety.py` (a generic geometry-
jumped-coordinate-frame detector, wired into `DecisionTransaction.verify()` as an informational
`geometry_shift_flag`, targeted narrowly at the recurring world/local coordinate-space bug -- not a
claim it catches the other execution-bug mechanisms found in the same audit); a root-cause
taxonomy (`docs/FAILURE_TAXONOMY.md`) now required on every human-review rejection
(`knowledge_engine/human_review.py::ROOT_CAUSE_CATEGORIES`); component-scoped reference evidence
(`ReferenceItem.component_ids`, `PropertyClaim.component_id`,
`validate_component_reference_coverage()`); and a mandatory `REFERENCE_ANALYSIS` gate requirement
that the real `audit_visual_reconstruction()` result (not a bare `True`) pass, with every declared
component -- contested or not -- needing a structurally-checked construction-method justification.
See `docs/REFERENCE_INTERPRETATION.md`'s "Modeling rule" section for the mechanism, and
`blender_ops/stage_gates.py`'s `REFERENCE_ANALYSIS` requirements for the enforcement itself. Not yet
done: no new prop has been built under this strengthened gate -- that is the actual proof still
owed, not this doc's description of the mechanism.

**2026-08-23 direction:** the project owner's own audit of this matrix agrees with the paragraph
above and sharpens it into a concrete pipeline to build, not just diagnose:
`visual observations -> competing 3D hypotheses -> cross-view prediction -> eliminate
contradictions -> choose representation -> sparse blockout -> render -> revise interpretation`,
with an explicit representation-prediction step (predict what a candidate representation should
look like from front/side/3-4 before modeling it, reject it if the prediction contradicts the
source images), reference analysis made component-aware rather than mostly global-silhouette-aware,
and a required explicit justification (revolved/swept/extruded/molded/separate/continuous/inset/
nested) before constructing any component. This is now the highest-value next milestone -- proving
the system can correctly infer an unfamiliar neutral object's 3D construction *before* modeling it
-- ahead of finishing any individual prop. `docs/FAILURE_TAXONOMY.md` is the first concrete piece
of this: classifying every real historical failure by root cause (not just symptom) to confirm
empirically whether failures actually cluster upstream, before more pipeline code is written on
the assumption that they do.

**2026-08-24 held-out evidence:** the double-bladed fantasy hammer reached only 6.6/10. Its
connected-cage construction, fresh-file technical verification and one render-driven depth
correction worked, but the chosen head representation stayed too monolithic. This strengthens the
diagnosis that the bottleneck is component inference and hidden-form prediction, not command
transport or mesh validity. The next depth-critical target must have a second view or an independent
same-object structural source before modeling begins.

**2026-08-24 multi-view transfer:** after the new depth-critical gate was enforced, the Romanian
flanged-mace test used four assigned structural views. Its first spike-like radial interpretation
was rejected by the top view; a broad-flange connected cage then reached 8.1/10 at the major-form
gate with fresh evaluated-manifold evidence. This is the first direct proof that the strengthened
reference pipeline changed a modeling decision successfully. It authorizes detail on this asset,
but does not unblock I1 or prove general professional capability.
