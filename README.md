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
- a mandatory `REFERENCE_ANALYSIS` gate (component-scoped reference evidence, an 11-pass visual
  reconstruction audit, per-component construction justification) that a build cannot skip past
  into modeling, proven on a real fresh prop where a competing body-profile hypothesis was rejected
  by an actual pixel measurement before any geometry existed, not asserted; a root-cause failure
  taxonomy (`docs/FAILURE_TAXONOMY.md`) separating what looks wrong from which reasoning stage
  produced it; and a real material-lit render pass added and debugged live when the existing
  Workbench-only diagnostics proved unable to show whether an assigned material actually looked
  right.
- a bounded CG Cookie sci-fi-crate I0 reproduction that is honestly retained as a 6.8/10 non-pass:
  it adds configurable inset boundaries and typed fitted-face duplication, verifies the saved asset
  in a fresh Blender process, and passes a curved-shell transfer without claiming tutorial fidelity
  or advancing the apprenticeship gate.

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
  a fresh-process import check. Its `5.5/10` reference-fidelity limitation is explicit. Historical
  technical completion does not satisfy the restarted fidelity gate.
- `runs/2026-08-22_tutorial-game-asset-factory-chair/` starts the strict beginner apprenticeship.
  Its public thumbnail is title-card artwork only and a direct browser frame-pull hit YouTube's
  bot-detection captcha, but the run's own prior Gemini analysis already contained real frame-level
  video inspection that had gone uncompared against the build -- doing that comparison found four of
  five real construction decisions matching directly. Scored `7.5/10` on process/topology fidelity, a
  narrower kind of evidence than the pixel-level comparisons other beginner lessons had (no
  finished-result image exists for this tutorial); does not count toward the two-pass gate, which
  B1/B4 already satisfy.
- `runs/2026-08-22_tutorial-polygon-runway-ramen-machine/` has full audiovisual extraction, retained
  typed-modeling corrections, a connected manifold housing, live modifiers, and fresh-process
  verification; original thumbnail comparison was `6.8/10`. A later correction pass built the
  reference's most prominent missing feature -- a warm glowing service window, absent entirely from
  the first pass -- found by direct thumbnail comparison rather than a proportion guess, and fixed
  two real bugs on the way (a parent-transform inverse that erased the housing's world offset, and
  an occlusion problem invisible until an isolated render proved the emissive object itself worked).
  Not re-scored to a specific number, but the single largest named gap is closed.
- `runs/2026-08-22_tutorial-blenderguru-beginner-rebuild-v2/` (the donut/mug scene) was corrected in
  a later v5-v7 pass: direct pixel comparison against the creator's published still found the
  dominant defect was one material bug (the table's base color was effectively pure black with no
  texture, not a vague "needs more atmosphere" gap), and fixing it plus recomputing camera framing
  from the donut's real measured bounds closed enough of the gap to re-score at **8.0/10**, passing
  the gate. See `docs/TUTORIAL_REPRODUCTION_TRACK.md` for why this and the watering can below are
  read as the two required consecutive passes, and why that reading is stated explicitly rather than
  applied silently.
- `runs/2026-08-22_tutorial-blenderguru-lightbulb/` adds a full bulb and multi-bulb scene using
  revolved connected profiles, curve-based wires/filament/thread, linked assemblies, live glass
  subdivision, emission, and Blender 5.2 compositor glare. Fresh technical verification passes,
  but direct creator-result comparison is only `7.2/10`; it remains beginner failure evidence. A
  later v5-v13 correction pass found and fixed four real bugs (alpha-blend glass instead of real
  raytraced transmission, a double-emitting glass shell, bulb spacing narrower than each bulb's own
  measured footprint, and a hidden template mesh rendering as an uncredited stray bulb) but also
  found that chasing the visible "ghosting" led the composition away from the reference's actual
  lying-bulb-cluster arrangement toward a standing row -- v13 is not scored as a fidelity
  improvement and does not pass the gate either. See that run's README for the full chain,
  including the misdiagnosed attempts kept as retained failures.
- `runs/2026-08-22_tutorial-blender-official-watering-can/` is the first strict beginner pass:
  one connected body/handle/spout half-cage, matched eight-vertex bridge loops, transition rings,
  live unapplied Mirror, official-file proportion comparison, and fresh-process verification. Its
  `8.1/10` source score, together with the corrected donut/mug scene's `8.0/10` above, are read as
  the two required consecutive passes -- intermediate (I0) work is now unblocked.
- `runs/2026-08-23_stanley-classic-bottle-reference-pipeline/` exercises the strengthened neutral
  reference pipeline outside the prop ladder. The saved asset is one connected `Vessel` mesh with
  distinct persistent body/base/gasket regions plus a separate removable `CapCup`; render-driven
  edits improved the shoulder and closed the open cap top without substitute primitives. It is at
  `SECONDARY_FORMS`, with no human visual acceptance or ladder-promotion status.
- `runs/2026-08-22_tutorial-grant-abbitt-low-poly-well/` records a researched five-part beginner
  queue. Modeling is deferred until audiovisual access is available rather than inventing steps
  from repeated final thumbnails.
- `runs/2026-08-19_observation-to-skill-gap-audit/` records the circular-validation correction that
  demoted unsupported runtime claims.

Historical paths may be named in dated reports even when their raw artifacts were intentionally
removed. `knowledge/foundation/source_retention_ledger.json` is authoritative for that boundary;
current capability claims must point to retained evidence or current code.
