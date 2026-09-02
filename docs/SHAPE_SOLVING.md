# Shape solving before Blender

The system no longer asks a language model to invent final vertex coordinates directly from a
reference board. It first creates an executable, bounded shape hypothesis and tests it against
materialized silhouettes outside Blender.

## Intermediate representation

A schema-version 1 hypothesis contains:

- one `section_loft` connected-cage family;
- 8–32 radial segments in multiples of four (12 or 16 is the normal blockout range);
- either a true sharp `box` perimeter or a measured `superellipse` cross-section;
- ordered cross sections with width, depth, height, and superellipse power;
- explicit orthographic camera hypotheses;
- JSON-pointer variables with finite bounds.

The initial family is intentionally narrow. A target that cannot be represented by it must trigger
a new generic family or a documented assembly split—not a target-named Python builder.

## Closed loop

```text
reference images
  -> masks + camera hypotheses
  -> semantic shape hypothesis
  -> CPU multiview fit
  -> per-view residuals and retained parameters
  -> one connected all-quad Blender cage
  -> live, unapplied surface modifiers
  -> Blender-native diagnostic renders
  -> accept, refit, change family, or reject
```

The optimizer may change only declared variables. It cannot invent parts, switch topology, or hide
a failed view inside an aggregate score. Per-view losses remain in the fit record.

## Command line

```powershell
python tools/modeling_pipeline.py validate hypothesis.json
python tools/modeling_pipeline.py fit hypothesis.json `
  --mask front=front-mask.png --mask side=side-mask.png --output fitted.json
python tools/modeling_pipeline.py compile fitted.json --name Blockout --output command.json
```

The compiled command uses `create_authored_quad_mesh`. It emits one connected all-quad side cage,
leaves caps explicit, and applies no modifiers. Blender mutations still run through the existing
decision transaction and independent state inspection.

## Current boundary

This is a real vertical slice, not general reconstruction yet. It supports orthographic section
lofts and has a deterministic two-view recovery test. Perspective calibration, articulated
assemblies, profile-extrusion cages, negative-space constraints, and image-derived initialization
remain future work. Optional image-to-3D systems may provide priors, but their meshes are never
accepted as production topology.
