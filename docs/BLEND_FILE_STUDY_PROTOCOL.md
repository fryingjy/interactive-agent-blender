# Blend file study protocol

## Why this exists

Every source this project has studied so far is a document or a video: text, frames, captions,
transcripts. A `.blend` file is a different kind of source entirely -- it is not someone *describing*
a technique, it is the actual *result* of a professional modeler's decisions, inspectable directly:
topology, edge loops, pole placement, bevel weights, modifier stacks and their order, the SubD control
cage versus its evaluated surface, object decomposition, symmetry, naming, collections, and whatever
construction/WIP geometry the artist left in the scene. This is exactly the kind of "form, strategy,
topology, surface, reference, workflow, recovery" reasoning `docs/MASTER_DIRECTIVE.md` already asks
for, and a `.blend` file can show the *result* of that reasoning in a way a tutorial only narrates.

This protocol is deliberately strict about one failure mode: opening a professional file, writing a
nice-sounding report about what's in it, and learning nothing operational. A report is not the goal.
The goal, matching the existing knowledge system's own promotion lifecycle in
`docs/KNOWLEDGE_SYSTEM.md` (`CAPTURED -> INTERPRETED -> CANDIDATE -> EXPERIMENTALLY_TESTED ->
TRANSFER_VALIDATED -> RUNTIME_VALIDATED -> PROMOTED`), is a capability that measurably changes what
the modeling agent does on its next real task. This protocol is a specialization of that same
lifecycle for `.blend` sources, registered in the same `knowledge/foundation/source_registry.json` --
not a second, disconnected knowledge database.

## The loop

```text
SOURCE BLEND
  -> INSPECT            (open read-only, preserve the original, record raw facts)
  -> UNDERSTAND          (separate observed fact from inference about intent/workflow)
  -> EXTRACT PRINCIPLE   (state the transferable rule, not the object-specific recipe)
  -> REPRODUCE           (build a small controlled Blender experiment testing the principle)
  -> TRANSFER            (apply the same principle to DIFFERENT geometry, a different shape family)
  -> VALIDATE            (does it actually transfer, or was the first result a coincidence?)
  -> STORE               (source_registry.json + an operator card, same schema as every other source)
  -> APPLY               (use it on a real modeling task, not a synthetic fixture)
  -> MEASURE             (did the real task's result actually improve -- state this honestly either way)
```

Do not stop after INSPECT. Do not stop after EXTRACT PRINCIPLE with only a written description. A
principle that has not been reproduced, transferred to different geometry, and applied to a real task
is `CANDIDATE` at best, not `PROMOTED` -- use the existing lifecycle states honestly.

## Per-file inspection checklist

For each `.blend`, working read-only (open it, never save over it, never edit the original file):

1. **Preserve the original.** Open via a script that reads data and does not call
   `bpy.ops.wm.save_mainfile`. If a copy is more convenient for interactive exploration, copy first
   and note that the working copy is a copy.
2. **Inventory**: every object, its type, vertex/edge/face counts (base mesh, not just evaluated),
   modifier stack (type, order, key parameters), materials, UV layers, collections, naming
   conventions, and any objects that look like construction aids, reference images, or abandoned WIP
   attempts left in the scene.
3. **Modeling strategy**: is the primary form a single continuous cage, a primitive assembly, a
   lofted/revolved profile, or a component decomposition into genuinely separate parts? What decides
   the boundary between "one connected mesh" and "a separate object" in this file?
4. **Topology and edge flow**: valence distribution, pole placement and whether poles sit in flat or
   curved regions, support-loop spacing near sharp features, n-gon/triangle usage and whether it's in
   a planar or curved region (`knowledge/foundation/operator_cards/topology_context_subd.md` already
   has the "not a defect by category" framing -- does this file confirm, extend, or contradict it?).
5. **Bevel/edge intent**: which edges carry a Bevel weight or crease, what the Bevel modifier's limit
   method and segment count are, and whether that pattern matches this project's own established
   policy in `knowledge/foundation/operator_cards/smooth_by_angle.md` or reveals something that policy
   is missing.
6. **Modifier stacks and ordering**: what's present (Bevel, Subdivision Surface, Mirror, Solidify,
   Array, etc.), in what order, and why that order matters for the result.
7. **SubD cage vs. evaluated surface**: how sparse is the control cage relative to the smoothed
   result, and what does that ratio suggest about how much geometric detail belongs in the base mesh
   versus how much the modifier should carry.
8. **Shading/highlight behavior**: Smooth by Angle vs. per-object smooth shading vs. custom split
   normals, and whether hard/soft transitions line up with genuine design edges or something else.
9. **Reconstruct the likely modeling workflow** as an explicit ordered narrative, and **tag every
   claim in it as OBSERVED (directly read from the file) or INFERRED (a plausible guess about intent
   or process)**. Do not blend the two without saying which is which.

## What NOT to do

- Do not copy the source mesh, exact vertex positions, or hard-code the source object's dimensions
  into any future construction script.
- Do not build an asset-specific builder keyed to this one file's specific shape.
- Do not use a studied file's geometry, measurements, or presence to manufacture a benchmark pass.
- Do not let a studied file's specific choices silently override existing project knowledge if they
  conflict. Record the contradiction explicitly and investigate it experimentally (build both ways,
  compare) rather than picking one side by assumption.
- Do not claim a technique transfers because it worked once on one shape. One success is not
  generalization -- this project has hit that exact mistake before (see `docs/KNOWLEDGE_SYSTEM.md`'s
  claim boundary section).

## When something can't be inspected

Say so directly in the record rather than guessing or fabricating an observation. If a lesson has
been reproduced but not yet transferred to a different shape, mark it `EXPERIMENTAL`, not
`VALIDATED` -- these are the existing lifecycle states in `knowledge/foundation/source_registry.json`
and `docs/KNOWLEDGE_SYSTEM.md`, reused here rather than invented fresh.

## Research use

Use the browser only for a genuine, specific knowledge gap encountered while interpreting a file (for
example: "why would a professional route a support loop here rather than there" when the file's own
evidence doesn't make it obvious) -- prefer the official Blender Manual/API, Blender Studio, and
established professional educators/technical communities, per the existing source hierarchy in
`docs/KNOWLEDGE_SYSTEM.md`. Do not re-research something the repository has already studied. Collecting
links is not research; reproducing and testing the technique is.

## Storage

Register each studied file as a source in `knowledge/foundation/source_registry.json` with
`source_type: "professional_blend_file"`, `local_path` set to the file's path, and an `access`
modality of `blend_data: true` (the existing `text/video/audio/captions` modalities don't fit a mesh
data source, so this is a deliberate, minimal schema extension, not a parallel system). Direct
observations, candidate principles, reproduction experiments, and transfer evidence go in the same
`metadata` shape every other source already uses. Durable, reusable lessons still belong in
`knowledge/foundation/operator_cards/` alongside every other operator card -- update an existing card
when a studied file adds to a topic that already has one, rather than creating a duplicate.

## Future connection to video study (not yet possible)

A user-directed critique (2026-08-13) named a genuinely stronger version of this protocol: if a
tutorial's own working `.blend` is available alongside its video, correlate video timestamp -> what
the artist said -> what they did -> what actually changed in the `.blend` file, rather than studying
either source alone. That is a real improvement over this protocol's current file-only study loop,
but it requires the video-understanding pipeline in `docs/VIDEO_EXTRACTION_PROTOCOL.md` (speech/action
alignment, Blender-action recognition) to exist first -- none of the ten files studied so far
(`runs/2026-08-13_blend-file-study/`) came with a paired tutorial video, so this remains a documented
future direction, not a capability to apply yet.
