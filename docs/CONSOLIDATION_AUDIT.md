# Repository V2 Consolidation Audit

Date: **2026-09-04**  
Baseline: **`5426ff6`**  
Scope: active source, tests, tools, documentation, knowledge, Blender integration, and reachable Git objects

## Outcome

The repository now has one geometry authority and one Blender mutation authority. The retained
execution path is:

```text
reference
-> evidence
-> components/correspondence
-> cameras
-> competing shape hypotheses
-> fit
-> compile
-> typed Blender
-> inspect
-> diagnose/refit/rebuild
```

`modeling_core` owns executable shape hypotheses, fitting, assembly continuity, and compilation.
`blender_ops` owns typed Blender mutations, transactions, state inspection, and rendering. Research,
learning, review, and retrieval remain in `knowledge_engine`; they may supply evidence and policy but
do not independently choose or generate geometry.

The machine-readable active-tree inventory is
[`architecture_file_classification.json`](architecture_file_classification.json). It parses Python
imports, accounts for Blender's sibling-import bootstrap, records production/test importers, marks
entry points, and traces reachability from the authoritative CLIs and runtime bridges. Its current
classification counts are:

| Classification | Files |
|---|---:|
| `CORE_RUNTIME` | 37 |
| `TEST_SUPPORT` | 59 |
| `TOOL` | 45 |
| `CURRENT_DOC` | 17 |
| `CURRENT_KNOWLEDGE` | 115 |
| `HISTORICAL` | 1 |

No active file is currently classified `DUPLICATED`, `UNREFERENCED`, or `SUPERSEDED`; files proven
to belong to those categories were removed in this consolidation. Static imports cannot prove
runtime use by themselves, so deletion decisions also used CLI registration, configuration,
tests, textual references, and runtime ownership.

## Authority by capability

| Capability | Single authority |
|---|---|
| source provenance and reference readiness | `knowledge_engine.reference_analysis` |
| masks, components, correspondence, cameras, hypotheses, fitting, continuity, compilation, refit tickets | `modeling_core` |
| typed scene mutation, transactions, state fingerprints, Blender-native inspection and rendering | `blender_ops.modeler_server` and typed operation modules |
| local/remote bridge | `tools.modeler_mcp_server` plus the configured external `blender-mcp` transport |
| pipeline CLI | `tools/modeling_pipeline.py` |
| controlled render/reference comparison | `knowledge_engine.reference_overlay`, exposed through `modeling_pipeline compare-reference` |
| runtime skill retrieval | `knowledge_engine.retrieval.StructuredSkillStore`, filtered by validation status |
| research and video ingestion | `knowledge_engine.ingest` and dedicated research/video tools |

The retained `knowledge_engine.parameter_fitting` is used by `modeling_core` and is shared numeric
infrastructure, not a second geometry system. `reference_overlay` and `visual_compare` are retained
verification math. `reference_registration` supplies evidence policy. `scene_decomposition` retains
component vocabulary and live scene-coverage checks only; its former strategy-selection role was
removed.

## Removal proof

Every deletion below meets at least one required proof category.

### Fully superseded

- `addon.py` and `tests/test_addon_resource_safety.py`: the repository copy was not imported or
  referenced by `.mcp.json`. The configured transport invokes external `uvx blender-mcp`, while
  typed modeler operations use `tools/modeler_mcp_server.py` and `blender_ops/modeler_server.py`.
  The repository file SHA-256 was
  `8DD32B48D4AA76557500607AFB2CAE9D849099ED8411A61733C542A4B84F67FB`; the installed Blender 5.2
  addon copies had SHA-256
  `60E7C1C086EBC0C3DFCD8318434C72CFB98E93ABFCBD9B8A42427538E3A11046`, proving the repository
  copy was also stale.
- `knowledge_engine/component_strategy.py`, `profile_sampling.py`,
  `representation_hypothesis.py`, `reference_constraints.py`, and `visual_reconstruction.py`, with
  their dedicated tests: these implemented parallel prose/heuristic geometry selection,
  reconstruction gates, or local constraint scoring. Executable competing hypotheses, fitting,
  selection, compilation, and residual diagnosis in `modeling_core` now provide the actual evidence.
- `knowledge_engine/strategy.py`: removed from the planner; geometry strategy now comes only from
  fitted executable hypotheses.
- `blender_ops/repair.py` and `tests/test_repair.py`: an unbounded destructive repair path superseded
  by typed operations, transaction-owned rollback, diagnosis, and scoped refit/rebuild.

### Unreferenced or test-only duplicate

- `blender_ops/coordinate_frames.py`: no production or test importer; runtime coordinate safety is
  implemented by the retained `coordinate_safety.py` path.
- `knowledge_engine/component_layout.py`: only its own test imported it; retained
  `scene_decomposition` and fitted component diagnostics cover active scene/component checks.
- `knowledge_engine/ingest/web_ingest.py`: no production, test, CLI, or documentation reference.
- Tests dedicated only to removed authorities were deleted with those authorities:
  `test_component_layout.py`, `test_component_strategy.py`,
  `test_competing_representation_hypotheses.py`, `test_profile_sampling.py`,
  `test_reference_constraints.py`, `test_representation_hypothesis.py`, and
  `test_visual_reconstruction.py`.

### Duplicated CLI surface

The following one-purpose wrappers duplicated library calls or pipeline stages and were removed:

- `align_silhouette_to_reference.py`
- `audit_visual_reconstruction.py`
- `build_reference_to_blockout_contract.py`
- `compare_reference_silhouettes.py`
- `compare_silhouettes.py`
- `evaluate_reference_constraints.py`
- `measure_reference.py`
- `test_representation_hypotheses.py`

`compare_reference_render.py` migrated to `modeling_pipeline compare-reference` and
`extract_component_mask_observations.py` migrated to
`modeling_pipeline inspect-component-mask`. Reference measurement is already part of
`modeling_pipeline extract-reference`.

### Documentation duplication

- Reference collection and interpretation are consolidated in `REFERENCE_PROTOCOL.md`.
- Human review, failure taxonomy, diagnosis, and repair policy are consolidated in
  `REVIEW_AND_REPAIR.md`.
- Video extraction and learning are consolidated in `VIDEO_PROTOCOL.md`.
- `DEVELOPMENT_PRIORITIES.md` was removed because `GOAL.md` is the sole mutable roadmap.

### Historical knowledge outside runtime retrieval

Operator cards remain reference material and are explicitly classified in
`knowledge/foundation/operator_card_classification.json`; they are not a second runtime skill
store. Runtime retrieval now accepts only `EXPERIMENTALLY_TESTED`, `REPRODUCTION_VALIDATED`,
`TRANSFER_VALIDATED`, `RUNTIME_VALIDATED`, or `PROMOTED` records. Candidate material is excluded.
The destructive `boolean-groove-cut-topology-cleanup` record is retained as `HISTORICAL` negative
evidence and cannot enter runtime retrieval.

## Git object-size audit

[`git_object_size_audit.json`](git_object_size_audit.json), captured against consolidated snapshot
`83aefd3a75ef6f891df8c69efaba53642d1fa14e`, reports 6,123 reachable blobs totaling
638,024,101 bytes. The consolidated current tree accounts for only 2,288,261 bytes. Deleted-only
objects account for 635,735,840 bytes (99.64%), and deleted historical media accounts for
606,027,315 bytes (94.99%). Historical `runs/**` paths alone account for 605,355,272 bytes. PNG and Blend blobs are
the dominant formats.

No history rewrite was performed.

### Separate history-rewrite plan

The exact proposed removal set is **all historical paths under `runs/**` in every rewritten ref**.
No current source, knowledge, docs, tests, or neutral fixtures are included. Execute only as a
separate coordinated maintenance operation:

1. Record all local/remote branches and tags; require a clean worktree.
2. Create both a bare mirror clone and a Git bundle containing all refs; verify each backup in a
   separate location.
3. Run a disposable-clone dry run with:
   `git filter-repo --path runs/ --invert-paths --force`.
4. Re-run repository, source-registry, architecture, object-size, full test, fresh Blender, and
   neutral regression checks in the rewritten clone.
5. Compare retained refs and current-tree hashes with the pre-rewrite record; confirm recovery by
   cloning from the mirror and by unbundling the bundle.
6. Announce rewritten commit identities and the required collaborator re-clone/rebase procedure.
7. Only then force-push the explicitly reviewed branches and tags. Keep the mirror and bundle until
   every collaborator confirms recovery.

This plan is intentionally not part of ordinary cleanup because rewriting shared object identity is
destructive and operationally distinct from deleting files in the current tree.

## September 5 consolidation refresh

Audit baseline: `4579480` (recover removed text with `git show 4579480:docs/GOAL.md`,
or the corresponding document path). This is a maintenance pass, not capability expansion.
The refreshed active-tree inventory covers 290 files and 169 Python files; no exact duplicate
non-empty files or Python parse failures were found. Static imports/classification are evidence,
not proof that every zero-import module is dead. No source module, user asset, media file or
shared Git history was deleted in this pass.

| Removed or corrected material | Evidence / deletion classification | Retained authority |
| --- | --- | --- |
| Chronological implementation queues in `GOAL.md` | **SUPERSEDED**: completed features exist in the retained solver/runtime, while the frozen B0 and curriculum now define the current phase. Several old paragraphs prescribe already completed work. | Single current queue, unchanged completion criteria, linked negative evidence; full prior diary in Git |
| `MASTER_DIRECTIVE.md` sections 18 and 19a's dated connector availability and August priority reconciliation | **HISTORICAL-only / SUPERSEDED**: session tool discovery does not expose those connector names; the September bootstrap supersedes the crate/katana-era queue. | Durable discovery, bypass disclosure, typed authority and benchmark discipline |
| Deleted foundation gate, telephone example and implementation-audit references | **SUPERSEDED**: targets absent from active tree. | Current curriculum, shape protocol and baseline counterexamples |
| Claim that image-derived initialization is future work | **SUPERSEDED** by `modeling_core/initialization.py` and its tests. | Explicit orthographic/calibrated-perspective support and ordinary-photo limitations |
| Root-level video dependency install command | **SUPERSEDED** by `requirements/video-learning.txt`. | Correct command plus checked local Markdown link |
| File-study claims that no Blend sources/video pipeline exist, shorthand lifecycle labels and conflicting promotion order | **SUPERSEDED** by current file-study evidence, video implementation and knowledge lifecycle. | Observation/inference separation, transfer before runtime promotion, paired-study evidence requirements |

The same audit tool now checks local file destinations in current documentation Markdown links and
reference definitions. It excludes code examples and remote links; it does not validate prose paths,
remote availability, fragment anchors or all CommonMark syntax. Four regression tests cover missing
targets, encoded/spaced paths, reference definitions, code examples and repository escape.

Self-diagnosis: the last two reference cycles improved evidence diagnostics without producing a
reference-task Blender artifact. This pass removes contradictory context and stale instructions;
it does not fix semantic perception, camera reasoning or construction skill by itself. The goal
now explicitly requires a bounded reference-to-construction exercise and prohibits treating another
metadata-only cycle as modeling progress. No bootstrap gate, family-selection margin, benchmark
result or runtime authorization was weakened.

Verification: **420 tests and 30 subtests passed**, with `BLENDER_TEST_EXECUTABLE` set to Blender
5.2.1, including fresh-process evaluated-shoulder failure/repair execution. Repository hygiene,
current document file links, curriculum and source-registry checks pass. Research refresh is in
[External architecture research](EXTERNAL_ARCHITECTURE_RESEARCH.md); no additional package was
needed for this maintenance pass. Git object inspection was read-only; the separate recovery and
history-rewrite plan above remains unexecuted. At baseline `4579480`, 6,168 reachable blobs total
639,162,943 bytes; current-HEAD blobs occupy 2,410,679 bytes. Deleted historical media represents
94.82% of reachable blob bytes. These are uncompressed object sizes, not checkout or pack-file sizes.

## Original consolidation verification (historical snapshot)

- Full Python suite: **400 passed, 30 subtests passed**.
- Repository audit: **PASS**, 274 active files, zero forbidden
  paths, root drift, syntax failures, or duplicate active files.
- Source registry: **PASS**, 14 records, zero missing artifacts, four intentional non-path refs.
- Architecture audit: no Python parse errors.
- Git object-size audit: completed read-only; history rewrite explicitly false.
- Fresh Blender execution: **PASS** in Blender **5.2.1 LTS** after removing an eager optional-OpenCV
  package import from Blender's lightweight runtime path.
- Neutral reference-to-blockout regression: **PASS**. Two generated orthographic masks were fitted
  against competing `section_loft` and `profile_extrusion` hypotheses. `section_loft` was selected;
  both fitted view losses were 0.0. The selected result compiled and executed as one connected,
  unapplied-modifier, 36-vertex/24-quad cage.
- Independent saved-Blend verification: **PASS** for the intentional open-surface contract, with
  zero n-gons, loose vertices/edges, degenerate faces, invalid non-manifold edges, or face-winding
  conflicts.
