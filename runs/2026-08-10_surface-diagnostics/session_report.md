# Evaluated surface concentration and oscillation diagnostics

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS as candidate-location evidence, not an automatic defect classifier

## Results

- A clean UV sphere had maximum robust Laplacian outlier score 0.9534 and zero candidates.
- Pulling one equatorial vertex outward produced score 80.6796 and five localized candidates.
- A uniform cylindrical side had zero meaningful displacement sign changes.
- Alternating ring radii by ±0.10 produced a 0.476190 sign-change ratio.
- All four meshes independently verified closed, nondegenerate, consistently oriented, and free of
  n-gons/loose geometry. Technical validity therefore did not conceal the visual defects.

The metric normalizes local Laplacian displacement by median edge length, uses a robust median/MAD
outlier score for concentrated pinches, and counts meaningful signed-displacement oscillations for
waviness. `get_evaluated_state` now returns these diagnostics through the typed modeler bridge.

## Preserved failure

The first lab invocation failed because package import of `blender_ops.evaluated_probe` still used
the legacy top-level-only `import bmesh_io`. The module now supports both package-relative and
Blender add-on top-level loading.

## Critical limitation

The uniform capped cylinder reports 48 pinch candidates at intentional hard cap/side transitions.
That is not a contradiction: concentrated curvature is real there, but it is design context rather
than automatically bad. Boundaries, hard transitions, and intentional corrugation can resemble
defects. The API labels results `CANDIDATE_EVIDENCE_ONLY`; normal/solid/highlight inspection and
surface intent remain required before repair.
