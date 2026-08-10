# Fixed-frame multi-view visual comparison

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS (`fbe6228777e7`)  
**Status:** PASS (controlled synthetic experiment only)

## Question

Can the system compare reference and candidate silhouettes in consistent front, side, and top
framing, identify a proportion mismatch, and measure whether a correction improves every view?

## Method

`tools/run_multiview_visual_lab.py` created one reference shape and two candidate variants.
`blender_ops.render_passes.render_silhouette` framed all candidates from the reference bounds, so
automatic per-object reframing could not hide size errors. `knowledge_engine.visual_compare`
measured foreground IoU, normalized centroid and bounding-box error, and symmetric contour
distance. The experiment used Workbench renders at 256 px.

The reference was a 4 x 2 x 2 rounded box with a 0.25 bevel. The intentionally poor candidate
was 4.6 x 1.6 x 2.3 with a 0.12 bevel. The corrected candidate was 4.05 x 1.98 x 2.02 with a
0.24 bevel.

## Results

| Metric | Initial | Corrected |
| --- | ---: | ---: |
| Mean silhouette IoU | 0.739440 | 0.979045 |
| Worst-view IoU | 0.735035 | 0.967056 |
| Mean normalized contour error | 0.021805 | 0.002058 |

All three view IoUs improved. All four experiment assertions passed. The saved corrected object's
evaluated mesh independently verified clean: 96 vertices, 192 edges, 98 faces, zero n-gons,
zero non-manifold edges, zero loose geometry, zero degenerate faces, and positive signed volume.

## Visual inspection

The PNGs contain a centered dark silhouette on a transparent background. Direct inspection agrees
with the measurements: the initial front view is too wide and tall, its side view too narrow and
tall, and its top view too wide and narrow. The corrected silhouettes nearly overlap the reference
in every orthographic view, with the largest residual at the front-view rounded corners.

## Limits

This is not held-out reference modeling. The generator contains both the reference and correction
parameters, the reference is synthetic, centroid alignment is intentionally trivial, and the
metric does not assess highlight flow, material response, perspective, landmarks, negative space,
or semantic decomposition. It proves fixed-frame multi-view regression measurement, not
professional visual judgment.

## Artifacts

- `multiview_visual_lab.blend`
- `reference_*.png`, `initial_*.png`, `corrected_*.png`
- `comparison_initial.json`, `comparison_corrected.json`
- `visual_comparison_report.json`, `render_report.json`
- `verify_reports/Visual_Corrected_20260810T161916Z.json`
