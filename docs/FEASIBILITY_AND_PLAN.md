# Professional Reference-Driven Modeling Tool

## Executive assessment

A useful tool for producing a bounded class of professional game props is a plausible engineering objective. A reliable autonomous replacement for a professional modeler across arbitrary references, styles, and production constraints is not established by the evidence reviewed. The correct initial target is a supervised asset-production tool whose outputs can earn acceptance, not a system that declares itself professional.

The first supported class should be rigid hard-surface game props and relatively simple weapons: clean silhouettes, modest component counts, controllable curvature, and no character rigging or sculpt-heavy ornament. This scope matches the intended work while allowing visual accuracy, topology, editing, and engine delivery to be evaluated together. Success in this class must not be advertised as character, vehicle, or general organic-modeling expertise.

There is a separate market obstacle. HiddenDevs' application rules prohibit AI-generated or modified examples and examples produced or modified through automation. They also exclude tutorial-based examples. Its 3D Modeler application requires at least three sophisticated models viewable in 3D, with appropriate textures or colors; screenshots alone do not qualify. These are application rules, not verified evidence of every commission-channel policy. Written clarification from staff is needed before relying on that market for AI-assisted commissions. [1](https://www.hiddendevs.com/bulletin?id=2)

Recommendation: continue developing an explicitly AI-assisted tool, but do not submit its output as manually authored skill-role evidence or promise HiddenDevs eligibility. If that marketplace does not permit the intended workflow, choose a permitted market or use the tool for private study and production assistance under appropriate terms. Concealing automation is not a viable product strategy.

## Evidence and uncertainty

This assessment uses public information checked on September 10, 2026. It is a feasibility analysis, not a completed system benchmark. No tutorial was watched or reproduced for this report; a video syllabus is proposed below. No generator was installed or tested, and no customer-demand or pricing study was completed inside Discord. Public repository descriptions establish candidate capabilities, not independently verified quality or security.

The fresh local repository contains no inherited runtime or benchmark assets. Existing installed Blender and external reference libraries remain separate. Direct workstation checks found Blender 5.2.1 LTS, Python 3.12, Git, FFmpeg, approximately 11.8 GiB physical RAM, and an Intel UHD display adapter. NVIDIA tooling was not available on PATH. This does not rule out unreported external hardware, but a CUDA-capable workstation must not be assumed.

Some version-specific Blender documentation pages could not be retrieved. The accessible BMesh documentation includes development-version material; actual operation signatures must be tested against the installed 5.2 runtime before implementation. Roblox texture documentation contains conflicting resolution statements, so a single universal maximum must not be hardcoded without asset-class-specific verification.

## What professional quality means

Professional status is a judgment about dependable delivered work. It is not a polygon count, a collection of modifier presets, a model subscription, or an attractive thumbnail. The tool should optimize for a client receiving an accurate, usable asset and being able to request predictable revisions.

The proposed quality contract has six independent dimensions:

| Dimension | Evidence required | Failure that cannot be averaged away |
| --- | --- | --- |
| Reference fidelity | Matched views, component proportions, landmarks, negative spaces | Wrong primary form despite attractive shading |
| Surface quality | Neutral studio lighting, close-ups, evaluated geometry | Pinching, unintended faceting, soft mechanical edges |
| Construction and editability | Inspectable base cage, purposeful components, live modifiers | Inseparable generated mesh or disconnected geometry hiding a required continuous form |
| Game readiness | Target-specific export/import and playback inspection | Missing textures, bad scale, excessive cost, unusable collision |
| Revision reliability | Local requested edit without unrelated degradation | Entire asset must be regenerated for a minor change |
| Commercial suitability | Clear authorship, permitted inputs and workflow, scoped delivery | Prohibited marketplace use or unauthorized reference redistribution |

For Roblox, the current general modeling specification states a 20,000-triangle maximum per individual mesh and describes watertight, non-zero-volume geometry. Specialized avatar and accessory rules differ. This is a compatibility ceiling, not an appropriate target budget for every prop. The brief must set a smaller budget where needed. [2](https://create.roblox.com/docs/art/modeling/specifications)

Texture delivery requires UV and material planning, not merely Blender shader nodes. Roblox documents a single material per mesh object, PBR maps, and OpenGL tangent-space normals. Its texture page currently lists differing resolution limits in different sections; validate the relevant asset type in Studio and record the tested budget. [3](https://create.roblox.com/docs/art/modeling/texture-specifications)

The importer supports mesh hierarchies and production data, but a supported file extension alone is not a successful delivery. Reimport in the destination application is mandatory. [4](https://github.com/Roblox/creator-docs/blob/main/content/en-us/studio/importer.md)

## Technical feasibility and current research

Three different problems are often conflated: controlling Blender, reconstructing an image, and delivering a professional asset. A bridge solves the first. Image-to-3D systems address part of the second. Neither automatically supplies the third.

The recent SEIG work, *Thinking in Blender*, reports gains from separating scene factors into stages and using stage-specific generator/verifier feedback. It also acknowledges single-view ambiguity: different hidden structures can explain the same visible image. Its evaluation includes rendered-image comparisons and mesh registration; that is not equivalent to an unassisted client revision or a game-ready delivery test. The useful lesson is bounded, localized correction—not copying its whole architecture or treating its examples as professional certification. [5](https://arxiv.org/html/2606.02580v1)

3DCodeBench provides a more systematic way to test procedural modeling agents using aligned procedural examples, reference conditions, and evaluations. Its benchmark is useful as an external test source after checking asset and code licenses. It does not establish that a model can independently handle arbitrary commission briefs, UVs, export issues, and revisions. Benchmark performance should be supplementary evidence, not the release gate. [6](https://arxiv.org/html/2606.01057v1)

TRELLIS.2 is a candidate image-to-3D proposal generator with PBR output. The repository specifies Linux testing and at least 24 GB NVIDIA GPU memory; headline generation timings are measured on an H100. Its code/model license and dependency licenses are explicitly separate. The current workstation is not a demonstrated fit for the documented installation. Generated geometry could be a spatial starting point, but clean controllable construction and exact reference correspondence still need evaluation. [7](https://github.com/microsoft/TRELLIS.2)

Hunyuan3D-2.1 is another shape-and-texture candidate. Its repository lists 10 GB VRAM for shape, 21 GB for texture, and 29 GB for the combined process. It is not a sensible default local dependency on this machine. If evaluated later through a hosted route, inspect commercial terms, confidentiality, total repair time, and cost before adoption. [8](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1)

Analytical conclusion: start with reference-guided editable modeling and controlled visual feedback. Compare a generated prior only if a real failure suggests it can reduce total delivery work. More tools are useful only when they reduce a measured failure or the time to an accepted asset.

## Principal failure risks and their remedies

The earlier reported experience suggests several hypotheses. Because the old repository was deliberately erased, these are not presented as fresh source-code findings. The rebuild must test them directly.

**A plausible object replaces the specific reference.** Naming an object activates generic expectations, which can override observed geometry. Remedy: record measurable proportions, visible transitions, silhouette landmarks, and uncertain regions before choosing an edit. Every major modeling action must identify which observation it addresses.

**Camera error is mistaken for shape error.** A poor camera can make a reasonable shape look wrong; a freely adjusted camera can also hide a bad shape. Remedy: fit camera and geometry in separate controlled steps, preserve common image coordinates, and reserve an independent view when available. An estimated camera remains estimated.

**Outer silhouette hides assembly errors.** Intersections and wrongly occluded components can still create a convincing outline. Remedy: compare visible component boundaries, junctions, depth ordering, and section views, in addition to the full mask. Never independently stretch components in image space to manufacture a match.

**Primitives substitute for construction.** A pile of cylinders may describe a category while missing continuous surfaces and transitions. Remedy: choose components by physical/visual structure, then use extrusion, inset, loops, bridging, profiles, and controlled curvature within each component. Separate pieces remain valid for genuine assemblies. A single object with disconnected islands is not automatically connected topology.

**Shading disguises geometry.** Smooth shading cannot fix a rounded corner that should be square. Remedy: inspect the base cage and evaluated form before material polish. Choose crease, support loops, or bevel based on the required surface, rather than applying one everywhere.

**The critic keeps changing its opinion.** Free-form model self-review may oscillate or reward its own output. Remedy: a stable per-brief rubric, explicit discrepancy locations, fixed comparison views, and independent final review. No automatic promotion because an iteration budget was exhausted.

**Research accumulates without skill transfer.** Summaries can grow without improving decisions. Remedy: retain a lesson only after a reproduction and a changed-shape transfer exercise. If retrieval does not improve outcomes, simplify or remove it.

**Engineering progress substitutes for art progress.** More tests can validate an inaccurate modeler. Remedy: track artifact acceptance and revision success separately from runtime correctness. Add infrastructure only to enable or protect an actual modeling experiment.

## Minimum initial architecture

Use one Python package, one public entry point, and a Blender-side executor. The following are proposed responsibilities, not modules already implemented:

| Responsibility | Owns | Must not own |
| --- | --- | --- |
| Brief and evidence | References, provenance, constraints, landmarks, view uncertainty | Geometry mutation |
| Modeling controller | Next local decision, budget, strategy changes | A second Blender implementation |
| Blender runtime | Selection, mesh edits, modifiers, state capture, saves, renders | Self-awarded visual acceptance |
| Review | Image/component comparisons, technical findings, discrepancy records | Silent edits or changed acceptance rules |
| Delivery | Export copies, import checklist, package manifest | Overwriting editable source |

The authoritative workflow is:

`brief + references -> measured evidence -> construction choice -> local Blender edit -> inspect/compare -> repair or retain -> destination validation -> delivery`

Knowledge retrieval is a consulted resource, not another geometry engine. External generators, camera tools, or segmentation services enter through replaceable adapters that produce explicitly provisional evidence or geometry proposals.

Start with Blender's own editing API. BMesh exposes mesh connectivity and operations used by native editing tools, making connected edits feasible without automating every menu click. This is a mechanism for editing, not an artistic decision policy. [9](https://docs.blender.org/api/main/bmesh.html)

The minimal command vocabulary should cover state inspection, targeted selection, transform/extrude/inset, subdivide/bridge/dissolve, crease/bevel/SubD settings, component organization, render, and save. Add operations only when a selected exercise needs them. Avoid implementing all Blender menus before producing one useful result.

Each mutation needs an expected scene state, explicit target, changed-element report, and recoverable working checkpoint. Checkpoints are temporary project safety, not restoration of the deleted repository. Do not treat arbitrary Python execution as sandboxed. Use a dedicated Blender process, disable automatic execution when opening untrusted files, and constrain filesystem/network access where practical.

Public bridges are reference implementations worth comparing. The original Blender MCP exposes arbitrary code execution; it demonstrates connectivity, not secure professional modeling. The curated-tool approach in PatrykIti/blender-ai-mcp is another candidate, but its published complexity and compatibility claims warrant a small pinned-version trial before adoption. Do not install a large bridge merely to acquire more tool names. [10](https://github.com/ahujasid/blender-mcp/) [11](https://github.com/PatrykIti/blender-ai-mcp)

## Reference interpretation and construction policy

Use original designer/manufacturer images or permitted client references where possible. Pinterest and image search are discovery tools: follow the image to its source and record authorship, available views, and any restrictions. A pin does not establish rights to resell the pictured design. Do not combine different product variants as though they were photographs of one specimen.

For each brief, record front/side/oblique evidence, major dimensions or ratios, symmetry assumptions, negative spaces, surface transitions, and unknown hidden regions. If only one image exists, distinguish observed geometry from a plausible completion. A generated extra view is a hypothesis, not independent confirmation.

fSpy can estimate a camera from useful vanishing-point evidence and transfer its camera to Blender. It is a targeted option for photographs with suitable directional structure, not a universal shape solver. On sparse product photographs, use bounded camera hypotheses and uncertainty rather than forcing an unjustified calibration. [12](https://fspy.io/)

Construction defaults are conditional:

- Box modeling for planar housings and broad mechanical forms.
- Low-density profile loops and extrusion for blades, handles, and tapered forms.
- Curves or revolve-style construction for suitable continuous profiles.
- Mirror for actual symmetry, with asymmetric features introduced deliberately.
- Creases and support geometry for controlled SubD; bevels for actual edge breaks.
- Separate objects for distinct manufactured/moving/material assemblies, connected geometry where the surface must genuinely continue.

The Blender edge-data documentation distinguishes crease and bevel-weight controls. Neither is a substitute for correctly placed cage geometry. Exact 5.2 behavior should be covered by a small native experiment before exposing it through the runtime. [13](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/edge_data.html)

Do not hardcode 12, 16, or 32 radial vertices as a universal quality rule. Use the lowest density that meets projected silhouette and shading requirements at the intended viewing distance. Prefer quad-dominant editable cages where they support the surface; evaluate triangulated export geometry separately.

## Learning that changes modeling behavior

Use a problem-led syllabus rather than completing every Blender tutorial. Each study should yield an observable improvement on an asset and a concise reusable rule with preconditions and failure cases.

The initial syllabus is reference/camera interpretation; connected polygon modeling; SubD and edge control; UV seams and texel density; high-to-low baking; target-engine import; and revisions. CG Cookie's game-asset learning material is a candidate structured source covering the asset pipeline. The public descriptions were inspected, not the paid lessons; no subscription purchase is assumed. [14](https://www.cgcookie.com/collections)

A specific initial video candidate is Bartosz Pampuch's fSpy workflow, whose chapter list addresses principal point, focal length, dimensions, and depth mistakes. Its age makes interface details a version-checking task. It is queued study, not knowledge already validated. [15](https://www.youtube.com/watch?v=daiMOYR8GS8)

Google's Gemini API supports video input and public YouTube URLs, with timestamped analysis. Its documentation describes default frame sampling and newer adaptive video processing. Fast mesh edits can be missed; important actions require close interval inspection and reproduction. This API route should not be confused with assumptions about a consumer chat application's YouTube behavior. [16](https://ai.google.dev/gemini-api/docs/video-understanding)

The proposed learning procedure is: ask a narrow question; inspect the relevant interval and modalities; extract the before-state, selection, operation, parameters, intended effect, and result; reproduce in Blender; vary the shape; then apply to the current failure. Store the source/timestamp, tested version, preconditions, and outcome. Do not retain hours of video or claim competence from a summary.

Retained knowledge means external, testable project guidance. It is not evidence that a base model has been retrained. Keep lessons small enough to retrieve by the actual modeling problem.

## Implementation and proof sequence

These phases are dependency-ordered, not calendar promises. No reliable time-to-professional-status estimate exists before the baseline and repair cost are measured.

| Phase | Work | Exit evidence |
| --- | --- | --- |
| 0: Scope | Define first asset family, brief schema, review rubric, marketplace uncertainty | One unambiguous internal test brief; no sales claim |
| 1: Thin execution loop | Build inspect/edit/render/save with scoped checkpoints | One connected edit, save/reload, and actual rollback verified in Blender |
| 2: Reference baseline | Model a simple rigid prop from permitted multi-view references | Measured proportions plus independent-view inspection; failures recorded |
| 3: Controlled repair | Correct camera, primary form, and edge behavior separately | Improvements survive other views and do not corrupt the cage |
| 4: Complete delivery | UV/material workflow, high/low organization, export/import | Editable source plus working engine asset and no missing dependencies |
| 5: Revision test | Change a proportion, component, and surface instruction | Local edits preserve unrelated accepted requirements |
| 6: Transfer | Evaluate unseen briefs in the declared class | Independent acceptance with all attempts and intervention reported |

First proof assets should be small but not meaningless primitives: a simple shield, a straight-bladed dagger, and a small box-like prop with an actual inset or assembled feature. These are proposed exercise families, not permission to reuse the same recipe as a held-out result. Start with one; choose the next only after reviewing its failure pattern.

Do not advance complexity merely because a script succeeds. Conversely, do not spend many sessions perfecting a toy shape that no longer tests a weakness. After a fixed local repair allowance, report the remaining defect and change the experiment or strategy. Failing an exercise is not a reason to rewrite the whole system.

## Evaluation design and stop conditions

First compare two deliberately small approaches on the same development briefs: direct editable Blender construction with structured observations, and the same approach with stage-scoped independent critique. Keep tool access, reference images, time budget, and output requirements matched. Add an external 3D prior only as a later third arm if the baseline demonstrates a need.

Measure reference fidelity using both global and local evidence: silhouette overlap, landmark displacement, component ratios, visible junctions, and negative space. Measurements must use a shared image frame. Choose tolerances relative to the brief and image uncertainty before testing; do not invent a universal IoU score that declares all models professional.

Technical checks include disconnected islands, degenerates, normals, appropriate manifoldness, modifier state, transforms, UV validity, texture availability, and export budgets. Surface inspection includes an untextured view and neutral lighting. None of these alone provides artistic acceptance.

Use a reviewer who did not construct the asset for final pilot judgments; a second model is a useful critic but not sufficient independent evidence. Ideally a working game-prop artist reviews editable files and engine imports against a fixed rubric. No paid reviewer is engaged by this plan. Human help and review time must be recorded rather than hidden inside an autonomy claim.

Proposed internal pilot gate: ten unseen briefs across at least three supported rigid-prop families, at least eight accepted after no more than two revision rounds, no unresolved delivery-critical defect in any accepted asset, and a successful local revision on each accepted asset. This is an engineering target, not a statistically established industry standard or HiddenDevs qualification. Report initial and final acceptance separately, all failures, assistance, wall time, and API/compute costs.

For a stronger commercial-readiness claim, repeat on another untouched set and compare against a competent human baseline under equivalent briefs. Release only for the categories actually demonstrated. If two consecutive batches show no improvement, stop adding integrations and identify whether evidence, selection, construction, or critique is failing through ablation tests.

The tool must return 'needs review' or 'unsupported' when it cannot establish fidelity, safely edit a region, meet export requirements, or resolve material ambiguity. It must never convert an exhausted attempt budget into acceptance.

## Delivery and commission operations

Before quoting, capture the asset's intended view distance, style, dimensions, triangle and texture budgets, engine, collision/pivot needs, required source files, revision count, and deadline. Confirm whether references are for inspiration or exact reconstruction, and whether the intended AI-assisted workflow is permitted. No price or revenue forecast is defensible from the present evidence.

Keep HIGH_POLY and LOW_POLY in distinct collections where both are required, with unapplied source modifiers. A temporary export copy can be evaluated and triangulated without damaging the editable source. Low-poly is not merely the same mesh labeled differently; its density, silhouette, UVs, and shading must fit the delivery budget.

The package should contain the editable source, requested interchange file, texture maps, a compact specification/usage note, and a validation manifest. Do not package studies, reference downloads without permission, credentials, failed candidates, or private client communications. A clean import into Roblox Studio is required before calling an asset Roblox-ready.

CG Cookie's production guidance emphasizes that low polygon count alone does not make an asset game-ready; usability depends on the intended engine and coherent asset design. This supports testing the full handoff rather than stopping at a render. [17](https://cgcookie.com/posts/creating-great-game-assets-for-fun-and-profit)

Until platform policy and output quality are established, use noncommercial internal briefs. Professional commission work also requires dependable communication and revisions; the tool does not replace responsibility for the delivered asset.

## Tools, spending, and storage decisions

Use the installed Blender, Python, Git, and FFmpeg first. Add ordinary image measurement dependencies only when the first reference experiment requires them. Prefer Workbench previews for geometry and reserve expensive rendering for material/bake validation. No new hardware purchase is justified before measuring the current bottleneck.

Optional tools have explicit adoption tests: fSpy must reduce camera uncertainty; segmentation must reduce annotation work without corrupting component boundaries; a video API must yield a successful reproduced technique; a generator must reduce total modeling-and-cleanup time at equal quality. Commercial licenses, dependency licenses, privacy, and operating cost must be reviewed before client use. A promising demonstration is not sufficient.

Keep code, tests, plans, compact measurements, and validated lessons in Git. Keep client source/delivery assets in a separate project location. Keep renders and comparison images temporary and regenerable; retaining a hash alone does not preserve visual evidence, so final claims must remain reviewable from the saved source, reference provenance, and reproduction settings. Do not create another screenshot archive.

Do not rebuild the erased project's module tree from memory. The first implementation should have only enough architecture to conduct the first complete modeling-and-repair experiment. After that, grow capabilities in response to observed failures.

## Decision and immediate next work

Proceed with a bounded, AI-assisted rigid-prop production tool. Keep the aspiration broad, but make the first release narrow and honest. The strongest leverage is better reference interpretation, editable local construction, reliable visual correction, and destination testing—not an indiscriminate installation of generators or another giant knowledge base.

The next implementation task is a thin Blender executor with inspect, a connected mesh edit, controlled render, save/reload, and rollback. Then run one permitted-reference prop through the complete loop before adding another subsystem. In parallel, obtain a clear answer from HiddenDevs staff on disclosed AI-assisted commissions; application restrictions are already a known constraint.

Current capability remains unproven. The report establishes a plan for demonstrating it, not a conclusion that it already exists.

## Sources

1. HiddenDevs / HiddenBot. [Application Rules](https://www.hiddendevs.com/bulletin?id=2). August 31, 2026. Application eligibility and portfolio requirements; not a verified general commission policy.
2. Roblox Creator Hub. [General specifications](https://create.roblox.com/docs/art/modeling/specifications). Living documentation, checked September 10, 2026.
3. Roblox Creator Hub. [Texture specifications](https://create.roblox.com/docs/art/modeling/texture-specifications). Living documentation; conflicting resolution statements noted.
4. Roblox documentation repository. [Importer](https://github.com/Roblox/creator-docs/blob/main/content/en-us/studio/importer.md). Living primary source.
5. Guangzhao He, Rundong Luo, Wei-Chiu Ma, and Hadar Averbuch-Elor. [Thinking in Blender: Staged Executable Inverse Graphics with Vision-Language Models](https://arxiv.org/html/2606.02580v1). June 1, 2026 preprint; author-reported results, not reproduced here.
6. Yipeng Gao and colleagues. [3DCodeBench: Benchmarking Agentic Procedural 3D Modeling Via Code](https://arxiv.org/html/2606.01057v1). Submitted May 31, 2026; benchmark design and scope.
7. Microsoft. [TRELLIS.2 repository](https://github.com/microsoft/TRELLIS.2). Requirements, representation, license/dependency notices; not installed.
8. Tencent Hunyuan. [Hunyuan3D-2.1 repository](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1). Model and memory requirements; not installed.
9. Blender Authors. [BMesh Module](https://docs.blender.org/api/main/bmesh.html). Development API documentation; installed-version verification still required.
10. ahujasid and contributors. [blender-mcp](https://github.com/ahujasid/blender-mcp/). Public bridge capabilities; not a security audit or endorsement.
11. Patryk Ciechanski and contributors. [blender-ai-mcp](https://github.com/PatrykIti/blender-ai-mcp). Curated-tool candidate; not installed or independently tested.
12. fSpy project. [fSpy](https://fspy.io/). Camera matching and Blender import.
13. Blender Authors. [Edge Data](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/edge_data.html). Indexed manual material; direct page retrieval failed.
14. CG Cookie. [Courses and learning paths](https://www.cgcookie.com/collections). Course descriptions only; paid content not accessed.
15. Bartosz Pampuch. [BEST way to use fSpy: full camera matching workflow](https://www.youtube.com/watch?v=daiMOYR8GS8). July 28, 2022. Public description and chapter list only; video not watched.
16. Google AI for Developers. [Video understanding](https://ai.google.dev/gemini-api/docs/video-understanding). Current API documentation; no API inference performed.
17. CG Cookie. [Creating Great Game Assets for Fun and Profit](https://cgcookie.com/posts/creating-great-game-assets-for-fun-and-profit). January 18, 2018. Enduring production guidance, not current platform specifications.
