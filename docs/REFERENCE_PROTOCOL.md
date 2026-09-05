# Reference protocol

## Mission

Reference collection is a core modeling capability, not a preliminary convenience. The agent must
learn to identify the target object, determine what information is missing, collect appropriate
references, rank them by reliability and purpose, distinguish factual references from inspiration,
resolve contradictions, establish proportions and dimensional anchors, identify primary/secondary/
tertiary forms, understand component relationships, build a reference plan, use references
continuously while modeling, re-research unresolved questions, and validate the finished model from
multiple views.

```text
REFERENCE COLLECTION -> REFERENCE ANALYSIS -> REFERENCE PLAN -> BLOCKOUT
  -> MULTI-VIEW CHECK -> PRIMARY FORMS -> SECONDARY FORMS -> DETAIL -> VALIDATION
```

Do not start modeling because one attractive image exists.

## Single-image tracing is not the goal

A single photograph usually cannot provide complete 3D information. For every reference ask: what
does this image tell me, what can it not tell me, is perspective distorting the proportions, do I
have another angle, do I have side/top/rear evidence, do I know any real dimensions, is the object
symmetric, which geometry is hidden, which features are uncertain. Never silently convert missing
information into invented geometry.

## Reference sets by purpose

- **Primary-form**: silhouette, overall proportions, major curvature and masses.
- **Orthographic/blueprint**: front, side, top, rear, bottom proportions.
- **Detail**: buttons, seams, fasteners, openings, joints, handles, small features.
- **Construction**: how components fit together, gaps, seams, assembly, interfaces.
- **Material/surface**: roughness, machining, plastic, paint, wear, surface treatment.
- **Dimension**: known real-world lengths, diameters, thicknesses, spacing.
- **Functional**: how the object moves, operates, connects, or is assembled.
- **Context**: scale, usage, physical relationships.
- **Inspiration**: style only -- never treated as factual evidence without corroboration.

## Search strategy

Generate searches from the target rather than a fixed query for everything: `[target] front view`,
`side view`, `top view`, `dimensions`, `technical drawing`, `blueprint`, `exploded view`, `teardown`,
`close up`, `mechanism`, `assembly`, `manufacturing`, `CAD`, `orthographic`. Add targeted searches
whenever an unresolved modeling question appears.

## Source quality tiers

- **Very high value**: manufacturer documentation, official technical drawings, engineering
  drawings, dimensioned drawings, product manuals, high-quality controlled product photography.
- **High value**: reputable technical sources, professional modeling references, high-quality
  tutorials, specialist communities, teardown/assembly documentation.
- **Useful but verify**: enthusiast photographs, marketplace listings, forum posts, social media,
  generic image searches.
- **Inspiration unless verified**: concept art, fan art, stylized renders, AI-generated images.

A beautiful image is not automatically accurate.

Structured manifests encode these tiers as `VERY_HIGH`, `HIGH`, `USEFUL_VERIFY`, and
`INSPIRATION`. A critical-property claim must have `MEDIUM` or `HIGH` confidence and a factual
purpose before `knowledge_engine/reference_analysis.py` will count it as authoritative coverage.

## Corroboration and conflicts

Seek multiple independent sources for important models (manufacturer drawing + front photograph +
side photograph + detail photograph + exploded/assembly reference + known dimensions). If sources
disagree, do not silently average them -- record the conflict, a possible cause, the current
decision, its confidence, and what would resolve it.

## Perspective distortion

Photographs are not orthographic drawings; perspective can change apparent length, width, thickness,
spacing, circular shapes, and relative component size. Use photographs for visual evidence and
orthographic/dimensional sources for proportions. Do not directly trace a perspective photograph as
if it were an orthographic projection.

## Dimensional anchors

When a trustworthy real-world dimension is available, use it as an anchor (overall length, a known
fastener diameter, a standard hole size, etc.), and record its source and confidence. Do not
fabricate precision from uncertain photographic measurements.

## Reference board organization

Organize by purpose, not one unsorted folder: `references/<target>/{primary,orthographic,details,
construction,dimensions,materials,mechanism,context,inspiration,uncertain}/`.

## Blender reference setup

Image Empties (front/back display, opacity, orthographic/perspective display, axis-aligned display,
depth/front display) are the primary mechanism --
<https://docs.blender.org/manual/en/latest/modeling/empties.html>. Images-as-planes
(<https://docs.blender.org/manual/en/latest/modeling/meshes/import_images_as_planes.html>) are for
when an image needs to exist as actual scene geometry/material, not every reference.

## Orthographic alignment

When front/side/top references exist: determine intended axes, normalize orientation, establish
scale, establish a shared origin, verify common dimensions, confirm the views describe the same
physical object. If they don't align, investigate perspective, distortion, a different product
revision/variant, or incorrect scale/orientation rather than forcing agreement without evidence.

## Revision control and metadata

Real products can have multiple generations/sizes/variants -- record target variant, version, size,
era before modeling. For each important reference, record source, type, purpose, view, reliability,
perspective, dimensional value, detail value, conflicts, and confidence, so the evaluator knows which
image to trust for which property.

## Modeling brief before Blender

Before complex modeling, produce a brief: object, primary components, secondary components, primary
proportions, known dimensions, unknown dimensions, critical silhouettes, critical negative spaces,
critical details, reference conflicts, modeling risks, confidence. This is the bridge between
research and actual Blender actions.

## Scene decomposition (structured, not just prose)

The primary/secondary/tertiary and mechanical/product-object sections below produce prose. Before
construction, that prose should also become a structured, checkable record via
`knowledge_engine/scene_decomposition.py` (`Component`, `Relationship`, `SceneDecomposition`) --
added 2026-08-13 directly in response to the adjustable wrench's actual failure mode: "I have a good
silhouette" vs. "you didn't actually model the wrench." A clean silhouette/topology pass cannot by
itself prove the object was decomposed into its real parts; `SceneDecomposition.check_object_coverage()`
can, by comparing the declared primary components against their actual physical representation and
flagging any with no plausible match. Legacy name matching remains one-to-one and ignores generic
tokens: one mesh named `Collector_Upper_Shell` cannot claim to satisfy a separate
`Boiler_Lower_Shell` merely because both contain "shell". A connected product skin may instead bind
multiple semantic components to distinct persistent semantic regions on the same host mesh. Each
bound region must exist, validate against the saved mesh's persistent IDs, and contain elements;
missing, stale, empty, or reused region identities fail closed. This preserves the anti-collapse
check without forcing material bands or molded transitions into unnecessary separate objects. It
remains a component-presence smoke test, not a geometry or likeness judgment.
When an aligned reference board provides component regions, a primary component may additionally
record optional normalized-centroid and normalized-size intervals. The same live capture then records
each matched mesh's evaluated world bounds, centroid, and size relative to the primary-component
union; out-of-range placement or proportion rejects the capture. This is deliberately optional:
missing views or perspective photos must not be converted into fictitious spatial precision. It is
still only a coarse placement/proportion gate, not proof of component shape, depth, topology, or
visual fidelity.
Run `tools/verify_scene_component_coverage.py` in a fresh Blender process against the saved asset,
the decomposition JSON, and its intended collection to record this check beside an asset review.
Advancing from `PRIMARY_BLOCKOUT` to silhouette/proportion review requires a structured distinct
component-coverage object as `component_coverage` stage evidence; a hand-authored boolean is deliberately
insufficient. A saved-asset evaluation should use the fresh-process report above rather than claim
that a live-stage record is independent verification. During active modeling, use the typed
`check_scene_component_coverage` runtime command to capture the actual live mesh names, session,
and revision before recording the stage evidence. The blockout gate rejects a capture once the
live scene revision differs, so coverage must be recaptured after any intervening edit.
Graph-shape validity
(duplicate/missing ids, dangling relationships) delegates to the existing
`knowledge_engine/reasoning.py::validate_component_graph`. This is a shared vocabulary validator,
not a second geometry planner. The current executable path is described in
[Shape solving](SHAPE_SOLVING.md).

The evidence-bound interpretation contract is defined below. Important
interpretations are typed as `OBSERVED`, `STRONGLY_INFERRED`, `WEAKLY_INFERRED`, or `UNKNOWN` and
carry evidence, confidence, impact, component references, and a modeling consequence. The structured
artifact covers the directive-required camera, form hierarchy, continuity/separation, negative-space,
landmark, symmetry, repetition, thickness, depth/overlap, material-boundary, dimension, unknown,
ambiguity, and construction fields. Only supported claims may change the strategy brief; important
unknowns and contradictory supported signals block blockout and produce an actionable research
contract. This preserves uncertainty instead of silently turning missing views into geometry.

## Primary / secondary / tertiary forms

Primary defines identity and silhouette. Secondary defines construction and recognizable design.
Tertiary adds small realism/detail. Do not spend excessive time researching tiny details before the
primary and secondary structure is understood.

## Negative space is data

Collect and evaluate gaps, openings, slots, holes, clearances, panel separations, handles, spaces
between components. A model with the right outer silhouette can still be structurally wrong if its
negative spaces are wrong. Conversely, image gaps from reflections or texture are not necessarily
geometric holes: retain the [baseline counterexamples](BOOTSTRAP_BASELINE.md).

## Mechanical/product objects

References should answer: what moves, rotates, slides, connects, is fastened, is structural, is
cosmetic, is separately manufactured; where are seams and clearances. This prevents reducing a
multi-part object to one decorative blob -- the exact failure mode the wrench hit.

## Researching how the object is made

For difficult objects, go beyond beauty photographs: exploded diagrams, repair manuals, assembly
documentation, engineering drawings, manufacturing information, CAD references, teardown material,
patents where useful.

## Studying reference tutorials (don't just summarize)

When studying a tutorial about reference workflow, extract: what references the artist searches for
and why, what they reject, how they organize and align them, how they establish scale, how they
handle conflicting views, when they stop collecting and start modeling, when they return to
references, how they recognize their model is wrong. The goal is to learn the workflow, matching
`docs/BLEND_FILE_STUDY_PROTOCOL.md`'s own "don't just report" discipline.

## Reference collection is iterative

`COLLECT -> MODEL -> DISCOVER UNKNOWN -> TARGETED SEARCH -> UPDATE REFERENCES -> CORRECT MODEL`. An
unresolved question ("is this panel separate geometry or part of the shell?") should trigger targeted
research, not a guess.

## Confidence levels

- **HIGH**: multiple independent sources agree, or reliable dimensional/orthographic evidence exists.
- **MEDIUM**: several photographs agree but perspective or dimensional uncertainty remains.
- **LOW**: single image, occluded area, strong perspective, or inference without corroboration.

Low-confidence geometry should remain easy to revise.

## Failure modes to detect

Single-image overfitting, perspective tracing, incorrect scale, mixed product variants, conflicting
views, AI-generated reference contamination, concept art treated as engineering truth, hidden
geometry invented without evidence, detail-first modeling, insufficient rear/side/top evidence,
incorrect reference alignment, reference accidentally moved, outdated references, reflections/
shadows/material patterns mistaken for geometry.

## Reference set to evaluator mapping

The evaluator should know which source is authoritative for which property (manufacturer drawing ->
dimensions, front photo -> front appearance, side photo -> side silhouette, detail photo ->
mechanism/detail, exploded view -> component relationships, material photo -> surface appearance).
Do not use one image to judge everything.

## Feeding the knowledge system

`REFERENCE -> OBSERVATION -> INTERPRETATION -> DECISION -> CONFIDENCE -> EXPERIMENT -> VALIDATION`.
Important conclusions enter the existing `knowledge/foundation/source_registry.json` /
`docs/KNOWLEDGE_SYSTEM.md` lifecycle, not a separate system.

## Machine-enforced reference-set contract

The prose rules above are enforced by `knowledge_engine/reference_analysis.py`. A manifest records
the exact target and variant, each reference's provenance source, purpose, view, projection,
property-scoped claims, dimensional anchors, limitations, and explicit conflicts. The audit keeps
these concepts separate:

- five views from one listing are five views but one provenance source;
- a perspective photograph that looks frontal is not an orthographic drawing;
- an inspiration image cannot authorize a dimensional or construction claim;
- an image of a different variant cannot fill a missing view for the target variant;
- an unresolved critical conflict forces targeted research;
- a dimensional anchor counts only when its reference is explicitly scoped to `DIMENSION`;
- duplicate full-object catalog angles do not satisfy a requested number of distinct viewpoint
  families, and a component detail does not count as a complete geometry view;
- `geometry_scope`, `viewpoint_family`, and bounded `occlusion_fraction` state what an image can
  actually constrain instead of promoting every accepted image to equal authority.

The disposition is `READY_TO_MODEL` or `TARGETED_RESEARCH`. The planner responds to the latter with
no Blender operation. `build_reference_stage_evidence()` maps the audit into the strict
`REFERENCE_ANALYSIS` stage gate; entry into `PRIMARY_BLOCKOUT` is blocked until that current-stage
gate passes. Passing means only that a reversible blockout is justified. It does not certify that
the eventual model is accurate or professionally acceptable.

Worked controls and a standalone verifier are in `runs/2026-08-15_reference-set-gate/` and
`tools/verify_reference_set_gate.py`.

### Question-driven research history

Readiness coverage alone does not prove that important unknowns were actively researched.
`ReferenceResearchQuestion` records the property, trigger, impact, exact queries, inspected
`ResearchCandidate` records, accept/reject reasons, resolution, and any reversible modeling
constraint. Accepted candidates must link to a factual `ReferenceItem`; rejected candidates remain
visible rather than disappearing from the evidence trail.

An open high-impact question now fails both the reference audit and the strict
`REFERENCE_ANALYSIS` stage gate. A lower-impact question may be `DEFERRED` only after attempted
research and only with an explicit modeling constraint. The policy is covered by controlled stage
and reference-set tests; it must be re-exercised and independently reviewed for each new board.

## Success criteria

Reference collection is successful only if it improves the model: better proportions, better
component placement, better negative spaces, better multi-view consistency, fewer invented features,
fewer structural mistakes, better object decomposition, fewer late-stage rebuilds, better visual
fidelity. Optimize for information value, not image count.

## The professional reference-driven loop

```text
USER REQUEST -> IDENTIFY TARGET -> DEFINE INFORMATION REQUIREMENTS -> SEARCH REFERENCES
  -> RANK SOURCES -> BUILD REFERENCE SET -> CHECK CONTRADICTIONS -> ESTABLISH DIMENSIONAL ANCHORS
  -> DECOMPOSE OBJECT -> CREATE MODELING PLAN -> OPEN BLENDER -> BLOCKOUT
  -> COMPARE AGAINST REFERENCES -> CORRECT PROPORTIONS -> PRIMARY FORMS -> MULTI-VIEW CHECK
  -> SECONDARY FORMS -> DETAILS -> SURFACE/SHADING -> FINAL MULTI-VIEW REVIEW
  -> INDEPENDENT VALIDATION
```

## Non-negotiable rule

If the agent does not have enough evidence to make an important modeling decision, it should
identify the missing evidence and research it. Do not guess simply to keep moving. The objective is
not a beautiful reference board -- the objective is a better model.

## Interpretation and geometry authority

Reference interpretation records visible components, relationships, uncertainty, questions, and
dimensional anchors; it does not choose geometry. The executable path is:

```text
reference audit
-> image evidence and editable masks
-> reviewed components and correspondence
-> registered cameras
-> competing executable shape and assembly hypotheses
-> bounded multiview fit
-> typed Blender compilation
-> evaluated inspection and refit/rebuild tickets
```

`knowledge_engine.reference_analysis` owns provenance and research policy.
`knowledge_engine.scene_decomposition` retains the evidence-bound component vocabulary needed for
live scene-coverage inspection. `modeling_core` is the only authority for representation, assembly,
fitting, and topology compilation. Model-assisted labels remain proposals until reviewed and
hash-bound. A fitted winner proves agreement only with the supplied masks, cameras, variables, and
families; it does not prove hidden geometry or professional quality.

Advancing from `REFERENCE_ANALYSIS` requires a structured `REFERENCE_SET_AUDIT`,
`REFERENCE_MODELING_SPEC_AUDIT`, and accepted `MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE`. Bare booleans,
hand-copied ratios, and prose-selected mesh families do not satisfy the gate.

## Relationship to video learning

Local and public-video study is a research source governed by `VIDEO_PROTOCOL.md`. It may improve
reference reasoning or technique retrieval, but it cannot bypass source validation, shape-family
competition, Blender inspection, or transfer testing.
