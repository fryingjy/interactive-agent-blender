# Repository layout

The repository contains maintained runtime code, current contracts, and small deterministic test
fixtures. It does not store a chronological laboratory notebook.

| Path | Purpose |
| --- | --- |
| `modeling_core/` | Reference-conditioned proxy solving and topology compilation |
| `blender_ops/` | Blender-owned mutation, state, topology, modifiers, and rendering |
| `knowledge_engine/` | Reusable analysis, learning, and workflow policy |
| `knowledge/` | Curated sources, operator cards, and promoted skills |
| `tools/` | Maintained CLIs and generic verifiers |
| `tests/` | Automated tests and project-owned fixtures |
| `reference/` | Redistributable benchmark/reference inputs |
| `docs/` | Current architecture and operating guidance |
| `requirements/` | Capability-scoped optional dependencies |

Generated renders, `.blend` checkpoints, downloaded media, temporary masks, and fitting records are
local work products. Keep them outside Git or in an ignored workspace. Promote only the smallest
artifact needed for a deterministic regression test, under `tests/fixtures/`, with clear ownership.

Target-specific Python builders are prohibited. A new target must use an existing generic shape
family or justify a reusable family added to `modeling_core/` with synthetic recovery tests.
