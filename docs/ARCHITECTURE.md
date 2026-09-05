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
- `component_proposals.py` creates deterministic Lab-color appearance regions inside a verified
  object mask and uses global assignment to propose cross-view matches from color, area, and aspect
  descriptors. It emits editable hash-bound artifacts, confidence, unmatched/ambiguous records,
  and never marks its output as semantic evidence. Its materialization bridge requires an explicit
  complete confirmation decision, revalidates every proposal/source/mask hash, and then produces
  ordinary `REFERENCE_COMPONENT_EVIDENCE` records for the existing bundle contract. External
  segmenter label maps enter through the same proposal type with provider/model/version, per-region
  confidence, source-label hash, full-mask coverage, leakage, and fragmentation checks.
- `reference_bundle.py` joins only reference-audited, registration-approved, hash-current views and
  checks cross-view component support before shape solving.
- `assembly.py` proposes generic per-component representation candidates and bracketing continuous
  versus separate assembly graphs, then resolves graph edges only from independent discriminating
  observations. Assembly resolution never implies that component shape families are resolved.
- `component_fitting.py` extracts each component's hash-bound label masks, fixes shared cameras,
  fits competing executable families with bounded object-space placement, enforces a selection
  margin, groups continuous assembly edges, and preserves resolved separate-object boundaries.
- `continuity.py` compiles explicitly bound, equal-cardinality open ports into one connected quad
  cage by welding coincident loops or bridging measured gaps. It rejects reused ports, excessive
  spans, disconnected output, degeneracy, non-manifold edges, and winding conflicts.
- `refit.py` probes only declared bounded shape parameters around a retained fit and emits localized
  component/view tickets. It suggests a parameter direction only when the view improves without a
  material multiview-mean regression; unrepresented negative spaces escalate to a family or graph
  change.
- `initialization.py` solves an axis-aligned world center and extent box from independent registered
  orthographic silhouettes or calibrated multiview perspective silhouette boxes. Perspective
  initialization triangulates component-center rays, fits projected eight-corner bounds, and
  rejects weak camera geometry or inconsistent observations. Both paths derive executable
  profiles/width stations/one-hole loops and residual- and pixel-uncertainty-bounded variables;
  rank-deficient views remain explicitly underconstrained.
- `camera.py` calibrates perspective views from measured 3D/2D landmark correspondences.
- `mesh.py` generates deterministic loft, extrusion, closed annular extrusion, revolution, and
  transported-frame circular/profile sweep cages from semantic parameters.
- `render.py` provides a cheap CPU silhouette renderer for optimizer inner loops. It detects open
  boundary cycles and fills them only in the rasterized silhouette, so an editable uncapped volume
  does not collapse to an outline when viewed down its open axis.
- `fitting.py` performs bounded multiview fitting and preserves per-view disagreement.
- `construction.py` separates production construction intent from fitted proxies and proposes
  feature edges from persistent-ID probes with explicit preserve/smooth overrides. Plans need
  executed surface evidence; schema validity is not a quality pass. Authored-face CPU comparisons
  use `fill_open_boundaries=False` and must be verified against Blender; virtual caps are not faces.
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

`gemini_component_segmentation.py` requests structured physical-part boxes and polygons from a
configured Gemini image model, maps the documented full-image `[ymin,xmin,ymax,xmax]` box plus
box-local `[x,y]` polygon into source pixels, and audits raw coverage/overlap against the
deterministic object mask. Declared attached assemblies and inserts may visibly occlude a primary
host; only that role relationship is composited, while peer overlap remains an error. When raw
polygons are usable but incomplete, their exclusive interiors become watershed seeds and the
completed partition must have supported internal image edges before entering the external proposal
adapter. Remote labels and confidence remain non-authoritative.

## Interfaces

- The externally maintained `blender-mcp` package supplies the general Blender connection declared
  in `.mcp.json`; no fork of its add-on is vendored here.
- `tools/start_modeler_in_blender.py` starts `blender_ops/modeler_server.py`, and
  `tools/modeler_mcp_server.py` exposes its typed Blender operations.
- `tools/modeling_pipeline.py` validates, fits, and compiles shape hypotheses.
- `.mcp.json` configures the local connections.

Historical experiments and target-specific builders are not part of the runtime architecture. Git
history preserves them without forcing every checkout and audit to carry their artifacts.
