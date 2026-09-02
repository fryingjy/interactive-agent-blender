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

Evidence update — 2026-09-02 (component/multiview cycle): editable grayscale component labels are
now bound to each source hash and checked for silhouette coverage, background leakage, visible
regions, and adjacency. A multiview bundle now accepts only unique images authorized by the existing
same-target/variant audit and authoritative under the existing registration gate; it also enforces
declared cross-view component support. This closes the mechanical evidence-binding gap, not semantic
understanding: component IDs are still explicit annotations, and the system cannot independently
recognize that two arbitrary photographs show the same variant. The next highest-value work is to
turn these per-view component observations into competing component graphs and generic assembly
representations while preserving uncertainty about occlusion and hidden structure.

Evidence update — 2026-09-02 (assembly-hypothesis cycle): bundled component observations now produce
generic per-component representation candidates and explicit continuous-cage versus separate-object
graph candidates. Projected adjacency never chooses topology. An edge resolves only from independent,
view-hash-bound observations of seams, continuous surface flow, projected separation, or verified motion;
one-view and contradictory evidence stay unresolved. The output explicitly remains construction-
blocked while component shape families are unselected. The next gap is component-level multiview
family fitting and competition, followed by compiling a resolved mixed graph into typed Blender
transactions without collapsing continuous regions or fragmenting genuine assemblies.

Evidence update — 2026-09-02 (component-fitting cycle): each component can now fit and compete
executable families against its own hash-bound masks under fixed shared cameras, with bounded
object-space translation and an ambiguity margin. A controlled two-component fixture recovered
placement, selected different families for the two parts, compiled a resolved separate assembly,
and passed fresh Blender 5.2.1 typed execution plus independent verification on both objects. Camera
optimization during family competition is rejected. Continuous relationships also reject
compilation rather than joining independent meshes. The next highest-value gap is a real shared-cage
continuity compiler, followed by broader component families and localized refit tickets derived from
per-component/per-view residuals.

Evidence update — 2026-09-02 (continuity-compilation cycle): evidence-resolved mixed graphs now
compile without primitive joining or forced object collapse. Continuous groups require explicit
unused boundary-port bindings, equal loop cardinality, and a measured maximum bridge span;
coincident loops weld and bounded separated loops bridge with quads. Separate groups remain separate
objects and all modifiers remain unapplied. Unit tests cover weld, bridge, mixed graphs, port reuse,
cardinality mismatch, and span rejection. A fresh Blender 5.2.1 process created a 48-vertex,
36-quad bridged cage, and independent verification found zero invalid non-manifold edges, n-gons,
loose geometry, degenerate faces, or winding conflicts. This proves only linear compatible-port
continuity, not arbitrary fusion, loop resampling, or branch junctions. The next highest-value gap
is broader generic component families plus localized refit tickets from per-view/component
residuals; those are needed before a real P0 exit target can be attempted defensibly.

Evidence update — 2026-09-02 (localized-refit cycle): retained component fits now emit prioritized
component/view tickets from their actual silhouette, contour, and negative-space residuals. The
diagnostic layer probes only declared bounded shape parameters and recommends a direction only when
the target view improves without materially regressing the multiview mean. Probes never mutate the
fit. A missing negative space escalates directly to family or component-graph change, and a residual
with no safe local lever is labeled as a representation/bounds problem. The next P0 capability gap
is representation breadth: radial/revolved, curved sweep, bent profile, shell, and opening-bearing
families must become executable and compete under the same fixed-view evidence contract.

Evidence update — 2026-09-02 (representation-breadth cycle 1): `profile_revolution` and
transported-frame `curve_sweep` are now executable generic families, not planner-only labels. They
validate bounded semantic parameters, build connected open all-quad cages, participate in CPU
silhouette fitting, compile through typed Blender commands, and expose compatible continuity ports.
Fresh Blender 5.2.1 execution and independent checks passed for both 48-vertex/36-quad fixtures with
zero invalid non-manifold edges, n-gons, loose geometry, degenerate faces, or winding conflicts. The
next breadth gap is not more radial duplication: it is shell/opening-bearing construction and bent
outline-led sheets, followed by evidence-driven family initialization rather than hand-authored
candidate starting values.

Evidence update — 2026-09-02 (representation-breadth cycle 2): `profile_sweep` now transports a
measured non-circular section along a 3D path, and `profile_ring_extrusion` builds a closed manifold
single-through-hole cage from corresponding outer/inner loops. The latter lets negative-space
evidence select an opening-bearing family over a solid extrusion instead of merely rejecting both.
This cycle also corrected a fitting defect: open volume cages viewed down their uncapped axis could
rasterize as outlines. The CPU renderer now derives boundary cycles and fills virtual caps in the
silhouette only; Blender topology stays open and editable. Fresh Blender 5.2.1 checks proved a
16-vertex/16-quad closed ring with zero boundary or invalid non-manifold edges and a bent
16-vertex/12-quad profile sweep with only its two intentional open boundaries; both had zero n-gons,
loose geometry, degenerates, or winding conflicts. Scope remains narrow: one corresponding-loop
opening is not arbitrary boolean topology or a general shell system. The largest P0 gap is now
evidence-derived candidate initialization and bounds, followed by automatic component labels and
cross-view correspondences on ordinary photographs.

Evidence update — 2026-09-02 (candidate-initialization cycle 1): registered orthographic component
masks can now initialize executable section-loft, outline-extrusion, radial, and single-through-hole
candidates without target-authored coordinates. The solver reconstructs world center and
axis-aligned half-extents from camera rows and silhouette bounds, requires full rank for both,
derives profile geometry from a stable X/Z view, and sizes parameter bounds from pixel scale and
solve residual. Duplicate/mismatched view identities, stale label hashes, collapsed axes, and
rank-deficient depth fail closed. A controlled one-hole component completed masks → automatic
candidate initialization → three-family competition → correct ring-family selection → typed Blender
compilation. Fresh Blender 5.2.1 verification found the automatically initialized winner to be a
closed 48-vertex/48-quad cage with zero boundary or invalid non-manifold edges, n-gons, loose
geometry, degenerates, or winding conflicts. This does not close P0: it is orthographic-only
initialization on explicit component labels. The next scoped gap is calibrated-perspective
initialization, followed by automatic component/correspondence proposals with confidence and
correction hooks on ordinary photographs.

Current priority order:

1. **Reference acquisition and provenance** — collect local or online multi-angle evidence, retain
   source URLs/paths and licenses where relevant, reject unrelated variants, and record uncertainty.
2. **Image evidence extraction** — normalize/crop views and derive editable object masks,
   silhouettes, landmarks, component regions, overlaps, and negative spaces with confidence and
   manual correction hooks.
3. **Camera and correspondence solving** — initialize orthographic/perspective views from image
   evidence, report reprojection error, and reject underconstrained calibration.
4. **Complete evidence-derived candidate initialization** — extend the proved orthographic path to
   calibrated perspective views and path/repeated families while retaining rank, residual, and
   uncertainty diagnostics instead of relying on hand-authored candidate coordinates.
5. **Remaining representation and fitting gaps** — add only evidence-justified shell,
   multi-opening, repeated, or branch families; preserve per-view/component disagreement and convert
   contour, landmark, depth, overlap, and negative-space errors into scoped modeling work.
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
