# Living Project Goal

Status: **PARTIAL — perception-to-geometry capability is the active gate**  
Last reviewed: **2026-09-02**

This is the repository's mutable execution goal. The durable operating contract remains
[`MASTER_DIRECTIVE.md`](MASTER_DIRECTIVE.md). If this page conflicts with current code or
reproducible Blender evidence, update this page; do not reinterpret the evidence to preserve an
old plan.

## North star

Build and prove a generalizable reference-driven Blender modeler that can reconstruct unfamiliar
hard-surface props and weapons with convincing form, appropriate editable construction, and
evidence-based self-correction.

The system must decide what geometry should exist before polishing it. It must gather enough
reference evidence, preserve ambiguity, compare competing 3D explanations, construct the selected
interpretation incrementally in Blender, inspect the actual cage/evaluated surface/appearance, and
repair or rebuild when the result is wrong.

## What does not count

None of these independently demonstrate the goal:

- a technically clean mesh whose silhouette or proportions are wrong;
- one successful prop, one view, or one target-specific builder;
- primitive spam, or joining unrelated primitives after the fact;
- forcing physically separate assemblies into one continuous mesh;
- all-quads, modifier use, test count, tutorial count, or source count without visible quality gain;
- smooth shading used to conceal unauthored hard edges;
- a polished render without an editable source cage;
- a human correction reported as autonomous success.

## Completion contract

Completion requires at least **three consecutive held-out props** spanning at least **two distinct
construction families**. The targets must be frozen before modeling and must not receive
target-specific code or post-freeze target research. Each result must:

1. use multiple-angle evidence sufficient to constrain silhouette, depth, components, overlap, and
   important negative spaces;
2. compare at least two plausible representation or shape hypotheses when ambiguity exists;
3. achieve convincing major-form, proportion, component, and negative-space agreement across the
   relevant views without a `REJECT_MAJOR_FORM` result;
4. use intentional editable construction: connected topology where material/form is continuous and
   separate objects where real assembly boundaries justify them;
5. preserve unapplied modifiers and separate high/low collections when those deliverables apply;
6. pass independent technical checks without using those checks as a proxy for visual quality;
7. demonstrate at least one autonomous repair, rollback, or representation change based on measured
   evidence; and
8. leave a reproducible `.blend`, diagnostic comparisons, decision history, limitations, and an
   honest post-build review.

One failed held-out prop resets the consecutive-success count. A contaminated benchmark is evidence
for development, not evidence for completion.

## Mutable current phase

### Gate P0 — Turn references into constrained geometry

The control plane is strong and the first bounded shape solver is real. The largest gap is now the
path from ordinary images to a defensible multi-part 3D hypothesis.

Evidence update — 2026-09-02: the repository now has a source-hashed, fail-closed extraction path
for alpha and clean-background isolated-object images. It emits editable masks, normalized crops,
outline landmarks, width profiles, extrema, centroids, and enclosed negative spaces; edited masks
can be re-ingested with their own hashes. Controlled fixtures and a real supplied sword concept
proved this narrow case. General photographs, variant selection, semantic components, cross-view
identity, and automatic correspondences remain unproved. The active priority therefore remains P0,
with multi-view acquisition and component-aware evidence as the next gap rather than another prop.

Current priority order:

1. **Reference acquisition and provenance** — collect local or online multi-angle evidence, retain
   source URLs/paths and licenses where relevant, reject unrelated variants, and record uncertainty.
2. **Image evidence extraction** — normalize/crop views and derive editable object masks,
   silhouettes, landmarks, component regions, overlaps, and negative spaces with confidence and
   manual correction hooks.
3. **Camera and correspondence solving** — initialize orthographic/perspective views from image
   evidence, report reprojection error, and reject underconstrained calibration.
4. **Representation and assembly hypotheses** — expand beyond section loft and profile extrusion to
   component graphs, repeated/radial parts, bent profiles, shells, openings, and real assembly
   boundaries without target-named builders.
5. **Cross-view fitting and localized diagnosis** — preserve per-view/component disagreement and
   convert contour, landmark, depth, overlap, and negative-space errors into scoped modeling work.
6. **Blender visual closure** — compare controlled solid, silhouette, wireframe, and evaluated views;
   refit, repair, or change family before secondary detail.

P0 exits only when one real, previously unused, multi-view reference can move through:

```text
images
-> provenance + normalized evidence
-> masks/landmarks/components + camera hypotheses
-> competing generic 3D interpretations
-> compatible fitted blockout
-> typed Blender transaction
-> controlled comparison renders
-> localized correction or justified rejection
```

The exit artifact is a blockout, not a polished prop. It must prove that image evidence—not invented
coordinates—determined the major form.

### Next phases

- **P1 — Representation breadth:** pass controlled transfer tests for axial, outline-led, radial,
  bent, shelled, opening-bearing, and multi-part forms.
- **P2 — Adaptive Blender construction:** demonstrate scoped edit-mode decisions, modifiers,
  continuity/assembly choices, recovery, and evaluated-surface inspection on non-held-out exercises.
- **P3 — Progressive benchmarks:** simple single-component targets first, then low-component
  assemblies, then more difficult weapons/props. Complexity advances only after breadth at the
  current level.
- **P4 — Production readiness:** topology/surface refinement, UV/material requirements, high/low
  organization, naming, export, and final review appropriate to each brief.
- **P5 — Generalization claim:** run the completion contract without changing thresholds after
  seeing the targets.

## Modeling policy

- Choose box/poly, SubD, curves, booleans, profile modeling, radial construction, sculpt/retopo, or a
  hybrid from the surface and deliverable—not from a universal slogan.
- Start from a box when the dominant form is box-like; do not pre-round corners that must remain
  sharp. Use enough circular segments for the visible result, commonly 12–16 at blockout scale.
- Add edge loops and extrude continuous features from a shared cage when that creates meaningful
  flow. Do not add cylinders merely to imitate rings that belong to the same manufactured body.
- Keep fasteners, hinges, blades, handles, inserts, and other genuine assemblies separate when that
  improves correctness and editability.
- Select crease, support loops, bevel/weighted bevel, weighted normals, flat shading, or auto smooth
  from the desired edge and highlight behavior. Do not blanket-smooth the scene.
- Keep modifiers live unless the brief explicitly requires application. Inspect both base and
  evaluated geometry.
- Prefer inexpensive solid/workbench diagnostics while iterating; render complexity must not slow
  form correction.

## Living update protocol

Update this page whenever evidence changes the highest-value next work. Every substantive cycle
must perform these steps:

1. record the observed capability failure or newly proved capability;
2. identify whether it changes the active gate, priority order, exit criterion, or benchmark
   readiness;
3. modify the relevant section instead of appending another competing roadmap;
4. preserve durable failures in tests or evidence records, not as stale implementation queues;
5. remove or consolidate superseded code/docs only after confirming they are genuinely redundant;
6. run tests, audits, and proportional Blender verification;
7. commit and push the goal update with the implementation/evidence that justified it.

The north star and completion contract change only when user intent or strong evidence changes the
definition of success. The current phase and priority order are expected to change often.

At each update ask:

> What is the highest-impact thing a proficient modeler would notice, infer, choose, or correct here
> that the system still cannot?

That answer becomes the next scoped objective.
