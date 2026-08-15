# Reference-workflow video synthesis

## Access and scope

All seven supplied public YouTube URLs resolved to the intended title and creator through YouTube
oEmbed. Each full video was passed to Gemini 3.6 Flash as public video input; the resulting records
state that both audio and visuals were used and contain timestamped episodes. The raw structured
analyses are preserved beside this file. No source video was downloaded or archived.

This is source study, not proof of capability. Every extracted item remains `CAPTURED` until it is
corroborated, reproduced, tested on a different target, and shown to improve a real model.

## Source fitness

| Source | Strong evidence for | Important limit |
| --- | --- | --- |
| Boxed Lunch Creative, PureRef | functional grouping, annotations, persistent working board | 54-second promotional overview, not a full tutorial |
| 3DTudor | orthographic Blender setup plus an external always-on-top board | Blender 2.8 UI; setup does not prove source quality |
| Lucas Peinador | assigning each secondary reference a named purpose; asking why | creative portrait synthesis, not exact reconstruction |
| Drawabox | multi-reference concept assembly | most of the video is mindset/play, not reference gathering |
| KazKalur visual wiki | schema-first catalog, direct timestamped evidence links, visual retrieval layer | game research demo; automation quality and deduplication are not validated |
| Alex Maniotis | reference fidelity should match the task: faithful, adapted, or composite | animation examples, not static geometry |
| FZD Design Cinema | extracting a property such as color/value/detail from a source without copying its literal subject | 2D photobashing; unsuitable as dimensional authority |

## Convergent findings adopted

1. A reference is useful only when its role is explicit. The PureRef board visibly labels images by
   form and color; Peinador selects separate sources for pose, face, hair, and palette; the visual
   wiki uses stable fields. The repository's `ReferenceItem.purposes` and property claims now make
   this machine-checkable.
2. Project-level and scene-level reference systems are complementary. A board supports broad
   collection, comparison, notes, and persistent retrieval. Blender Image Empties support calibrated
   axis-specific modeling views. One should not be forced to perform the other's job.
3. Reference method depends on intent. Faithful reconstruction, controlled adaptation, and creative
   synthesis are different tasks. The system must declare which task it is doing before it chooses
   evidence or a fidelity policy.
4. The question should drive collection. A schema or board is valuable because it makes missing
   evidence visible and retrievable, not because it contains many images.
5. Evidence should remain one click from its claim. The visual-wiki demo pairs structured fields
   with direct timestamped clips; this maps to source URL + purpose + observation + confidence in
   the existing knowledge system.
6. References remain active during work. Both PureRef demonstrations keep the board alongside the
   production application. This supports the iterative loop: model, discover uncertainty, search,
   update evidence, correct.

## Critical contradiction resolved

Several art sources recommend combining multiple references to create an original design. That is
appropriate for inspiration and synthesis. It is dangerous for reconstructing a specific real prop:
mixing attractive variants can corrupt dimensions, component layout, and hidden-form inference.

The adopted rule is therefore:

- **Design task:** multiple inspiration/form/style sources may be synthesized, with attribution.
- **Exact reconstruction:** converge on same-target/same-variant factual sources; inspiration may
  explain style but cannot authorize geometry or dimensions.
- **Adaptation task:** explicitly record which target properties remain fixed and which may change.

This is why the machine gate separates target identity, provenance count, view count, purpose, and
property coverage rather than treating “more images” as progress.

## Changes caused by the study

- Added a reproducible Gemini public-YouTube analyzer rather than leaving the method only in prose.
- Added structured `ReferenceSet`, `ReferenceItem`, property claim, conflict, and audit contracts.
- Added a strict `TARGETED_RESEARCH` planner disposition: incomplete reference evidence does not
  open Blender or create geometry.
- Corrected the runtime stage transition path so the stage being completed is actually validated;
  the MCP command no longer bypasses forward gates.
- Added controlled cases proving that one photo fails, five views from one listing are still one
  provenance source, mixed variants fail, and a same-object multi-view set can be ready to model
  without implying the resulting model is accurate.

## Still unproven

The videos do not establish automatic search quality, reliable target/variant recognition,
duplicate-image detection, camera calibration from perspective photos, hidden-form inference, or
professional modeling judgment. The Nailsea reference set can pass readiness while its resulting
model is still rejected by a human. Readiness is permission to begin a reversible blockout, not a
quality certificate.

## Next validation

Before a new prop is modeled, run a reference-gathering-only exercise on an unfamiliar target and
obtain human review of: target identification, unknowns, questions, source fitness, same-variant
evidence, property authority, conflicts, and remaining uncertainty. Then compare equal-budget
target-only versus structured-reference-set builds. Promotion requires the structured set to reduce
structural mistakes and improve multi-view fidelity on more than one unrelated target.
