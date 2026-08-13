# Interactive Agent Blender — Master Directive

Repository: `https://github.com/fryingjy/interactive-agent-blender`

This document defines the durable operating contract for the project. It intentionally excludes commit-bound progress claims, source catalogs, and exhaustive curricula. Keep those in run evidence, foundation reports, knowledge records, and `docs/RESEARCH_ROADMAP.md`.

If prose conflicts with current code or reproducible evidence, evidence wins. Correct the documentation; never force evidence to fit an outdated claim.

## 1. Mission

Build an autonomous Blender modeling system that can create clean, editable, organized digital assets from unseen references or briefs while demonstrating sound form, strategy, topology, surface, workflow, recovery, and learning judgment.

The target is not merely to control Blender, execute Python, produce a technically valid mesh, collect tutorials, or create one impressive asset. The target is an adaptive loop:

```text
brief/reference
-> inspect and measure
-> choose a strategy
-> observe exact live Blender state
-> make one scoped modeling decision
-> execute through the typed interface
-> inspect base geometry, evaluated result, and appearance
-> accept, repair, rollback, or change strategy
-> repeat
-> independently verify and save an editable result
```

When knowledge is insufficient:

```text
problem
-> research a strong source
-> form a hypothesis
-> run a controlled Blender test
-> apply the result to the original asset
-> measure improvement
-> retain, narrow, or reject the lesson
```

Do not use real-world weapon-construction or engineering material as training data. Fictional combat-themed assets may use general artistic hard-surface, topology, and reference-modeling principles.

## 2. Precedence and scope

Use this precedence order:

1. User intent and explicit constraints.
2. Current live Blender and repository state.
3. Reproducible run/test evidence.
4. This durable directive.
5. Roadmaps, reports, knowledge cards, and historical notes.

Apply rigor in proportion to the task. A small requested edit does not require the full research curriculum. A benchmark or autonomous reference model requires strong evidence, checkpoints, comparisons, and independent verification.

Do not rebuild demonstrated infrastructure without evidence that it is inadequate. Inspect the existing typed operations, decision transactions, state probes/fingerprints, persistent IDs, semantic regions, modeling stages, evaluated probes, render passes, reference measurement, knowledge store, and verifier first.

## 3. Session start

Before modifying this repository or operating its live modeler:

1. Inspect the current branch, commit, and worktree status.
2. Read the current README and the parts of this directive relevant to the task.
3. Inspect `docs/RESEARCH_ROADMAP.md` only for research or learning-system work.
4. Inspect current foundation reports, coverage records, and recent run evidence when they affect the task.
5. Inspect the relevant implementation and tests; do not infer behavior from filenames or old reports.
6. Connect to Blender/modeler only when needed and record process/session identity, protocol version, scene revision, active object, mode, and selection.
7. Reconcile stale claims against newer evidence.

Never assume that a previous Blender process, selection, object mode, scene revision, or server connection is still valid.

## 4. Professional modeling judgment

The system must develop and demonstrate:

- **Form:** primary/secondary/tertiary hierarchy, silhouette, proportions, negative space, shape language, and component relationships.
- **Strategy:** box/poly, SubD, booleans, bevels, curves, separate geometry, modifiers, sculpting, retopology, and hybrid workflows chosen for the actual form and deliverable.
- **Topology:** contextual edge flow, poles, density, support geometry, triangles/n-gons, continuity, editability, and deformation needs.
- **Surface:** pinching, waviness, faceting, curvature continuity, highlight flow, bevel consistency, intersections, and shading artifacts.
- **Reference:** viewpoint, projection ambiguity, landmarks, overlap, symmetry, component ratios, and hidden-form uncertainty.
- **Workflow:** ordering, simplification, repair versus rebuild, modifier timing, stopping criteria, and production organization.
- **Recovery:** detect a bad result, identify likely causes, rollback or repair, change strategy, and continue without hiding failure.

Never reduce topology to slogans such as “all quads are good” or “triangles are bad.” Judge geometry by location, surface behavior, deformation, shading, editability, and output requirements.

## 5. Modeling stages

Use the existing modeling-stage controller as a flexible state machine:

```text
REFERENCE_ANALYSIS
PRIMARY_BLOCKOUT
PROPORTION_SILHOUETTE
SECONDARY_FORMS
TOPOLOGY_SURFACE
TERTIARY_DETAIL
PRODUCTION_PREP
FINAL_REVIEW
```

Require evidence for meaningful transitions. Regress when later evidence reveals an earlier mistake.

Do not polish tertiary detail while primary form, component placement, or silhouette is materially wrong.

## 6. Component and strategy planning

Before heavy modeling, decide:

```text
what must be continuous?
what should remain separate?
what repeats or mirrors?
what is curve-driven?
what benefits from a modifier?
what must deform?
what must remain editable?
```

Prefer the simplest construction that satisfies form and downstream requirements. A modifier, boolean, or separate object is not inherently less professional than manual continuous topology. Likewise, a clean cage is not useful if its evaluated surface or silhouette is wrong.

Store a component graph when relationships are complex enough to justify it.

## 7. Planner contract

Before each significant artistic decision, gather the relevant subset of:

```text
brief/reference and uncertainty
modeling stage
session identity and scene revision
active object, mode, and selection
persistent IDs and semantic regions
base topology
evaluated modifier result
controlled visual evidence
current mismatch or defect
recent accepted/rejected decisions
rollback and repair history
retrieved knowledge and confidence
```

Output one scoped decision with:

```text
goal
target
operation and parameters
expected effect
verification criteria
rollback/recovery option
confidence and alternatives when uncertain
```

High-level plans may span an asset. Exact later actions must depend on the state produced by earlier actions.

## 8. Closed-loop execution

For each meaningful modeling decision:

```text
OBSERVE
-> DIAGNOSE
-> RETRIEVE
-> DECIDE
-> ACT
-> VERIFY
-> JUDGE
-> ACCEPT / REPAIR / ROLLBACK / CHANGE STRATEGY
-> RE-OBSERVE
```

When available, use the typed transaction path:

```text
observe revision N
-> begin decision
-> capture scoped rollback state
-> perform one artistic mutation
-> reconcile persistent identity
-> inspect the actual result
-> commit or reject
```

A decision is an artistic choice, not an arbitrary function-call count. Mechanical setup, querying, saving, checkpointing, ID repair, and independent verification may be deterministic helpers.

Do not use unrestricted Blender code merely for convenience when a suitable typed operation exists. If fallback execution is necessary, disclose it and do not count it as typed-interface evidence.

## 9. State authority and recovery

Keep these identities distinct:

```text
process/session ID
scene revision
decision ID
command ID
event ID
```

Use layered state fingerprints for topology identity, coordinates, object transforms, and modifiers. Reject stale mutations when external edits invalidate the observed state.

Prefer transaction-owned or scoped checkpoint rollback over blind reliance on Blender’s global undo stack. Restore geometry, transforms, modifiers, semantic regions, and selection when each is part of the decision.

Track repeated repairs by region. Rebuild when patching causes topology degradation or complexity growth without measurable visual improvement.

Do not claim success because a command returned without exception. Inspect the result independently.

## 10. Persistent geometry and semantics

For tracked vertices, edges, and faces:

- IDs are nonzero and unique per domain.
- Deleted IDs are not silently reused.
- Surviving unrelated geometry retains identity.
- IDs survive save/load when supported.
- Unsupported identity-preserving operations record an explicit discontinuity.

Test identity behavior across the operation classes the system actually uses, including extrusion, inset, bevel, subdivision, loop cut, bridge, spin, merge, dissolve, boolean/application, and modifier application.

Use semantic regions as modeling memory for roles such as primary form, silhouette feature, corner, transition, support loop, feature edge, mirror seam, hole boundary, attachment region, bevel edge, high curvature, and flat panel.

Use semantics to localize inspection, retrieval, repair, and multi-step targeting; do not let labels drift after topology changes.

## 11. Separate truth channels

Never collapse these into one quality signal:

### Base cage

Inspect editable topology, density, edge flow, poles, support geometry, and semantic integrity.

### Evaluated surface

Inspect the actual modifier result, curvature, intersections, thickness, shading, and deformation. Candidate defect classifiers remain candidate evidence until validated.

### Visual/reference result

Inspect silhouette, proportions, negative space, component placement, highlights, and appearance from controlled views.

### Technical validity

Inspect manifoldness when required, degenerate or loose geometry, zero-length edges, normals, transforms, and scene hygiene.

A mesh can pass technical validity while having poor topology, surface quality, proportions, or editability.

## 12. Reference modeling and perception

Represent references with images, view/projection hypotheses, masks or components when useful, landmarks, symmetry, known dimensions, and uncertainty.

Measure before heavy modeling:

```text
silhouette bounds and aspect ratio
width/height profiles
landmarks and component ratios
overlap and negative space
```

Compare controlled Blender outputs to all relevant views. Useful signals include silhouette overlap, contour distance, bounding-box and centroid error, landmark error, component proportions, and negative-space error. Convert discrepancies into localized modeling tickets.

Metrics support judgment; they do not replace it. Do not optimize one view while silently damaging another.

Use Blender-native state and controlled render passes for Blender facts: silhouette, solid, wireframe, normals, depth, object masks, selected-region views, and reference overlays as needed. Tie each artifact to scene revision, camera/view, projection, resolution, and target objects. Use desktop screenshots only when UI state itself matters.

## 13. Research and knowledge lifecycle

Research must originate from a real task, curriculum gap, or benchmark requirement. Prefer:

1. Current Blender Manual, Python API, and official Blender training.
2. Established professional education.
3. Technical Q&A and serious community discussion.
4. Weak or isolated advice only as a hypothesis requiring reproduction.

Score sources by authority, accuracy, visual clarity, explanation, workflow completeness, production relevance, version relevance, reproducibility, and evidence quality.

Do not fabricate paid or inaccessible content, bypass platform restrictions, or claim video understanding without access to the relevant modalities. Record whether frames, audio, captions, transcript, and chapters were available.

Keep these layers separate:

```text
SOURCE OBSERVATION
INTERPRETATION
EXPERIMENTAL EVIDENCE
EXECUTABLE GUIDANCE
```

Promotion path:

```text
captured
-> interpreted
-> candidate
-> experimentally tested
-> runtime validated
-> transfer validated
-> promoted
```

Also preserve `contradicted`, `deprecated`, `version-limited`, and `insufficient-evidence` states. Narrow applicability instead of deleting conflicting evidence.

Knowledge is useful only when it improves a runtime decision. A research episode that ends in notes is incomplete.

## 14. Controlled experiments and retrieval

Use minimal Blender labs to answer specific questions about operators, modifiers and ordering, topology, SubD behavior, retopology, UVs, materials, or API/BMesh behavior.

For each useful experiment record:

```text
question and hypothesis
Blender version and preconditions
test geometry/state
operation and parameters
observed result
failure variants
unexpected effects
applicability limits
evidence paths
```

Test principles on a different shape before claiming transfer. Use retrieval quizzes without pasting study notes into the prompt when measuring retention.

Keep exhaustive curricula and source inventories outside this master directive. Update `docs/RESEARCH_ROADMAP.md` and the knowledge/foundation records instead.

## 15. Quality and completion

Evaluate proportionately across:

- **Technical validity:** non-manifold edges, degenerates, loose geometry, normals, and zero-length edges.
- **Topology:** valence/poles, triangle/n-gon placement, density, edge/face distribution, support topology, and SubD behavior.
- **Surface:** pinching, waviness, continuity, highlight flow, intersections, and bevel consistency.
- **Reference:** silhouette, contour, landmarks, proportions, overlap, and negative space.
- **Production:** naming, collections, modifier organization, materials, transforms, UVs, export readiness, and editability.
- **Process:** accepted/rejected decisions, rollbacks, recovery, external edits, human intervention, fallback use, and quality gain.

Before completion, review:

```text
1. primary form
2. silhouette and proportions
3. secondary forms
4. surface quality
5. topology
6. modifier behavior
7. scene organization
8. reference match
9. independent validity
10. final saved .blend and requested exports
```

## 16. Evaluation and anti-fake-progress rules

Use held-out assets for capability claims. Do not develop exact dimensions, topology, action sequences, decomposition, helper code, or repair recipes on the same asset used to claim generalization.

Do not count these as evidence of adaptive professional modeling:

```text
an asset-specific one-shot builder
a precomputed sequence relabeled as separate decisions
a tutorial summary relabeled as learned knowledge
an untested forum answer promoted as a rule
a clean validity report relabeled as good topology
a command accepted only because it raised no exception
a desktop screenshot substituted for queryable Blender state
a human correction attributed to the agent
a benchmark threshold changed after seeing the result
knowledge collected but never used
one successful asset relabeled as generalization
```

Keep failures and contradicted claims visible.

A credible capability claim requires multiple unseen assets across relevant shape families, little human intervention, strong form/reference fidelity, contextually appropriate topology, clean editable files, successful recovery, efficient decisions, knowledge reuse, and at least one externally researched problem solved end-to-end.

## 17. Reporting

End substantive sessions with a concise evidence report:

```text
STATUS: PASS / PARTIAL / FAIL
commit and worktree state
task and modeling stage
Blender/session/protocol identity when relevant
accepted, rejected, repaired, and rolled-back decisions
human interventions and fallback execution
technical, topology, surface, reference, and production checks
research sources, experiments, and knowledge updates
claims disproved
known limitations and evidence paths
largest remaining gap
highest-value next step
```

Report only fields relevant to the session. Never pad reports with unmeasured claims.

## 18. Tool architecture: Cloudglue and the Blender Connector (2026-08-13)

Two additional MCP connectors are available in this environment alongside the repository's own
typed modeler: **Cloudglue** (`mcp__Cloudglue__*`, video understanding — `describe_video`,
`search_video_moments`, `search_video_summaries`, `segment_video_chapters`,
`extract_video_entities`, `segment_video_camera_shots`, confirmed functional via a live
`list_collections` call) and a **Blender Connector** (`mcp__Blender__*`, broad live-Blender access —
`execute_blender_code`, `get_objects_summary`, viewport/window screenshots,
`get_blendfile_summary_*`, plus offline `search_manual_docs`/`search_api_docs` over the bundled
Blender manual and Python API reference, confirmed functional standalone).

Broad tools discover and observe; the narrow typed modeler establishes reproducible evidence. Do not
let this collapse into one undifferentiated "AI can touch Blender" capability:

- **Cloudglue** is a research source, equivalent in kind to a documentation page or forum post, not
  a fact. A video showing a technique does not make the technique correct for the current asset;
  treat its output as `SOURCE OBSERVATION` requiring the same `INTERPRETATION -> EXPERIMENTAL
  EVIDENCE -> EXECUTABLE GUIDANCE` promotion path as any other source (Section 13). For held-out
  benchmarks, never research the specific target asset after the benchmark is frozen — mark the
  benchmark `CONTAMINATED` if this happens.
- **Blender Connector** mutations bypass this repository's transaction/identity/rollback machinery.
  A mutation performed through it must be disclosed as `BLENDER_CONNECTOR_BYPASS`, never silently
  counted as `TYPED_MODELER` evidence, and must trigger external-edit reconciliation
  (`check_external_edit`/re-probe) before the typed path resumes — the same discipline already
  required for any other out-of-band edit (Section 9). Use it to observe, prototype, and discover;
  formalize a capability into `blender_ops/` (with tests, rollback, and identity guarantees) before
  relying on it for benchmark evidence.
- Neither connector's live-instance tools work without their own server actually running (the
  Blender Connector needs its addon started inside an open Blender session on port 9876, distinct
  from `blender_ops/modeler_server.py`'s own port 9878) — confirmed live, not assumed; both report a
  clear connection-refused/timeout rather than silently no-op.
- Do not build a redundant video-transcription/frame-extraction stack or a redundant generic
  Blender-Python bridge inside this repository merely because these connectors exist elsewhere in
  the environment — they are not guaranteed available in every session, so `blender_ops/`'s own
  typed surface and `knowledge_engine/ingest/video_ingest.py`'s local-file path remain the
  repository's real, portable capability; the connectors are an accelerant when present, not a
  replacement for owning the evidence trail.

## 19. Current development rule

Do not encode a commit-specific implementation queue in this document. Determine current priorities from the live repository, foundation reports, roadmap, failing tests, and latest evidence.

At every milestone ask:

> What is the highest-impact thing a proficient modeler would notice, understand, choose, or do here that the current system still cannot?

Then build or practice that capability.

Do not let infrastructure substitute for modeling intelligence, tutorial collection substitute for understanding, technical validity substitute for good topology, a polished render substitute for an editable asset, or one success substitute for generalization.
