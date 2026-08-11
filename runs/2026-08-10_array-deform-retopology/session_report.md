# Array, Shrinkwrap, Simple Deform, and retopology lab

**Status:** PASS after two diagnosed test corrections.

## Results

All 11 final assertions passed across ten saved variants in Blender 5.2.0 LTS.

- Array: three-copy topology, additive Relative+Constant offset, and unapplied-scale world-span effects confirmed.
- Shrinkwrap: nearest-surface conformance and 0.2 offset confirmed; wrong projection direction produced a measured zero-displacement no-op.
- Simple Deform: low-density 180° twist produced four degenerate faces; Simple subdivision before Twist produced a clean 386-vertex result and measurable deformation versus a subdivision-only control.
- Retopology transfer: a 42-vertex cage conformed to a 1,984-vertex sphere target with mean radius 0.9989 and remained independently clean.

## Preserved failures and corrections

1. The first Array assertion compared unlike relative-offset baselines (1.25 versus 1.0+constant). The matched control corrected the experimental design.
2. The first Simple Deform helper set `angle` and then `factor`; Blender 5.2 stores these as mode-specific views of one amount, so the second assignment silently reset Twist to zero. A subdivision-only evaluated control exposed the no-op. The helper now sets only the mode-appropriate amount.
3. The final low-density Twist failed independent verification with four degenerate faces, while the subdivided variant passed. This is an intended failure case, not counted as a clean result.

## Independent verification

Fresh evaluated checks passed Array, subdivided Twist, and the shrinkwrapped retopology cage. Low-density Twist failed exactly as expected. Earlier timestamped verifier files from the inert-modifier attempt remain visible as historical evidence and must not be mistaken for the final run.

## Limits

The sphere cage proves conformance and density reduction, not production deformation flow. Open Shrinkwrap grids intentionally retain boundaries. Visual highlight/contour comparison and a non-spherical retopology transfer remain necessary.
