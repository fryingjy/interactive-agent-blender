# Facial expression corrective-transfer report

**Status:** PASS for the bounded rig/driver/topology mechanism; PARTIAL for facial-expression quality.

## Task and source boundary

The lab uses Blender's official CC0 Human Base Mesh bundle, specifically
`GEO-head_animation_realistic`. The supplied head establishes anatomy, UVs, and source topology.
This run tests a rigged facial-expression transfer and driven corrective; it does not claim
autonomous head modeling or retopology authorship.

## Implemented result

- Three comparable specimens: dense corrected reference, uncorrected low-cage transfer, and driven
  corrective low-cage transfer.
- One deforming `Jaw` bone, two non-deforming bilateral smile controls, Armature-before-Subdivision,
  Preserve Volume, a `SmileWide` relative key, and a combined-pose `JawSmileCorrective` key.
- The corrective evaluates to `0.0` at rest, jaw-only, and smile-only, then `1.0` for the combined
  10-degree jaw/smile pose.
- Mouth-region nearest-surface mean error falls from `0.00100663` to `0.00048193` (2.08876x);
  maximum falls from `0.00403267` to `0.00172016`.

## Failure and recovery trail

1. The first jaw mask affected 733 vertices and touched 12 source non-quad faces, producing an
   over-broad rectangular gape. The region was narrowed and vertices incident to non-quads were
   excluded from jaw weighting.
2. The final 123-vertex jaw region passed the localized-density gate. The earlier generic
   250-vertex assertion was rejected because it rewarded broad influence rather than localization.
3. Parent armatures were initially hidden from rendering, which also hid their child heads. The
   render setup was corrected and focused uncorrected/corrected evidence views were added.

## Independent verification

`tools/verify_facial_expression_transfer.py` opens the saved file in a fresh factory-startup
Blender process and imports no project modeling code. It verifies expected objects/bones, base-cage
health, jaw-region quad placement, modifier order/targets, shape keys, driver variables and four
gating states, plus combined-pose evaluated geometry.

All assertions pass. All three evaluated heads have zero non-manifold edges, loose geometry, and
degenerate faces. See `facial_expression_transfer_verify.json`.

## Honest limitations

- The visible expression is subtle and does not establish production-quality acting, anatomy,
  FACS coverage, lip sync, eyelid behavior, inner-mouth behavior, or animator acceptance.
- The dense reference and corrective share an authored deformation hypothesis. Error improvement
  proves the corrective mechanism against that target, not independent anatomical truth.
- The source head is 3,206 quads, 18 triangles, and 10 n-gons. The whole asset is not mislabeled
  all-quad; only the weighted jaw region is proven quad-only.
- No experienced character modeler or rigger supplied an independent artistic review.

## Evidence

- `facial_expression_transfer.blend`
- `facial_expression_transfer_report.json`
- `facial_expression_transfer_verify.json`
- `facial_rest.png`
- `facial_combined_expression.png`
- `facial_uncorrected_expression.png`
- `facial_corrected_expression.png`
- `source_asset_audit.json`
