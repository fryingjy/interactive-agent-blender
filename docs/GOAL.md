# Living Project Goal

Status: **PARTIAL — perception-to-geometry capability is the active gate**  
Last reviewed: **2026-09-04**

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

Evidence update — 2026-09-04 (repository V2 consolidation): the active tree now has one explicit
geometry authority (`modeling_core`), one typed Blender mutation authority (`blender_ops`), and one
pipeline CLI (`tools/modeling_pipeline.py`). Parallel heuristic reconstruction/strategy modules,
destructive repair code, stale addon code, thin duplicate CLIs, and overlapping policy documents
were removed with import/reference evidence recorded in `CONSOLIDATION_AUDIT.md`. Runtime retrieval
now excludes candidate and historical knowledge. This reduces architectural ambiguity but does not
advance P0 by itself; P0 still requires a successful real held-out multiview reference-to-blockout
demonstration after the neutral regression proves that consolidation preserved the machinery.

Evidence update — 2026-09-04 (professional-capability diagnosis): current 3D-agent research and a
read-only sample of 13 weapon/hard-surface files show that more tools or shape families alone will
not close the quality gap. The missing bridge is an apprenticeship loop that pairs visual intent
with construction decisions, reproduces each decision on neutral geometry, transfers it to a
different family, and then tests it in an adaptive repair. The sample contained 322 mesh objects:
272 were internally connected, while complete assets still used separate objects for genuine
assemblies; 176 used SubD, 100 Bevel, 116 Mirror, and only 24 carried crease attributes. A focused
battle-axe file used five internally connected, nearly all-quad components with live SubD and
selective full-strength creases. This rejects both primitive spam and a universal "everything must
be one object/use creases/use bevel" rule. The prop ladder is therefore paused behind the active
`capability_bootstrap` in `progressive_prop_benchmark_curriculum.json`; no held-out result may count
until reference-to-form, construction-grammar, surface-control, and adaptive-repair drills pass
reproduction and cross-family transfer.

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

Evidence update — 2026-09-02 (candidate-initialization cycle 2): calibrated perspective component
masks can now initialize the same executable family set without target-authored coordinates. The
solver validates rigid world-to-camera matrices, triangulates component-center rays, rejects weak
camera rank/conditioning, and fits an axis-aligned 3D box against the projected bounds of all eight
corners. Perspective profile rays are intersected with a solved X/Z plane instead of being treated
as orthographic measurements. Controlled tests recover translated nonuniform bounds, reject
duplicate cameras and non-rigid calibration, and preserve family ambiguity when the evidence does
not distinguish two valid explanations. A separate one-hole fixture completed calibrated masks →
automatic candidate initialization → ring-versus-solid competition → correct ring selection →
typed Blender compilation. Fresh Blender 5.2.1 execution and independent verification produced a
closed 48-vertex/48-quad cage with zero invalid non-manifold edges, boundaries, n-gons, loose
geometry, degenerates, or winding conflicts. This proves calibrated multiview perspective bounds,
not calibration or semantic perception from ordinary photographs. The next P0 gap is automatic
component and cross-view correspondence proposals with explicit confidence and correction hooks.

Evidence update — 2026-09-02 (component-proposal cycle 1): the repository now has a local,
deterministic prior for missing component labels. It proposes Lab-color appearance regions only
inside a hash-verified object mask, emits editable labels and previews, and records cluster
selection, fragmentation, dispersion, and confidence. A cross-view matcher uses global assignment
over color, visible area, and aspect descriptors; unmatched and low-margin alternatives remain
explicit. Controlled transfer tests show that it discovers a two-finish split, avoids inventing
multiple regions on a uniform object, follows appearance when left/right positions reverse,
preserves equal-descriptor ambiguity, and rejects stale label artifacts. The proposal records are
hard-coded as non-semantic and cannot enter a shape bundle until edited labels receive explicit
component IDs through the existing annotation contract. This is a useful correction hook and CPU
baseline, not general part understanding: same-colored assemblies, lighting gradients, occlusion,
and texture can defeat it. The next scoped gap is a confirmation/materialization bridge plus a
stronger optional segmentation adapter evaluated under the same fail-closed contract.

Evidence update — 2026-09-02 (component-proposal cycle 2): reviewed cross-view proposals can now be
materialized into the existing semantic component-evidence contract. The bridge requires complete
one-to-one group assignments, unique shared component IDs, an explicit
`CONFIRM_COMPONENT_IDENTITY` decision, reviewer identity and timestamp, current source/mask/label
hashes, and full proposal-pixel coverage in every view. It records the correspondence hash and
confirmation inside each per-view evidence file. A controlled two-view test reversed the regions'
screen positions, recovered shared IDs from appearance matching, materialized both views, and
passed the normal multiview bundle with two-view support for each component. Missing groups and a
generic approval decision fail closed. This closes the review/materialization plumbing, not visual
semantics. The remaining P0 perception gap is a stronger optional segmentation adapter and its
evaluation on ordinary multi-angle photographs, followed by correspondence/camera evidence that
does not depend on controlled color separation.

Evidence update — 2026-09-02 (component-proposal cycle 3): the deterministic proposer was run on
the supplied tactical-axe product reference rather than another synthetic fixture. Object-mask
extraction passed, but the appearance model incorrectly separated shading/highlights: its smaller
region covered 5.6% of the object and fragmented into 177 islands, reducing proposal confidence to
0.0056. The pipeline now classifies that result as `REVIEW_REQUIRED_LOW_CONFIDENCE`, records both
defects, and propagates proposal quality into cross-view match confidence. This is useful negative
evidence: separable background does not imply usable part segmentation, especially for same-finish
hard-surface assemblies. A provider-agnostic external adapter now accepts stronger label maps with
declared provider/model/version and per-region confidence, while enforcing complete verified-mask
coverage, zero background leakage, hash provenance, fragmentation penalties, and the same mandatory
review/confirmation boundary. Controlled tests prove that it can preserve two same-color supplied
part labels and rejects leakage or missing confidence. The next P0 work is to exercise a genuinely
strong segmenter on ordinary multi-angle references and evaluate cross-view identity jointly with
camera/correspondence evidence; the local color baseline is now correctly bounded rather than
mistaken for that solution.

Evidence update — 2026-09-02 (component-proposal cycle 4): current official Gemini image
understanding supports segmentation polygons, so a hash-bound remote provider path was implemented
and exercised with the configured key on the supplied tactical axe. The key is now proven usable;
an initial `gemini-3.7-flash` request rejected the documented minimal-thinking setting and a retry
hit temporary model demand, while `gemini-3.6-flash` completed. Gemini correctly identified the
steel head/full-tang body and attached textured handle scale, with later prompting avoiding
highlight clusters and unnecessary fasteners. Integration testing caught provider drift: returned
polygons used `[y,x]` despite the requested/documented `[x,y]`; coordinate order is now selected and
recorded only when each polygon's own box disambiguates it. The best raw masks still covered only
87.62% of the verified silhouette and overlapped on 13.21%, so they were not accepted directly.
Their exclusive interiors seeded a bounded watershed partition. The final mask covered the object
completely, had no overlap, and its internal part boundary measured 1.54× the object-interior
gradient baseline. After raw-error confidence penalties and an explicit host-occlusion exception
for the steel visible on both sides of the handle scale, the external adapter produced a 0.714
`REVIEWABLE_PROPOSAL`; it remains non-semantic and review-required. This is the first real-image
strong-model segmentation transfer, but it is one view and one target. The next P0 gap is repeated
multi-angle segmentation/correspondence on an identity-audited variant, jointly constrained with
camera evidence rather than appearance alone.

Evidence update — 2026-09-04 (component-proposal cycle 5, contract correction): an exact-variant
ZT0102 audit found that the prior Gemini adapter contradicted the current official segmentation
contract. Gemini 3.8 returns `[ymin,xmin,ymax,xmax]` full-image boxes and `[x,y]` polygons normalized
inside each box; the old full-image-polygon prompt and coordinate-order guessing produced unstable
part boundaries. Prompt v3 now follows the documented box-local transform exactly, normalizes
16-bit catalog PNGs to bounded 8-bit request images, and can replay hash-bound provider responses.
It also distinguishes component-segmentation eligibility from silhouette-fitting eligibility, so a
useful crop may propose visible parts without pretending to be a complete fitting view.

The same untouched full-profile image then exposed and fixed a second modeling fact: a continuous
steel host is legitimately described behind an attached G10 scale, but visible component labels
must be exclusive. Role-aware compositing now subtracts only declared `ATTACHED_ASSEMBLY`/`INSERT`
pixels from a `PRIMARY_VOLUME`; peer overlaps still fail. On the full profile, raw box-local masks
covered 62.14% and overlapped 34.19%, all of that overlap was the declared scale-over-host relation,
and a bounded watershed produced a complete exclusive partition whose internal boundary had 2.12x
the object-interior gradient baseline. Visual inspection showed the boundary following the scale
perimeter instead of the earlier diagonal/winding split. An opposite-face head detail transferred
with 82.56% raw coverage and a 3.57x boundary ratio. Cross-view matching grouped both components
without unmatched regions; the scale match reached 0.735 confidence while the cropped host match
correctly remained ambiguous at 0.442. An independent retailer profile failed closed at a 0.612
boundary ratio. The exact reference audit also found only one full-object viewpoint family despite
multiple URLs, so the set remains `TARGETED_RESEARCH`. This is a real visible correction and
partial transfer, not a P0 exit: multi-source component boundaries and full-object depth are still
unproved.

Current priority order:

1. **Establish a scored baseline** — run small non-held-out reference tasks through the current
   system unchanged and record where form, depth, construction, surface, or repair judgment fails.
2. **Reference-to-form apprenticeship** — practice multiview landmarks, depth/overlap reconciliation,
   and rejection of unsupported hidden-form hypotheses before topology refinement.
3. **Construction-grammar apprenticeship** — reproduce and transfer connected profile cages,
   box/SubD edge intent, radial continuous details, and genuine assembly boundaries from inspected
   examples and tutorials without copying source geometry.
4. **Surface-control apprenticeship** — compare crease, support-loop, bevel, weighted-normal, flat,
   and Smooth-by-Angle choices through base-cage, evaluated, and highlight renders; promote only
   choices that transfer across shape families.
5. **Adaptive critic and repair** — require evidence for every applicable review criterion, localize
   the highest-impact visible defect, make one bounded live edit, and accept, rollback, or change
   representation from measured before/after evidence.
6. **Resume P0 on a real target** — only after the four bootstrap tracks pass, acquire an exact-
   variant multiview target and run the complete reference-to-blockout exit path below.

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
