# External Architecture Research

Reviewed: **2026-09-04**

This note records ideas worth testing after repository consolidation. These projects are evidence
and comparison points, not dependencies and not sources to copy wholesale. Claims below are limited
to their papers, project pages, and repositories as reviewed on the date above.

## Relevant systems

| System | Useful architectural evidence | Decision for this repository |
|---|---|---|
| [LL3M](https://threedle.github.io/ll3m/) ([paper](https://arxiv.org/abs/2508.08228)) | Specialized agents share interpretable Blender code, retrieve Blender/API knowledge, debug execution, and visually self-critique. | Retain editable representations and retrieval-backed operations. Do not replace typed commands with unrestricted generated Python. |
| [Planner–Actor–Critic for agent-augmented 3D modeling](https://arxiv.org/abs/2601.05016) | Separates planning, execution, and critique and reports improvement over single-prompt Blender MCP execution with human supervision. | The current plan/execute/inspect/refit separation is directionally aligned. Test whether explicit critic state improves results rather than adding agents by assumption. |
| [ViSculpt](https://arxiv.org/abs/2608.24169) | Uses viewport observation and localized Blender GUI edits to preserve untouched regions of an existing mesh. | Treat direct visual-local editing as a complementary future repair path, not a replacement for deterministic typed construction. Require region masks and before/after state evidence before adoption. |
| [Vibe3DScene](https://github.com/3DSceneAgent/Vibe3DScene) | Separates routing/runtime, MCP tools, Blender execution, and optional external services; supports persisted sessions and headless/local clients. | The repository already has the important runtime/tool boundary. Avoid importing its broader scene-generation/service stack into this focused modeler. |
| [mcp-3d-modeling-agent](https://github.com/SekaiNoOwari77/mcp-3d-modeling-agent/blob/main/README.en.md) | Documents a plan→execute→observe→review→replan graph, schema-gated tool selection, minimal per-role context, prompt versioning, and benchmark logging. | Highest-value future comparison: criteria-coverage enforcement and per-stage minimal context. Validate against this repository's held-out reference benchmark before adopting orchestration complexity. |
| [BlenderGym](https://github.com/richard-guyunqi/BlenderGym-Open) ([paper](https://arxiv.org/abs/2504.01786)) | Finds that current VLM systems struggle on graphics tasks easy for human Blender users and that inference effort must be allocated strategically between generation and verification. | Spend more reasoning and visual checks at high-salience form decisions, not uniformly on every command. Use its task/evaluation separation as a benchmark reference, not its data as a substitute for this project's reference-modeling goals. |
| [3DCodeBench](https://arxiv.org/abs/2606.01057) | Reports API failures plus visually successful outputs with disconnected/floating geometry, uses pairwise human preferences, and finds multi-turn refinement useful. | Typed operations already address API reliability; add stronger assembly/editability hard failures and blinded pairwise review to measure visible progress. |

## Consolidation conclusions

The comparison does not justify replacing the retained architecture. It reinforces five principles
already present here:

1. keep plans, execution, observation, and critique distinct;
2. expose narrow schema-validated operations instead of relying on unrestricted scripts;
3. inspect actual Blender state and rendered evidence after execution;
4. preserve editable geometry and bounded repair scope; and
5. measure improvement on held-out tasks rather than inferring capability from tool count.

The most credible immediate gaps are apprenticeship, evaluation, and control-flow gaps, not another
geometry module:

- criteria-coverage enforcement so no requested visual/technical criterion silently skips review;
- compact per-stage context so the planner, executor, and critic each receive only authoritative
  state relevant to their decision;
- a benchmark comparison of single-loop versus explicit critic/replan state;
- optional localized viewport editing for existing-mesh repair, gated by region-preservation checks;
- broader held-out reference benchmarks that score visible correspondence, editability, repair
  quality, and regression, not merely command success.

Criteria-coverage enforcement and a measured apprenticeship bootstrap were added after consolidation.
The remaining items still require a separate hypothesis, acceptance metric, and regression experiment
before they can enter the authoritative path.
