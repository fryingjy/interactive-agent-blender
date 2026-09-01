# IKEA TERTIAL diagnostic — retained failure

This run is **not a passed model** and does not authorize surface work. It is retained because it
exposed systemic camera/segmentation/evaluator weaknesses that drove the 2026-09-01 repair.

## Retained states

- `v1`: original baseline. Normalized hero silhouette IoU 0.2686, centroid error 0.0462, contour
  error 0.0369.
- `v14`: named failed 1.25× articulation hypothesis. It was rejected and rolled back.
- `v15`: restored best blockout. IoU 0.4440, centroid error 0.0063, contour error 0.0150. Gemini v3
  still returns `CORRECT_PRIMARY_FORM` for upper-arm angle/length and scores semantic 0.82,
  silhouette 0.78, component relationships 0.80, and depth 0.85.

The reference segmentation reports zero enclosed negative-space pixels despite visible articulated
gaps. This is now classified as a segmentation-audit failure, not trustworthy geometry evidence.
The single perspective hero also lacks a calibrated camera solution. Therefore the improvement is
directional evidence only; it is not likeness, camera, depth, topology, or human acceptance proof.

## Retention policy

Equivalent intermediate revisions v2–v13 and superseded critic files were deleted. The run keeps
the official reference package, construction/source records, baseline evidence, one named failed
hypothesis, best rejected evidence, and the final critic. No further modeling may continue from this
run while the repository-wide modeling hold is active.
