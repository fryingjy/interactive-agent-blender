# Solidify curved second-shape transfer

## Status

**PASS** for transfer execution and measurement integrity. Two initial hypotheses were disproved and remain recorded as false.

## Environment

- Blender: 5.2.0 LTS
- Build hash: `fbe6228777e7`
- Shape: open elliptical quarter-cylinder panel, 21 vertices / 12 quads
- Requested thickness: `0.2`
- Script: `tools/run_solidify_transfer_lab.py`

## Purpose

Test whether plane-derived Solidify guidance transfers to a curved shell with varying normal directions. Compare Simple, Simple + Even Thickness, and Complex Fixed/Even/Constraints modes, then repeat Simple with unapplied non-uniform scale.

## Measurement correction

The first run failed because it assumed Complex mode leaves one evaluated shell exactly on the source and preserves a simple vertex-half ordering. Both assumptions were false. Complex mode may move both shells and reorder/interleave evaluated vertices.

The corrected metric geometrically pairs the two nearest evaluated shell vertices to each source vertex. Panel spacing intentionally exceeds requested thickness, making the two shell samples locally distinguishable. The initial failed report was overwritten only because it was a measurement implementation error; the disproved artistic hypotheses remain explicit in the final JSON.

## Results

All variants evaluated as closed, all-quad, non-degenerate meshes with consistent normals.

| Mode | Pair-distance range | Max error from 0.2 |
| --- | --- | ---: |
| Simple, scale baked | 0.1999998–0.2000001 | ~`1.9e-7` |
| Simple + Even Thickness | 0.2000–0.2188 | `0.0188` |
| Complex Fixed | 0.1828–0.2000 | `0.0172` |
| Complex Even | 0.2000–0.2188 | `0.0188` |
| Complex Constraints | 0.2000–0.2188 | `0.0188` |
| Simple, scale unapplied `(1.5, 0.75, 1)` | 0.1921–0.3000 | `0.1000` |

The non-uniform-scale warning transferred decisively from the plane to curved geometry.

## Disproved hypotheses

- Enabling Simple Even Thickness did **not** reduce maximum Euclidean source-pair distance error on this faceted elliptical panel.
- Complex Constraints did **not** reduce that same metric relative to Simple.

This does not prove those modes are worse. Euclidean corresponding-vertex distance is not identical to true minimum wall thickness or normal-projected thickness at corners. The result proves that mode names cannot substitute for measurement and that a professional evaluator needs surface-normal/closest-surface metrics before ranking modes.

## Independent verification

`tools/verify_mesh.py --evaluated` passed:

- `Solidify_Curved_Simple`
- `Solidify_Curved_Complex_Constraints`
- `Solidify_Curved_UnappliedScale`

Each had 42 vertices, 80 edges, 40 faces, zero n-gons, zero degenerates, zero non-manifold edges, and outward-consistent signed volume.

## Evidence

- `solidify_transfer_lab.blend`
- `solidify_transfer_report.json`
- `verify_reports/`
- `tools/run_solidify_transfer_lab.py`

## Highest-value next step

Implement closest-surface and normal-projected wall-thickness measurement on an acute bent shell before making quality claims about Even or Complex modes.
