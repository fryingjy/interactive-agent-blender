# Interactive Agent Blender

An experimental reference-conditioned Blender modeling system. Its goal is to turn one or more
reference images into an editable, connected, production-oriented Blender asset through a measured
closed loop—not through target-specific scripts or primitive spam.

## Current status

The Blender control plane is mature: typed operations, persistent mesh identity, transaction-owned
rollback, state fingerprints, evaluated-geometry inspection, semantic regions, and Blender-native
diagnostic renders are implemented.

The shape-solving plane has been restarted. Its working vertical slice now:

1. extracts hashed masks, normalized crops, outline landmarks, profiles, and enclosed negative spaces
   from alpha or clean-background references, with fail-closed diagnostics and editable-mask replay;
2. binds editable semantic component labels to each source silhouette and measures visible component
   extent and adjacency without claiming hidden structure;
3. assembles only hash-authorized, registration-approved, unique views into a multiview bundle and
   enforces required cross-view component support;
4. proposes generic component representations and competing continuous-cage versus separate-object
   assembly graphs, then refuses to choose topology from projected adjacency alone;
5. resolves assembly edges only from independent multiview seam, continuity, separation, or motion
   evidence while leaving component shape families unresolved;
6. fits each component's competing generic families against its own label masks under fixed shared
   cameras, including bounded object-space placement without letting candidates move the camera;
7. compiles resolved mixed graphs: separate assemblies remain distinct Blender objects, while
   explicitly bound equal-cardinality ports weld or bridge continuous components into one checked
   all-quad cage;
8. converts retained per-component/per-view residuals into scoped refit or representation-change
   tickets using bounded parameter probes that may not hide multiview regression;
9. executes section-loft, outline-extrusion, profile-revolution, curve/profile-sweep, and a closed
   single-through-hole ring extrusion through the same validation, fitting, and Blender compilation
   path; open volume cages receive virtual silhouette caps during fitting without changing topology;
10. supports orthographic/perspective fitting and PnP calibration before compiling editable cages.

That is meaningful infrastructure, not proof that the system can model arbitrary objects. The
current solver does not yet infer landmarks, masks, assemblies, or hidden structure automatically.
Professional generalization remains unproven.

## Architecture

```text
references -> masks/landmarks/cameras -> competing shape hypotheses -> multiview fit
           -> topology compiler -> typed Blender transaction -> inspect/refit/reject
```

See the [living project goal](docs/GOAL.md), [architecture](docs/ARCHITECTURE.md), and
[shape-solving contract](docs/SHAPE_SOLVING.md).

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

`docs/GOAL.md` is the single mutable roadmap. Update its active gate and priorities when new
evidence changes the highest-value work; do not create competing continuation plans.

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
python tools/modeling_pipeline.py extract-reference reference.png --output-dir work/reference
python tools/modeling_pipeline.py annotate-components work/reference/reference_evidence.json `
  component-labels.png --component body=1 --component handle=2 --output components.json
python tools/modeling_pipeline.py bundle-references bundle-manifest.json --output bundle.json
python tools/modeling_pipeline.py propose-assembly bundle.json components.json --output assembly.json
python tools/modeling_pipeline.py resolve-assembly assembly.json observations.json `
  --output resolved-assembly.json
python tools/modeling_pipeline.py fit-components bundle.json assembly.json candidates.json `
  --resolved-assembly resolved-assembly.json --output component-selection.json
python tools/modeling_pipeline.py diagnose-fit fitted.json --component-id body `
  --mask front=front-mask.png --mask side=side-mask.png --output refit-tickets.json
python tools/modeling_pipeline.py compile-assembly component-selection.json `
  --continuity-interfaces continuity-interfaces.json `
  --output compiled-assembly.json --sequence-output sequence.json
python tools/modeling_pipeline.py validate hypothesis.json
python tools/modeling_pipeline.py calibrate-camera correspondences.json --output camera.json
python tools/modeling_pipeline.py select-family loft.json profile.json `
  --mask front=front-mask.png --mask side=side-mask.png --output selected.json
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
