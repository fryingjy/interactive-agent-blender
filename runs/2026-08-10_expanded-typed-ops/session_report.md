# Expanded typed modeling operation surface

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Protocol:** 0.2  
**Status:** PASS after preserved API/fixture failures

## Result

Fifteen cases passed. Thirteen new artistic operations are registered in the modeler transaction
surface: rotate, selected bevel, delete, dissolve, merge, fill, bridge, spin, edge-ring loop cut,
plane bisect, symmetrize, split-in-place, and separate-to-object. Protocol discovery reports all
thirteen.

The loop-cut transaction preserved all eight original vertex IDs, assigned four new vertex IDs,
eight edge IDs, and four face IDs, and advanced scene revision 0 -> 1. Separate-to-object records
an explicit cross-object identity discontinuity; rejecting that transaction restored the original
6-face cube and removed the newly created object. This extends rollback beyond target geometry to
operation-created objects.

Five closed outputs (rotate, bevel, loop cut, bisect, and transaction identity) independently
verified manifold, consistently oriented, nondegenerate, n-gon-free, and without loose geometry.
Open fill/bridge/delete/split fixtures are assessed by their operation-specific counts rather than
incorrectly required to be closed solids.

## Preserved failures

- The first symmetrize call passed UI-style `-X_TO_+X` directly, but Blender 5.2 BMesh accepts only
  `X/-X/Y/-Y/Z/-Z`.
- A full-cube symmetrize fixture was invalid because destination-side geometry already existed.
- Testing a negative-only half established that BMesh `-X` means copy negative X to positive X;
  the public typed API now maps readable source-to-destination labels explicitly.
- Several BMesh operator dictionaries omitted intermediate created geometry despite real count
  changes. Identity clearing now uses pre/post element-set differences rather than return-key guesses.

## Limits

These are mechanical typed primitives. Intelligent selection, operation choice, and acceptance
still belong to one-decision closed-loop reasoning. `separate_selection` intentionally assigns new
IDs in the new object because cross-object persistent identity is not yet represented.
