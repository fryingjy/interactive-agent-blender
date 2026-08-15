# interactive-agent-blender

An evidence-driven Blender modeling agent that observes live scene state, makes scoped decisions,
edits through a typed runtime, verifies base/evaluated/visual results, recovers from failures, and
retains experimentally tested modeling knowledge.

## Current status

**Current post-purge status: PARTIAL.** The typed Blender runtime remains available, but the
repository does not claim professional-level generalization. On 2026-08-14 the user directed the
removal of accumulated historical build/render evidence; current work therefore starts from the
retained blend-file study, simple connected-form exercises, problem-driven documentation/video
study, and explicitly bounded transfer tests. Do not use prose that cites a missing `runs/...` path
as if its artifact still existed.

Current retained work includes:

- typed modeling operations, persistent IDs, semantic regions, state fingerprints, transaction
  rollback, and the expanded hard-surface intent/shading surface;
- the professional `.blend` file study, including the evidence-backed distinction among semantic
  weighted Bevel, ANGLE/VGROUP scope, edge crease, and intentional absence of hard edges;
- the current curriculum and source-to-knowledge records, whose claims remain `CAPTURED` or
  `CANDIDATE` until a different-shape transfer test validates them;
- post-purge simple-form work: a screw/revolve transfer, a grown connected door-handle lever, and
  a teapot body/spout/handle investigation with retained transaction and bridge-twist failures;
- Level-14 professional-judgment synthesis, which rates the current knowledge as strong,
  moderate, or thin rather than treating coverage counts as skill.

The current authority order is the live code, retained runs, and
[`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md). See
[`runs/README.md`](runs/README.md) for the evidence-retention boundary; the older foundation audit
is historical context, not a live-evidence index.

## Start here

| Need | Document or folder |
| --- | --- |
| Operating contract | [`docs/MASTER_DIRECTIVE.md`](docs/MASTER_DIRECTIVE.md) |
| Historical requirement audit | [`docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md`](docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md) — pre-purge citations may be unavailable locally |
| Research/learning roadmap | [`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md) |
| Current development priorities | [`docs/DEVELOPMENT_PRIORITIES.md`](docs/DEVELOPMENT_PRIORITIES.md) |
| Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Knowledge lifecycle | [`docs/KNOWLEDGE_SYSTEM.md`](docs/KNOWLEDGE_SYSTEM.md) |
| Repository layout | [`docs/REPOSITORY_LAYOUT.md`](docs/REPOSITORY_LAYOUT.md) |
| Chronological project history | [`docs/BENCHMARK_HISTORY.md`](docs/BENCHMARK_HISTORY.md) — historical, not a live-evidence index |
| Evidence conventions | [`runs/README.md`](runs/README.md) |

## Runtime loop

```text
brief/reference
-> inspect and measure
-> choose strategy
-> observe live Blender state
-> begin one scoped decision transaction
-> mutate through the typed operation surface
-> inspect base cage, evaluated surface, visuals, and technical state
-> accept, repair, rollback, or rebuild
-> independently verify and save
```

Research returns to the same loop:

```text
problem -> retrieve -> research -> hypothesize -> reproduce -> measure
        -> retain/reject -> apply to the original task -> verify
```

## Repository map

- `blender_ops/` — Blender-side typed operations, state authority, transactions, identity,
  semantic regions, render passes, stage gates, and evaluated probes.
- `knowledge_engine/` — retrieval, strategy, reasoning, review, telemetry, learning, and visual
  comparison policies that can run outside Blender.
- `knowledge/` — source registry, operator cards, quizzes, promoted skills, and foundation reports.
- `tools/` — MCP entry points, reproducible Blender labs, audits, comparators, and independent
  verifiers.
- `tests/` — fast policy/unit regression tests.
- `runs/` — immutable dated evidence: reports, renders, saved `.blend` files, verification, and
  retained failures.
- `reference/` — project-owned benchmark/reference inputs and notes.
- `docs/` — current contracts, architecture, audits, roadmap, and historical narrative.

## Local validation

Run the fast regression suite from the repository root:

```powershell
python -m pytest -q
```

Blender evidence scripts target Blender 5.2 LTS and are normally run in factory-startup background
mode. Each run's report or session note records its exact command and evidence boundary. Independent
verifiers deliberately avoid importing the modeling code they are checking.

The local Blender/MCP entry points are:

- `addon.py` — Blender-side socket add-on;
- `.mcp.json` — MCP host configuration;
- `tools/modeler_mcp_server.py` — typed modeler MCP surface;
- `blender_ops/modeler_server.py` — Blender-side command implementation.

## Evidence and claim rules

- Current code and reproducible evidence override stale prose.
- A clean/manifold mesh is not automatically good topology or good modeling.
- Metrics support visual judgment; they do not replace it.
- Development fixtures and source-tuned assets do not count as held-out generalization.
- Failed attempts remain visible and are never rewritten to manufacture a pass.
- Third-party media belongs under ignored `runs/*/media/` paths unless redistribution is explicitly
  permitted and documented.
- Do not use real-world weapon-construction or engineering material as training data. Fictional
  prop art may use general modeling principles.

## Historical and retained evidence landmarks

> **Retention boundary:** the historical entries below may cite run folders removed in the
> 2026-08-14 cleanup. They are not current reproducible evidence. Use the retained current-work
> links first: [`runs/2026-08-13_blend-file-study/`](runs/2026-08-13_blend-file-study/),
> [`runs/2026-08-14_video-curriculum/`](runs/2026-08-14_video-curriculum/),
> [`runs/2026-08-14_teapot-body-revolve/`](runs/2026-08-14_teapot-body-revolve/), and
> [`runs/2026-08-15_synthesis-level14-professional-judgment/`](runs/2026-08-15_synthesis-level14-professional-judgment/).

- `runs/2026-08-11_connected-camera-corrective/` — post-review one-object camera rebuild: one
  connected 256-quad control cage, 16-vertex radial loops, welded inset/extrusion details, 0.828
  mean three-view IoU, weighted lens bevels, 19/19 fresh-process checks, and one-mesh GLB round trip. This is corrective,
  not new held-out evidence; exact detail and expert acceptance remain open.
- `runs/2026-08-11_heldout-camera-subd/` — second online CC0 held-out family whose 19-object
  candidate passed automated gates but was explicitly overturned by experienced review for an
  over-broad separate-assembly strategy. The rejection is retained as evidence, not hidden.

- Boombox benchmark: removed 2026-08-12. It passed every automated gate but was rejected on direct
  human visual review for not resembling its reference at all; see
  `docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md` for the retained lesson.
- `runs/2026-08-11_multiview-barrel/` — connected 5,376-quad barrel shell and multi-view checks.
- `runs/2026-08-11_facial-expression-transfer/` — bounded driven facial-corrective mechanism.
- `runs/2026-08-11_mixed-surface-diagnosis/` — adaptive five-cause diagnosis and exact clean-state
  recovery under fixed-seed Cycles.
- `runs/2026-08-10_online-lessons/` — decoded official lesson evidence and synchronized modalities.
- `runs/2026-08-10_profile-authored-sword/` and `runs/2026-08-10_profile-authored-axe/` — corrective
  profile-authored hard-surface evidence.
- `runs/2026-08-11_expressive-facial-articulation/` — independently verified regional smile
  coupling with five preserved rejected iterations; organic follow-on is deferred.

Use the foundation report and implementation audit for the complete, bounded interpretation of
these runs.
