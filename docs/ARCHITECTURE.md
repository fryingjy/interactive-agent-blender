# Architecture

The project has two authorities: a reference-conditioned solver decides what geometry should exist;
Blender owns scene mutation and evaluated truth.

```text
materialized references
        |
        v
mask / landmark / camera evidence
        |
        v
bounded shape hypothesis (modeling_core)
        |
        v
CPU multiview fit + per-view residuals
        |
        v
topology compiler -> typed Blender command
        |
        v
transaction -> connected cage -> live modifiers
        |
        v
base cage + evaluated surface + diagnostic renders
        |
        +---- refit / change family / accept / reject
```

## `modeling_core/`

- `hypothesis.py` validates the executable shape/camera intermediate representation.
- `reference_evidence.py` binds image provenance and extracts fail-closed masks, normalized crops,
  outline landmarks, profiles, and enclosed negative-space observations for separable backgrounds.
- `component_evidence.py` binds editable grayscale semantic labels to source silhouettes and
  measures per-view visible regions and adjacency.
- `reference_bundle.py` joins only reference-audited, registration-approved, hash-current views and
  checks cross-view component support before shape solving.
- `assembly.py` proposes generic per-component representation candidates and bracketing continuous
  versus separate assembly graphs, then resolves graph edges only from independent discriminating
  observations. Assembly resolution never implies that component shape families are resolved.
- `component_fitting.py` extracts each component's hash-bound label masks, fixes shared cameras,
  fits competing executable families with bounded object-space placement, enforces a selection
  margin, and compiles only supported separate-object assemblies. Shared-cage edges fail closed.
- `camera.py` calibrates perspective views from measured 3D/2D landmark correspondences.
- `mesh.py` generates deterministic connected cages from semantic parameters.
- `render.py` provides a cheap CPU silhouette renderer for optimizer inner loops.
- `fitting.py` performs bounded multiview fitting and preserves per-view disagreement.
- `compiler.py` emits the existing typed `create_authored_quad_mesh` command without applying
  modifiers.
- `selection.py` competes generic shape families and refuses to select an incompatible candidate.

This layer exists because correctness cannot be recovered by adding more Blender operations to a
bad shape plan. Coordinates must be measured or fitted before they become scene mutations.

## `blender_ops/`

Blender remains authoritative for scene state. Persistent IDs, state fingerprints, transaction-owned
rollback, typed operations, evaluated geometry probes, semantic regions, and native diagnostic
renders remain in this layer. A command return is not proof of success; the resulting cage,
modifier surface, render, and technical state must be inspected.

## `knowledge_engine/`

This package contains reusable reference, review, retrieval, and stage policy. It may rank evidence
or propose a bounded hypothesis, but it cannot bypass fitting or Blender transactions.

## Interfaces

- `addon.py` starts the Blender-side endpoint.
- `tools/modeler_mcp_server.py` exposes typed Blender operations.
- `tools/modeling_pipeline.py` validates, fits, and compiles shape hypotheses.
- `.mcp.json` configures the local connections.

Historical experiments and target-specific builders are not part of the runtime architecture. Git
history preserves them without forcing every checkout and audit to carry their artifacts.
