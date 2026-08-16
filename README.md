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
  reversible uncertainty constraints, retrieval provenance, and strict pre-modeling stage gates;
- secondary-view component-strategy evidence that makes front-only ambiguity trigger research and
  uses measured top-view depth to choose continuous versus separate construction across two shapes.
- a validated 30-prop progressive benchmark ladder whose A-G promotion gates preserve human review;
  Swingline 747 remains locked at reference-board review rather than being self-authorized. Its
  review page now emits a reviewer-identified decision bound to the exact audit and construction
  plan, with a fail-closed recorder for approval or correction.
- a typed two-endpoint Connect Vertex Path operation that splits crossed faces/edges continuously,
  rejects invalid paths before acceptance, and preserves transaction rollback and persistent IDs.
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
- `docs/field-report/` — dependency-free interactive status and retained-evidence navigator.

## Local validation

Run the fast regression suite from the repository root:

```powershell
python -m pytest -q
python tools/audit_repository.py
python tools/audit_directive_coverage.py --output runs/2026-08-16_directive-coverage-audit/directive_coverage_audit.json
python tools/verify_reference_board_gate.py runs/2026-08-16_reference-gathering-swingline-747/human_review_gate.json --audit runs/2026-08-16_reference-gathering-swingline-747/audit_report.json --reference-plan runs/2026-08-16_reference-gathering-swingline-747/reference_plan.md
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

## Recent evidence landmarks

The 2026-08-10 through 2026-08-12 paths below are historical citations: their raw folders were
intentionally removed during the 2026-08-14 cleanup after durable lessons were consolidated. They
must not be treated as currently reproducible evidence. See `docs/REPOSITORY_LAYOUT.md` for the
retention boundary and `docs/field-report/index.html` for links to retained, inspectable evidence.

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
- `runs/2026-08-15_video-transfer-uniform-deformation/` — direct transfer of the anvil video's
  uniform-loop deformation lesson to a different 12-sided circular product form: identical
  connected all-quad cages, 82.10% lower profile RMSE, 54.85% better side-quad aspect-ratio p95,
  independent fresh-process verification, and a retrieval-to-planner behavior proof. This is a
  controlled transfer, not held-out professional-asset evidence.
- `runs/2026-08-15_video-study-reference-workflow/` — seven supplied reference-workflow videos
  analyzed through public-video input with timestamped audio/visual episodes, source-fitness limits,
  and seven unpromoted captured principles.
- `runs/2026-08-15_reference-set-gate/` — controls proving that image count, view count, provenance
  count, target identity, and property authority are not interchangeable.

- `runs/2026-08-15_bridge-correspondence-control/` — protocol 0.3 bridge-twist analysis and typed
  control, two-shape crossed-to-clean quad transfer, unequal-density rejection, and exact rollback
  after a post-mutation failure; independently verified without orphan mesh datablocks.
- `runs/2026-08-15_addon-resource-safety/` - Blender 5.2-validated connector cleanup: bounded HTTP
  timeouts, shared streamed downloads, exact temporary-resource ownership, and a measured decision
  not to delete unique retained evidence.
- `runs/2026-08-15_retrieval-abstention/` - frozen positive/paraphrase and unrelated-ticket negative
  controls proving that weak lexical overlap now abstains instead of emitting a planner hint.
- `runs/2026-08-15_bevel-subd-order/` - controlled, rendered modifier-order comparison with an
  independent verification record.
- `runs/2026-08-15_shrinkwrap-footprint-transfer/` - bounded projection transfer with retained
  `.blend`, MatCap render, report, and independent verification.
- `runs/2026-08-15_reference-interpretation-contract/` - evidence-bound silhouette, boundary,
  uncertainty, and target-identity decisions integrated into stage progression.
- `runs/2026-08-15_gemini-pipeline-validation/` - retained failed provenance control: the executable
  Gemini request returned a different source ID and is now explicitly rejected.
- `runs/2026-08-15_video-discovery-queue/` - live metadata-only lesson discovery, known-source and
  held-out contamination filters, strict source binding, one retained cross-video rejection, and
  one independently detected timestamp defect; no video was archived and no lesson was promoted.
- `runs/2026-08-15_nailsea-form-correction/` - correction of the retained rejected candlestick:
  curvature-aware loop redistribution on one connected 12-sided quad shell, 0.955 front IoU,
  published-dimension recovery, and a passing fresh-process Blender verifier. Human form approval
  remains pending and no skill was promoted.
- `runs/2026-08-16_bmesh-editmode-customdata/` — current Blender 5.2 live Edit Mode BMesh evidence:
  destructive all-quad subdivision, valid selection flushing, edge/face/loop custom data, saved
  `.blend`, and a fresh-process verifier.
- `runs/2026-08-16_bevel-normal-policy/` — matched Blender 5.2 solid/evaluated-normal comparison:
  plain smooth Bevel versus Harden Normals versus Bevel Face Strength followed by Weighted Normal,
  with a saved `.blend`, render, numeric report, and fresh verifier.
- `runs/2026-08-16_curved-bevel-normal-policy/` — twelve live radial/taper variants separate
  Bevel-induced normal damage from uneven-cage error; Harden Normals restores the baseline while
  Weighted Normal is explicitly rejected on the uneven curved fixture.
- `runs/2026-08-16_double-curvature-bevel-subd/` — two connected all-quad double-curvature families
  separate declared physical-rim intent from weight assignment; complete controls stay visually
  continuous while eight-edge omissions remain technically clean but visibly pinch and fail the
  exact persistent-ID audit. Live stacks, base-cage wireframe, MatCap comparisons, and 11/11 fresh
  checks are retained.
- `runs/2026-08-16_real-video-reference-setup-review/` — identity-bound whole-video plus native
  range-scoped Gemini analysis, five independently inspected browser frames, sampled visible
  captions, one verified 24–124 s orthographic-correction episode, and explicit rejection of later
  timestamp drift.
- `runs/2026-08-16_reference-image-alignment-transfer/` — typed editable Image Empty creation,
  CUSTOM free-view failure control, 0° FRONT/RIGHT transfer, duplicated-single-source multi-view
  rejection, saved `.blend`, controlled renders, and fresh-process verification.
- `runs/2026-08-15_level14-synthesis-audit/` - independent audit and correction of professional-
  judgment synthesis claims.

Use the foundation report and implementation audit for the complete, bounded interpretation of
these runs.
