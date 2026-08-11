# Standalone Bevel and Mirror foundation lab

## Status

**PASS** for the scoped experiment. This is not a foundation-gate pass.

## Environment

- Blender: 5.2.0 LTS
- Build hash: `fbe6228777e7`
- Execution: background, factory startup
- Script: `tools/run_modifier_foundation_lab.py`

## Task

Close the documented gap where Bevel and Mirror had only been studied indirectly through modifier-order pairs, not as standalone modifiers.

## Evidence

- `modifier_foundation_lab.blend`: viewable scene containing all ten variants.
- `modifier_foundation_report.json`: base/evaluated measurements and seven assertions.
- `knowledge/foundation/operator_cards/bevel_modifier.md`
- `knowledge/foundation/operator_cards/mirror_modifier.md`

## Results

- Angle-limited Bevel excluded coplanar triangulation edges in the test mesh (56 evaluated vertices versus 80 with no limit).
- Increasing Bevel segments from 1 to 3 increased evaluated vertices from 24 to 96.
- Clamp Overlap changed the excessive-width result but produced nearly collapsed edges (`~2.38e-7` minimum length); manifoldness did not imply good topology.
- An exact Mirror seam merged cleanly.
- A seam at X=`0.002` remained open with threshold `0.001` (eight boundary/non-manifold edges).
- Threshold `0.01` closed the same seam.
- X Bisect on a cross-plane cube produced a closed evaluated result.

All seven encoded assertions passed.

Independent `tools/verify_mesh.py --evaluated` checks also passed for:

- `Mirror_ExactSeam`: 12 vertices, 20 edges, 10 faces, zero non-manifold edges.
- `Mirror_BisectCrossPlane`: 12 vertices, 20 edges, 10 faces, zero non-manifold edges.
- `Bevel_Segments_3`: 96 vertices, 192 edges, 98 faces, zero non-manifold edges.

A default base-mesh verification of `Bevel_Segments_3` also passed, confirming that the new
evaluated mode did not replace the verifier's existing default behavior.

## Honest limitations

- The lab measures topology and bounds, not highlight flow or self-intersection.
- Bevel miter/intersection modes, Harden Normals, custom profiles, width methods, vertex groups, and non-uniform scale still need dedicated tests.
- Mirror Clipping is an Edit Mode interaction constraint and was read from documentation but not reproduced by this headless evaluated-geometry lab.
- Findings were tested on controlled box-family geometry; second-shape transfer remains pending.

## Highest-value next step

Run a second-shape transfer on curved/cylindrical geometry, including Bevel width behavior under non-uniform scale and Mirror seam behavior under SubD, while keeping standalone findings distinct from stack-order findings.
