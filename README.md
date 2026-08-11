# interactive-agent-blender

An evidence-driven Blender modeling agent that observes live scene state, makes scoped decisions,
edits through a typed runtime, verifies base/evaluated/visual results, recovers from failures, and
retains experimentally tested modeling knowledge.

## Current status

**Foundation status: PARTIAL.** The Blender-control and verification infrastructure is substantial,
but the repository does not claim professional-level generalization. Stronger organic form,
expressive facial work, named external-engine validation, longer-horizon retention, unknown
production-defect diagnosis, broader held-out assets, and experienced human review remain open.

Current evidence includes:

- typed modeling operations, persistent element IDs, semantic regions, state fingerprints, and
  transaction-owned rollback;
- base-cage, modifier-evaluated, technical, silhouette, wireframe, normal, depth, and component
  evidence channels;
- stage gates, reference measurements, localized mismatch tickets, strategy selection, and
  professional-review aggregation;
- legal local video/document ingestion, 11 decoded Blender lessons, controlled reproduction labs,
  structured retrieval, quizzes, telemetry, and self-session replay;
- profile-authored reference models, a connected-quad multi-view barrel, driven corrective transfer,
  and adaptive mixed-cause surface diagnosis with preserved failed attempts.

The authoritative readiness decision is in
[`knowledge/foundation/foundation_exit_report.md`](knowledge/foundation/foundation_exit_report.md).

## Start here

| Need | Document or folder |
| --- | --- |
| Operating contract | [`docs/MASTER_DIRECTIVE.md`](docs/MASTER_DIRECTIVE.md) |
| Current requirement audit | [`docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md`](docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md) |
| Research/learning roadmap | [`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md) |
| Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Knowledge lifecycle | [`docs/KNOWLEDGE_SYSTEM.md`](docs/KNOWLEDGE_SYSTEM.md) |
| Repository layout | [`docs/REPOSITORY_LAYOUT.md`](docs/REPOSITORY_LAYOUT.md) |
| Chronological project history | [`docs/BENCHMARK_HISTORY.md`](docs/BENCHMARK_HISTORY.md) |
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

## Recent evidence landmarks

- `runs/2026-08-11_multiview-barrel/` — connected 5,376-quad barrel shell and multi-view checks.
- `runs/2026-08-11_facial-expression-transfer/` — bounded driven facial-corrective mechanism.
- `runs/2026-08-11_mixed-surface-diagnosis/` — adaptive five-cause diagnosis and exact clean-state
  recovery under fixed-seed Cycles.
- `runs/2026-08-10_online-lessons/` — decoded official lesson evidence and synchronized modalities.
- `runs/2026-08-10_profile-authored-sword/` and `runs/2026-08-10_profile-authored-axe/` — corrective
  profile-authored hard-surface evidence.

Use the foundation report and implementation audit for the complete, bounded interpretation of
these runs.
