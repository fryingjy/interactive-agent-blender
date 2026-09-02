# Interactive Agent Blender

An experimental reference-conditioned Blender modeling system. Its goal is to turn one or more
reference images into an editable, connected, production-oriented Blender asset through a measured
closed loop—not through target-specific scripts or primitive spam.

## Current status

The Blender control plane is mature: typed operations, persistent mesh identity, transaction-owned
rollback, state fingerprints, evaluated-geometry inspection, semantic regions, and Blender-native
diagnostic renders are implemented.

The shape-solving plane has been restarted. The first working vertical slice now:

1. validates an explicit shape-and-camera hypothesis;
2. renders it cheaply on CPU;
3. fits bounded semantic parameters to multiple silhouettes;
4. retains disagreement per view;
5. compiles the result into one connected all-quad cage;
6. leaves surface modifiers live and unapplied for the artist.

That is meaningful infrastructure, not proof that the system can model arbitrary objects. The
current solver supports orthographic section lofts only. Professional generalization remains
unproven.

## Architecture

```text
references -> masks/cameras -> bounded shape hypothesis -> multiview fit
           -> topology compiler -> typed Blender transaction -> inspect/refit/reject
```

See [Architecture](docs/ARCHITECTURE.md) and [Shape solving](docs/SHAPE_SOLVING.md).

## Repository map

- `modeling_core/` — executable shape hypotheses, CPU projection/rasterization, fitting, and cage
  compilation.
- `blender_ops/` — Blender-side typed mutations, transactions, identity, state, topology, shading,
  and rendering.
- `knowledge_engine/` — reusable reference, review, retrieval, video, and workflow policy.
- `knowledge/` — compact source registry, operator cards, and promoted reusable skills.
- `tools/` — maintained CLIs and generic inspection/verification utilities.
- `tests/` — unit/regression tests plus small owned fixtures.
- `reference/` — redistributable project reference inputs only.
- `docs/` — current architecture, workflow, and research contracts.

Historical experiment output and target-specific builders were removed from the active tree. They
remain recoverable from Git history. New generated evidence belongs outside source control unless it
is a small, stable regression fixture.

## Quick validation

```powershell
python -m pytest -q
python tools/audit_repository.py
python tools/audit_source_registry.py
```

Fit and compile a hypothesis:

```powershell
python tools/modeling_pipeline.py validate hypothesis.json
python tools/modeling_pipeline.py fit hypothesis.json `
  --mask front=front-mask.png --mask side=side-mask.png --output fitted.json
python tools/modeling_pipeline.py compile fitted.json --name Blockout --output command.json
```

## Modeling rules

- Gather enough views to constrain silhouette, depth, taper, and assembly relationships.
- Fit major form before adding Blender detail or surface polish.
- Prefer connected edit-mode construction when features are physically continuous; separate objects
  are for real assembly boundaries, not convenience.
- Use 12–16 radial segments for ordinary blockout circles unless evidence demands more.
- Keep high- and low-poly variants in separate collections and do not apply their modifiers.
- Choose SubD creases, support loops, bevel weights, or explicit bevels from the intended surface;
  never smooth every object as a substitute for authored hard edges.
- Evaluate raw cage, evaluated surface, solid diagnostic render, silhouette, and wireframe as
  separate evidence channels.
- Generated 3D/depth/segmentation tools may provide priors; their output is not final topology.

## Blender entry points

- `addon.py` — Blender-side socket add-on.
- `.mcp.json` — local MCP configuration.
- `tools/modeler_mcp_server.py` — typed agent-facing operation surface.
- `blender_ops/modeler_server.py` — Blender-side command implementation.
- `tools/run_modeler_command_sequence.py` — fresh-process execution of typed JSON sequences.

Blender 5.2 LTS is the current tested target. Optional dependencies are split under
`requirements/`; the core fitting path uses NumPy, OpenCV, and SciPy and is designed for the
available Intel integrated GPU/CPU environment.
