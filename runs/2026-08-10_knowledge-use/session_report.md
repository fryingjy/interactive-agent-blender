# Retrieval, retention, and runtime skill-use report

**Status:** PASS for the controlled benchmark.

## Structured retrieval

Five context-rich cases all returned the expected top skill:

1. Tangent Boolean degenerates → `boolean-groove-cut-topology-cleanup`.
2. Unused material slot → `material-slot-orphan-assignment`.
3. Diffuse color not rendered → `diffuse-color-not-connected-to-bsdf`.
4. SubD boundary mismatch → `subd.boundary_resolution.match_quads_over_triangulate`.
5. Mirror/SubD seam → `modifier.stack_order.subd_safe_mirror_placement`.

The report stores each query context, top three results, total scores, and score breakdowns. Accuracy was 1.0.

## Runtime use

A new cube had two material slots but every face used slot 0. Structured retrieval selected `material-slot-orphan-assignment`. One scoped mutation assigned the intended top-half faces to slot 1:

- scene revision: 0 → 1;
- orphan slots: 1 → 0;
- used material indices: `[0]` → `[0, 1]`;
- telemetry: one use, one success, zero failures.

The final cube independently verified clean. This is controlled runtime use, not a claim that every retrieval result will generalize to production assets.

## Retention quiz

`knowledge/foundation/quizzes/quiz_002.md` contains 15 fresh answers with mechanisms or measured examples. It is a second same-day check, so it improves repeated-retrieval evidence but does not establish multi-day retention.

## Evidence

- `retrieval_benchmark.json`
- `material_skill_use_report.json`
- `skill_usage.jsonl`
- `material_skill_use.blend`
- `verification/MaterialSkillUse_*.json`
