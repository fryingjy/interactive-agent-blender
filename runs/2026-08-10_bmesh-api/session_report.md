# Modeler-relevant BMesh API lab

**Status:** PASS (9/9 final assertions, with three preserved API failures).

## Covered behavior

Duplicate removal, degenerate dissolve, n-gon triangulation and face mapping, Limited Dissolve scope, direct shared-edge dissolve, normal recalculation, UV custom data, selection flushing, and owned-copy lifecycle were executed in Blender 5.2.0 LTS.

## Preserved failures

1. `remove_doubles` returned `None`; expecting `result.get("targetmap")` crashed despite the mutation succeeding.
2. Direct `bm.faces[0]` access after creation raised “outdated internal index table” until `ensure_lookup_table()` was called.
3. Limited Dissolve did nothing for narrow selections, then erased the whole open patch when every boundary element was included with boundary dissolving. A direct shared-edge dissolve was the correct scoped operation for that intent.

## Independent checks

The recalculated-normal cube, UV custom-data cube, and ownership cube independently passed manifold, n-gon, loose-geometry, degenerate, and signed-volume checks. Open/degenerated failure specimens were intentionally not misclassified as clean solids.

## Evidence

- `bmesh_api_lab.blend`
- `bmesh_api_report.json`
- `verification/*.json`
- `tools/run_bmesh_api_lab.py`
