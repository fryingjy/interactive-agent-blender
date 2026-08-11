# Standalone Boolean and Solidify foundation lab

## Status

**PASS** for the scoped documentation/experiment cycle. Foundation status remains **PARTIAL**.

## Environment

- Blender: 5.2.0 LTS
- Build hash: `fbe6228777e7`
- Execution: background, factory startup
- Script: `tools/run_boolean_solidify_foundation_lab.py`

## Task

Close the standalone Boolean/Solidify foundation gap identified after Bevel/Mirror reconciliation.

## Sources

- Blender 5.0 Boolean Modifier Manual.
- Blender Manual Solidify Modifier page and documented limitations.
- Existing repository Boolean failure, repair, retrieval, and transfer evidence.

No video, audio, captions, or transcript were accessed or claimed.

## Experiments

Twelve variants:

- Boolean Exact Difference, Union, and Intersect on overlapping closed boxes.
- Boolean Manifold Difference on the matched closed-box case.
- Exact Difference tangent torus/cylinder groove failure.
- Solidify Fill Rim on/off.
- Solidify Offset -1/0/+1.
- Solidify requested thickness under unapplied versus applied non-uniform scale.

All nine encoded assertions passed.

## Independent evaluated verification

Passed:

- `Boolean_Intersect_Target`: closed, zero n-gons/degenerates, volume 2.25.
- `Solidify_Rim_On`: closed, zero n-gons/degenerates, volume 0.8.
- `Boolean_Difference_Target` with contextual allowance of one n-gon: closed, volume 5.75.

Expected failures correctly detected:

- `Solidify_Rim_Off`: eight non-manifold/boundary edges.
- `Boolean_TangentGroove_Target`: 90 n-gons and 18 degenerate faces despite zero non-manifold edges.

## Claims supported

- Difference, Union, and Intersect produced expected closed volumes on controlled manifold operands.
- Exact and Manifold Difference agreed on volume for the matched closed-box case.
- Tangent/near-coincident Boolean geometry can be manifold while remaining poor topology.
- Fill Rim controls whether an open source surface evaluates as a closed shell.
- Solidify Offset placement followed face-normal direction.
- Non-uniform object scale changed world-space thickness exactly as warned by the Manual.

## Known limitations

- Fast/`FLOAT` solver overlap behavior was read but not yet isolated experimentally.
- Boolean collection operands, Self Intersection, and Hole Tolerant remain untested.
- Solidify Complex mode, Even Thickness on acute/bent geometry, Clamp, vertex groups, materials, and UV behavior remain untested.
- Solidify second-shape transfer is still pending.
- This lab measured topology and volume, not rendered highlight quality.

## Evidence paths

- `boolean_solidify_lab.blend`
- `boolean_solidify_report.json`
- `verify_reports/`
- `knowledge/foundation/operator_cards/boolean_modifier.md`
- `knowledge/foundation/operator_cards/solidify_modifier.md`

## Highest-value next step

Run a curved second-shape Solidify transfer with acute corners and non-uniform orientation, comparing Simple/Complex and Even Thickness, while recording wall-thickness error and self-intersection rather than only topology counts.
