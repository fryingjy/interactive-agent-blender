# Sculpt-to-retopology and deformation-density lab

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS with preserved coordinate/render-process failures

## Result

The lab appended the 2,562-vertex `BrushSculpt` created by the earlier recorded interactive Sculpt
Draw stroke and projected a 114-vertex low cage onto it. The cage is over 22 times lighter, closed,
nondegenerate, n-gon-free, and independently verified clean. Face-center distance to the actual
sculpt source averages 0.0280 units (95th percentile 0.0377; maximum 0.0907).

A separate deformation test applies the same 70-degree bend to a high-resolution reference, a
17-ring quad cage, and a 5-ring quad cage. The adequate cage reduces mean surface error from
0.02958 to 0.01131 and maximum error from 0.09754 to 0.03182. This demonstrates why deformation
density must follow form change; it does not claim animation-production anatomy or joint weighting.

Three Blender-native passes record the actual sculpt, retopo wire cage, and bent quad routing.

## Preserved failures

- The first distance calculation mixed world-space sample points with a target-local BVH and
  produced impossible 2–3 unit errors. Converting samples through the target inverse transform
  fixed the measurement; the threshold was not changed.
- Loading the source with `open_mainfile()` in GUI mode replaced the running script context and
  left the helper process open. The runner now appends only `BrushSculpt` through Blender's library
  API; the explicitly launched helper process was terminated after diagnosis.
- Initial wire passes used black lines over transparent black and were numerically nonblank but
  visually unreadable. Diagnostic wire output is now light gray; the original visual-pass lab was
  rerun and passed all assertions.
- On two completed render attempts Blender crashed only during application shutdown inside Intel
  driver `igxelpicd64.dll`; reports/images had already been written. One complete GUI pass exited
  cleanly before the wire-contrast correction, and a fresh background verifier independently
  accepted the final saved cage.

## Limits

The deforming tubes are open intentionally and evaluated for routing/error, not closed-solid
validity. The sculpt cage has latitude/longitude flow and pole triangles suitable for this static
rounded form; it is not evidence for facial, shoulder, elbow, or other production articulation.
