# Corrective shape keys and pose drivers

## Use

Restore pose-specific volume, silhouette, or crease behavior that weights and ordinary skinning do
not preserve. A corrective is a localized deformation layer, not a substitute for sound topology,
weights, or a suitable armature strategy.

## Preconditions

- Finalize topology before shape-key work; every key depends on stable vertex correspondence.
- Establish and verify the uncorrected posed failure first.
- Name the exact pose channels and region the correction targets.
- Keep Basis, corrective key, armature, vertex groups, and modifier order inspectable.

## Decision and verification

1. Compare rest, single-channel edge cases, and the combined target pose.
2. Author the smallest regional offset that addresses the measured failure.
3. Drive influence through explicit driver variables so dependency tracking is valid.
4. Confirm the driver is inactive outside the intended pose combination.
5. Measure evaluated surface and volume against a credible reference; inspect highlights and
   silhouette as separate channels.
6. Reject the correction if it moves the defect, over-bulges neighboring poses, or hides poor
   weighting that should be repaired directly.

## Failure modes

- Editing topology after shape keys breaks correspondence or leaves inconsistent keys.
- A single rotation threshold can activate during unrelated motion; multi-channel corrections need
  edge-case gating.
- Linear blend collapse may remain despite adequate rings; Preserve Volume changes behavior but can
  introduce other discontinuities and is not an automatic replacement for a corrective.
- A shared formula between reference and candidate proves mechanism/transfer, not anatomical truth.

## Evidence

Current Blender 5.2 LTS Manual: Shape Keys Panel, Drivers Panel, and Armature Modifier. In
`runs/2026-08-11_multi-axis-corrective/`, a driven low cage reduces combined-pose joint mean error
3.88425× and relative volume error from 12.3923% to 5.1967%, remains inactive at rest/flex-only/
twist-only, and passes 3/3 fresh evaluated mesh checks.

`runs/2026-08-11_facial-expression-transfer/` transfers the same combined-channel principle to
Blender's official CC0 animation head. A Jaw + bilateral-smile driver remains `0/0/0` for the three
edge cases and reaches `1.0` only in the combined pose. The corrective reduces mouth-region mean
nearest-surface error 2.08876x and maximum error 2.34436x. A separate fresh-process verifier checks
the saved bones, modifiers, shape keys, driver variables, gating, jaw-region topology, and evaluated
meshes. The expression is visually subtle, so this is transfer/mechanism evidence rather than a
production facial-animation claim.
