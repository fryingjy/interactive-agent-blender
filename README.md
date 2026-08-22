# interactive-agent-blender

An evidence-driven Blender modeling agent that observes live scene state, makes scoped decisions,
edits through a typed runtime, verifies base/evaluated/visual results, recovers from failures, and
retains experimentally tested modeling knowledge.

## Current status

**Foundation status: PARTIAL.** The Blender-control and verification infrastructure is substantial,
but the repository does not claim professional-level generalization. Stronger hard-surface/SubD
judgment, multi-view reference modeling, production preparation, broader held-out assets,
longer-horizon retention, and experienced human review remain open. Advanced sculpting and organic
specialization are deliberately deferred.

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
  adaptive mixed-cause surface diagnosis, and a real Godot tangent-bake import with deliberate
  semantic failure evidence;
- rollback-owned high/low variant packaging with separate collections, independent editable cages,
  and unapplied modifier stacks, including controlled rejection and real Nailsea runtime use;
- question-driven reference research that records exact searches, accepted and rejected candidates,
  reversible uncertainty constraints, retrieval provenance, and strict modeling-stage gates;
- secondary-view component-strategy evidence that makes front-only ambiguity trigger research and
  uses measured top-view depth to choose continuous versus separate construction across two shapes.
- a validated 30-prop progressive benchmark ladder whose A-G promotion gates preserve post-model
  human review. No ladder prop is currently active; deleted candidates are history, not current
  modeling evidence.
- a typed two-endpoint Connect Vertex Path operation that splits crossed faces/edges continuously,
  rejects invalid paths before acceptance, and preserves transaction rollback and persistent IDs;
  controlled nonplanar/SubD transfer now adds an opt-in all-quad preflight that rejects a curved
  diagonal without state drift rather than treating connected topology as automatically SubD-safe.
- a current two-family seam-directed UV production transfer whose connected all-quad high/low
  sources keep live modifiers, outperform matched no-seam controls, bake tangent normals, and
  round-trip as low-only GLBs under an independent Blender verifier.
- explicit semantic bevel-edge declaration separated from weight assignment, with crown/saddle
  double-curvature controls proving that eight omitted sharp-rim segments remain detectable even
  when every evaluated mesh is closed, nondegenerate, and all-quad.

The authoritative readiness decision is in
[`knowledge/foundation/foundation_exit_report.md`](knowledge/foundation/foundation_exit_report.md).

## Start here

| Need | Document or folder |
| --- | --- |
| Operating contract | [`docs/MASTER_DIRECTIVE.md`](docs/MASTER_DIRECTIVE.md) |
| Current requirement audit | [`docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md`](docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md) |
| Executable directive coverage | [`knowledge/foundation/directive_coverage_matrix.json`](knowledge/foundation/directive_coverage_matrix.json) |
| Research/learning roadmap | [`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md) |
| Reference sourcing and analysis | [`docs/REFERENCE_COLLECTION_PROTOCOL.md`](docs/REFERENCE_COLLECTION_PROTOCOL.md) |
| Current development priorities | [`docs/DEVELOPMENT_PRIORITIES.md`](docs/DEVELOPMENT_PRIORITIES.md) |
| Current capability gap matrix | [`docs/CURRENT_STATE_GAP_MATRIX.md`](docs/CURRENT_STATE_GAP_MATRIX.md) |
| Progressive prop benchmark ladder | [`docs/PROGRESSIVE_PROP_BENCHMARK_CURRICULUM.md`](docs/PROGRESSIVE_PROP_BENCHMARK_CURRICULUM.md) |
| Reference-interpretation contract | [`docs/REFERENCE_INTERPRETATION.md`](docs/REFERENCE_INTERPRETATION.md) |
| External visual feedback and repair | [`docs/HUMAN_VISUAL_REVIEW_PROTOCOL.md`](docs/HUMAN_VISUAL_REVIEW_PROTOCOL.md) |
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
- `knowledge_engine/` — retrieval, strategy, structured reference readiness, reasoning, review,
  telemetry, learning, and visual comparison policies that can run outside Blender.
- `knowledge/` — source registry, operator cards, quizzes, promoted skills, and foundation reports.
- `tools/` — MCP entry points, reproducible Blender labs, audits, comparators, and independent
  verifiers.
- `tests/` — fast policy/unit regression tests.
- `requirements/` — optional, capability-scoped Python dependency sets (for example, public-video
  Gemini analysis); these do not download or archive third-party media.
- `runs/` — immutable dated evidence: reports, renders, saved `.blend` files, verification, and
  retained failures.
- `reference/` — project-owned benchmark/reference inputs and notes.
- `docs/` — current contracts, architecture, audits, roadmap, and historical narrative.

## Local validation

Run the fast regression suite from the repository root:

```powershell
python -m pytest -q
python tools/audit_repository.py
python tools/audit_directive_coverage.py --output runs/2026-08-16_directive-coverage-audit/directive_coverage_audit.json
python tools/verify_reference_set_gate.py runs/2026-08-16_reference-gathering-scotch-c38/reference_manifest.json --output runs/2026-08-16_reference-gathering-scotch-c38/audit_report.json
```

The directive audit must pass structurally while still reporting `directive_status: PARTIAL` whenever
any section remains partial, externally review-gated, or deliberately deferred. Its passing result
proves evidence traceability, not professional modeling autonomy.

For a long public YouTube lesson, scope Gemini's actual video/audio inspection to the relevant
source interval instead of reprocessing the whole video:

```powershell
python tools/analyze_video_with_gemini.py "https://www.youtube.com/watch?v=VIDEO_ID" `
  --source-metadata path/to/source_identity.json `
  --start-seconds 24 --end-seconds 124 `
  --output path/to/gemini_range_0024_0124.json
```

Both range arguments are required together. Output episode times remain absolute full-video
timestamps, and model extraction remains unverified until an independent frame/audio/caption review
confirms it. The pipeline does not download or archive the source video.

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

## Current execution landmarks

- `runs/2026-08-21_tutorial-rebuild-donut/` is a tutorial-following training artifact. It does not
  count as unfamiliar-reference capability or a ladder promotion.
- `runs/2026-08-21_reference-aa-battery/` is the current real-reference blockout. Independent
  observations falsify one of two competing representations before a single connected 16-sided
  cage is built through typed Blender decisions. Human visual acceptance remains open.
- `runs/2026-08-21_reference-scotch-c60/` is a rejected non-rotational reconstruction. Its evidence
  correctly disproves disconnected rails, a circular-tube interpretation, and a floating hub, but
  human review found the whole result inaccurate and still too fragmented. Prop work stopped; the
  run remains only as failure evidence.
- `runs/2026-08-21_tutorial-jl-mussi-energy-can/` begins the tutorial-reproduction reset: bounded
  audiovisual study, an actual connected all-quad can reproduction, render-driven correction, and
  a different-geometry SubD-density transfer test. The ordered gate is documented in
  `docs/TUTORIAL_REPRODUCTION_TRACK.md`; held-out props remain paused.
- `runs/2026-08-21_tutorial-blenderbros-hive-controller/` completes Stage 2 with a connected
  annular opening, a rejected overconstrained support/crease branch, and an offset-aperture transfer.
- `runs/2026-08-21_tutorial-blenderbros-beginner-hardsurface/` completes bounded Stage 3 with an
  actual full-video study, a connected mechanical enclosure, visible modifier-order failure and
  correction, and a different-geometry symmetry/Boolean transfer. Its evaluated cut topology is
  explicitly retained as a limitation; Stage 4 advanced SubD/pinch diagnosis is next.
- `runs/2026-08-22_tutorial-blenderbros-subd-topology-sheet/` and
  `runs/2026-08-22_tutorial-blenderbros-tricky-subd-detail/` complete Stage 4 with actual
  audiovisual study, matched SubD failures/corrections, convex loop-termination evidence, a
  connected tapered-shell reproduction, and a different 14-segment diagonal-detail transfer.
  The asset reproduction is explicitly bounded and supplies the prerequisite for Stage 5.
- `runs/2026-08-22_tutorial-cgboost-retopology/` completes bounded Stage 5 with full audiovisual
  study, independent high/low eye-landmark cages in separate collections, a manifold-but-twisted
  topology failure, live Shrinkwrap/SubD deformation tests, and a pointed-mouth transfer. The
  three-view fit passes the tutorial-stage `0.85` gate but remains below the later `0.90` production
  target. Stage 6 UV/material work is next.
- `runs/2026-08-22_tutorial-cgboost-uv-production/` completes bounded Stage 6 with two complete
  audiovisual tutorial studies, a one-object connected compound cage, a visually rejected first
  transfer, a corrected curved-clasp transfer, non-overlap/distortion measurements, UV checker
  materials, and real saved tangent-normal bakes. Stage 7 full production delivery is next.
- `runs/2026-08-22_tutorial-cgthoughts-game-asset/` completes Stage 7 with a simplified medical-case
  high/low asset, live source modifiers, UVs on every low mesh, four PBR channels, GLB delivery, and
  a fresh-process import check. Its `5.5/10` reference-fidelity limitation is explicit. The held-out
  return gate is now ready after consecutive Stage 6 and Stage 7 passes.
- `runs/2026-08-19_observation-to-skill-gap-audit/` records the circular-validation correction that
  demoted unsupported runtime claims.

Historical paths may be named in dated reports even when their raw artifacts were intentionally
removed. `knowledge/foundation/source_retention_ledger.json` is authoritative for that boundary;
current capability claims must point to retained evidence or current code.
