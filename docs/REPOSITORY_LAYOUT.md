# Repository layout and organization rules

## Top-level folders

| Path | Responsibility |
| --- | --- |
| `blender_ops/` | Blender-side typed modeling/runtime implementation |
| `knowledge_engine/` | Planner, retrieval, reasoning, learning, comparison, and review policy |
| `knowledge/` | Durable sources, cards, skills, quizzes, and readiness records |
| `tools/` | Reproducible labs, verifiers, audits, comparators, and MCP entry points |
| `tests/` | Fast unit and policy regression tests |
| `runs/` | Dated empirical evidence and retained failures |
| `reference/` | Project-owned benchmark/reference inputs and notes |
| `docs/` | Current contracts/guides plus clearly labeled history |

## Naming

- Run folders: `runs/YYYY-MM-DD_short-purpose/`.
- Primary run report: a descriptive `*_report.json` plus `session_report.md` for substantive work.
- Independent checks: `*_verify.json` or `verify/`.
- Failed attempts: a clearly named `failed_*` subfolder; never overwrite failure evidence merely to
  produce a pass.
- Reusable Blender scripts: verbs such as `run_`, `verify_`, `render_`, `compare_`, or `analyze_`.
- Knowledge cards: stable topic names, not dates or commit hashes.

## What belongs in Git

Commit code, tests, concise source records, reproducible reports, representative renders, saved
editable `.blend` evidence when reasonably sized, and failures required to interpret a result.

Do not commit:

- Blender autosaves (`*.blend1`);
- large redistributable or third-party source media under `runs/*/media/`;
- caches, temporary files, or duplicate renders not referenced by a report;
- credentials, private data, or unlicensed assets.

## Stability rule

Dated run paths are evidence identifiers and are referenced by reports, cards, and audits. Organize
new work correctly at creation time; do not mass-move historical runs unless every reference and
reproduction command is updated and revalidated. Current documentation may be reorganized more
freely because Git preserves its history.

## Evidence-retention boundary

The user-directed 2026-08-14 cleanup removed most earlier build/render run folders. A citation to
a missing `runs/...` directory is historical prose, not a current reproducible artifact. Keep that
distinction visible in navigation and status documentation: retain lessons and commit history, but
do not label deleted outputs as presently verifiable evidence. `runs/README.md` is the authoritative
record of this boundary.
