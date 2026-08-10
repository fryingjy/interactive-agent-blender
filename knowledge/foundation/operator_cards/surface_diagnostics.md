# Evaluated surface diagnostics

## Signals

- **Robust Laplacian outlier:** concentrated local displacement relative to median edge length;
  useful for locating a sharp pinch on an otherwise uniform surface.
- **Signed-Laplacian oscillation:** repeated alternating displacement across adjacent edges;
  useful for locating high-frequency waviness.
- **Neighbor-normal angle:** supporting faceting/curvature evidence.

## Interpretation

These signals generate inspection tickets, not confirmed defects. Hard cap transitions, boundaries,
intentional corrugation, and extraordinary topology can score strongly. Always combine them with
surface intent and Blender-native normal/solid/highlight views.

## Evidence

`runs/2026-08-10_surface-diagnostics/` separates a clean and one-vertex-pinched sphere and a uniform
and alternating-radius cylinder. The pinch score changed from 0.9534 to 80.6796; waviness sign
changes changed from 0.0 to 0.476190. All specimens remained technically clean.
