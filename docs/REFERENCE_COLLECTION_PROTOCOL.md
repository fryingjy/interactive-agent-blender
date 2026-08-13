# Reference collection & reference-driven modeling protocol

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
can, by comparing the declared primary components against the actual built object names and flagging
any with no plausible match -- not sufficient on its own (a name match isn't a geometry match), but a
real, mechanically-checkable red flag a silhouette pass cannot produce. Graph-shape validity
(duplicate/missing ids, dangling relationships) delegates to the existing
`knowledge_engine/reasoning.py::validate_component_graph`, which existed already but was called from
nowhere outside its own test -- this is now its first real caller, not a second parallel validator.
See `runs/2026-08-13_telephone-rebuild/scene_decomposition.json` for a worked example.

## Primary / secondary / tertiary forms

Primary defines identity and silhouette. Secondary defines construction and recognizable design.
Tertiary adds small realism/detail. Do not spend excessive time researching tiny details before the
primary and secondary structure is understood.

## Negative space is data

Collect and evaluate gaps, openings, slots, holes, clearances, panel separations, handles, spaces
between components. A model with the right outer silhouette can still be structurally wrong if its
negative spaces are wrong -- this is exactly the lesson the adjustable wrench rejection already
established the hard way (see `docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md`).

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

## Relationship to the video-learning roadmap

A separate, larger critique (recorded 2026-08-13, not yet implemented) argues the project's video
ingestion pipeline (`docs/RESEARCH_ROADMAP.md`, `video_ingest.py`) is an honest foundation --
real stream/audio/transcript/frame access with provenance tracking -- but not yet an autonomous
"watches a tutorial and understands it" system: it lacks YouTube discovery/acquisition, speech-to-
visual-action temporal alignment, Blender-action recognition tied to spoken reasoning, and automated
mistake/recovery extraction from tutorials. That is tracked as a distinct, larger future subsystem
(a `video_agent/` pipeline: discovery -> acquisition -> transcription -> scene segmentation ->
speech/action alignment -> lesson extraction -> mistake detection -> technique extraction ->
Blender experiment -> knowledge promotion) and is not implemented by this document.
