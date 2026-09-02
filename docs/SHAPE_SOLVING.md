# Shape solving before Blender

The system no longer asks a language model to invent final vertex coordinates directly from a
reference board. It first creates an executable, bounded shape hypothesis and tests it against
materialized silhouettes outside Blender.

For isolated objects with alpha or a separable border background, `extract-reference` now produces
a source-hashed evidence record, editable full-resolution mask, normalized crop, outline landmarks,
33-sample width profile, extrema, centroid, and enclosed-negative-space measurements. Ambiguous or
border-leaking extraction fails closed. An edited mask can be replayed with `--mask-override`; both
the original image and override remain hash-bound in the record. This is a deterministic baseline,
not general semantic segmentation.

An editable grayscale label map can assign stable semantic component IDs to the visible silhouette.
`annotate-components` verifies foreground coverage and background leakage, rejects missing or
undeclared labels, and measures each component's visible bounds, landmarks, area, negative spaces,
and adjacency. Label zero is background; labels 1–255 are declared explicitly. These regions are
annotations, not proof of hidden extent, physical continuity, or occlusion order.

`bundle-references` consumes the existing reference-set and registration gate records. It rejects
stale or unauthorized source hashes, duplicate images masquerading as different views,
non-authoritative cameras, component labels bound to another source, and components lacking the
declared number of supporting views. This connects the repository's mature audit layer to the new
pixel evidence without replacing either one.

`propose-assembly` converts bundled visible regions and adjacency into two deliberately bracketing
graph candidates: shared editable cages and separate objects. It also requires at least two generic
shape-family candidates for every component. Projected adjacency cannot select connectivity because
both a molded transition and an attached part can touch in the same silhouette.

`resolve-assembly` accepts independently recorded observations whose artifact SHA-256 is authorized
for the cited registered view. Two registered
views showing a continuous transition can select a shared cage; two views exposing a seam or
separation can select separate objects; verified independent motion is strong separate-assembly
evidence. Conflicts and one-view continuity remain unresolved. Even a resolved assembly graph is
not construction-ready until each component's 3D family is fitted and selected separately.

`fit-components` extracts each semantic region directly from the hash-verified grayscale label
maps and fits at least two declared generic families per component. Every candidate uses the same
registered cameras; camera variables are forbidden during family competition. Bounded
`translate_x/y/z` shape parameters place components in shared world space rather than laundering
placement into per-component camera offsets. A family remains unresolved when compatible candidates
are separated by less than the configured loss margin.

`compile-assembly` emits one typed `create_authored_quad_mesh` command per component only when every
family and assembly edge is resolved. Separate assemblies remain separate editable objects.
Continuous edges deliberately fail: independently fitted meshes are not joined and mislabeled as a
shared cage. A true continuity compiler is required for that case.

## Intermediate representation

A schema-version 1 hypothesis contains:

- a generic `section_loft` or arbitrary measured `profile_extrusion` connected-cage family;
- 8–32 radial segments in multiples of four (12 or 16 is the normal blockout range);
- either a true sharp `box` perimeter or a measured `superellipse` cross-section;
- ordered cross sections with width, depth, height, and superellipse power;
- explicit orthographic camera hypotheses;
- JSON-pointer variables with finite bounds.

The family set is intentionally narrow. `section_loft` covers axial manufactured forms;
`profile_extrusion` covers blades, shields, brackets, plates, and other outline-led forms with
controlled depth stations. A target that cannot be represented must trigger a new generic family or
a documented assembly split—not a target-named Python builder.

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
a failed view inside an aggregate score. Per-view losses, contour error, and enclosed negative-space
counts remain in the fit record. Perspective views carry explicit distance and field of view.

## Command line

```powershell
python tools/modeling_pipeline.py extract-reference reference.png --output-dir work/reference
python tools/modeling_pipeline.py extract-reference reference.png --output-dir work/corrected `
  --mask-override work/reference/reference_mask.png
python tools/modeling_pipeline.py annotate-components work/reference/reference_evidence.json `
  labels.png --component body=1 --component handle=2 --output components.json
python tools/modeling_pipeline.py bundle-references bundle-manifest.json --output bundle.json
python tools/modeling_pipeline.py propose-assembly bundle.json components.json --output assembly.json
python tools/modeling_pipeline.py resolve-assembly assembly.json observations.json `
  --output resolved-assembly.json
python tools/modeling_pipeline.py fit-components bundle.json assembly.json candidates.json `
  --resolved-assembly resolved-assembly.json --output component-selection.json
python tools/modeling_pipeline.py compile-assembly component-selection.json `
  --output compiled-assembly.json --sequence-output sequence.json
python tools/modeling_pipeline.py validate hypothesis.json
python tools/modeling_pipeline.py calibrate-camera correspondences.json --output camera.json
python tools/modeling_pipeline.py select-family loft.json profile.json `
  --mask front=front-mask.png --mask side=side-mask.png --output selected.json
python tools/modeling_pipeline.py fit hypothesis.json `
  --mask front=front-mask.png --mask side=side-mask.png --output fitted.json
python tools/modeling_pipeline.py compile fitted.json --name Blockout --output command.json
```

Family selection fits at least two generic candidates against identical evidence and returns only
the lowest-loss compatible result. Compilation refuses raw or incompatible fits by default.

The compiled command uses `create_authored_quad_mesh`. It emits one connected all-quad side cage,
leaves caps explicit, and applies no modifiers. Blender mutations still run through the existing
decision transaction and independent state inspection.

Perspective calibration expects at least six non-coplanar 3D landmarks paired with measured image
pixels and a stated field of view. It records the world-to-camera matrix and normalized reprojection
error; it does not invent correspondences or pretend an arbitrary product board is a calibrated
multiview capture.

## Current boundary

This is a real vertical slice, not general reconstruction yet. It supports orthographic and
perspective cameras, section lofts, profile extrusions, explicit negative-space diagnostics, and
fail-closed family compatibility. Clean-background silhouette extraction is proven on controlled
fixtures and one real concept image. Editable component labels and audited multiview binding are
implemented, but automatic semantic labeling, complex photographic backgrounds, and independent
visual identity recognition are not. Separate-object family fitting and typed compilation are now
implemented; shared-cage assembly compilation, broader generic families, correspondence discovery,
negative-space-producing topology, and image-derived initialization remain future work.
Optional image-to-3D systems may provide priors, but their meshes are never accepted as production
topology.
