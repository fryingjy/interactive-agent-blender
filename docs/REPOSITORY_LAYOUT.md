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

Review screenshots and diagnostic renders are disposable by default. Inspect them, retain the
observed lesson and measured limitations, then delete them when the review is complete. Preserve
final editable models, concise decision/measurement records and replay instructions. Keep source
references and hash-bound masks only while needed by an active fitting/replay contract; those are
inputs, not redundant review pictures. Do not claim deleted media remain available for independent
review. Superseded generated checkpoints may be removed after the final model and replay are verified.

Target-specific Python builders are prohibited. A new target must use an existing generic shape
family or justify a reusable family added to `modeling_core/` with synthetic recovery tests.

For a raw-cage/curvature review deadlock, `tools/run_modeler_command_sequence.py` supports
`--surface-diagnostic-only`: an existing saved cage, normal reference authorization, a narrow
live-modifier/query allowlist, and a new `.diagnostic.blend` output. It cannot overwrite a file,
apply modifiers, construct geometry, export or advance a stage. The report explicitly marks the
trial unaccepted; ordinary surface acceptance still requires the existing review gate.
