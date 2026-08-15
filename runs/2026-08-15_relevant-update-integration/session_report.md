# Relevant-update integration report

## Scope

This branch consolidates the relevant, independently developed work that remained ahead of
`main`, while preserving the repository's current protocol and evidence boundaries.

Integrated dependency stack:

- video-skill transfer and planner use (`483fa60`);
- rejected runtime attempts retained as failures (`5500950`);
- structured reference readiness (`db16161`);
- repository/reference-gate hygiene (`d06cc97`);
- bridge correspondence protocol 0.3 and exact rollback (`54c2264`);
- model-free Bialetti reference gathering (`992f992`);
- add-on resource ownership (`ebd87e2`);
- retrieval abstention (`85b7169`).

Integrated independent experiments:

- Bevel/Subdivision modifier-order reconciliation (`733ca50`);
- scoped Shrinkwrap footprint transfer (`a8e7653`);
- evidence-bound reference interpretation (`9e1aa77`);
- Level-14 synthesis audit (`f452d82`);
- reproducible Gemini video-study pipeline (`7d4ecb9`).

## Selective reconciliation

- The earlier field-report UI was retained and rewritten against current evidence.
- The evidence-retention warning from the post-purge documentation branch was retained without
  restoring its stale broad README rewrite.
- The earlier bridge implementation was intentionally omitted. Its `twist=` API and weaker lab are
  superseded by protocol 0.3's `twist_offset`, correspondence analysis, unequal-density rejection,
  and transaction-owned rollback evidence.
- Historical README paths that no longer exist are now explicitly labeled historical instead of
  being presented as reproducible artifacts.

## Conflict resolution

The reference-analysis merge now applies both gates in order: structured source readiness first,
then evidence-bound decomposition. At primary blockout, technical-health preemption remains first,
followed by decomposition validation. Existing skill-guided ticket behavior and effective briefs
were preserved.

## Validation

- `python -m pytest -q`: **96 passed, 6 subtests passed**.
- `python -m pyflakes addon.py blender_ops knowledge_engine knowledge tools tests`: **pass** after
  removing two unused lab imports.
- `python -m compileall -q ...`: **pass**.
- `python tools/audit_repository.py`: **pass**, 531 tracked files at audit time, no forbidden
  artifacts, unclassified root files, syntax errors, or exact duplicate tracked files.
- all repository JSON files parse successfully.
- field-report link audit: 9 local links, 0 missing.
- conflict-marker and `git diff --check` scans: **pass**.
- Level-14 independent synthesis audit: **pass**, 90 authoritative items and three corrected
  prior count mismatches.
- reference-interpretation independent verifier: **pass**.
- Blender 5.2 fresh-process Bevel/SubD verifier: **pass**.
- Blender 5.2 fresh-process Shrinkwrap verifier: **pass**, including the intentionally retained
  failed unscoped control.

## Readiness boundary

This integration does not authorize Bialetti modeling. Its structured reference evidence passes
machine checks, but `human_review_gate.json` remains pending. The foundation remains `PARTIAL`.
