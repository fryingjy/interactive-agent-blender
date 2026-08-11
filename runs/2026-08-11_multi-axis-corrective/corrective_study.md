# Multi-axis driven corrective study

## Problem

The previous weighted-joint lab tested one-axis bending and ring density. It explicitly left twist
and corrective shape keys open. This run adds a three-bone `Upper`/`Lower`/`Twist` chain, smooth
weights, 72° flex, 18° splay, and 58° distal twist.

## Current official behavior used

- Relative shape-key value blends a key against its Basis; topology should be finalized before
  creating corrective keys because most topology edits do not safely respect shape-key locking.
- Driver variables should carry dependency references rather than direct expression lookups.
- Armature vertex groups provide explicit bone influence; linear blend skinning can lose joint
  volume, while Preserve Volume changes the deformation tradeoff rather than solving every pose.

## Hypothesis and implementation

A corrective limited to the combined flex-and-twist state should restore elbow/twist-root volume
without affecting rest, flex-only, or twist-only poses. The relative `CorrectiveFlexTwist` key adds
localized radial offsets near the elbow and twist root. A scripted driver reads `Lower` local X
rotation and `Twist` local Y rotation and multiplies their gated influences.

Driver values are 0.0 at rest, 0.0 for flex only, 0.0 for twist only, and 1.0 for the combined pose.
The modifier/evaluation order is shape keys → Subdivision Surface → Armature.

## Result

Against a dense corrected reference, the uncorrected low cage has joint mean error 0.05805965 and
joint maximum 0.12682819. The driven corrected cage reduces these to 0.01494744 and 0.02697982,
respectively: a 3.88425× joint-mean improvement. Relative volume error falls from 12.3923% to
5.1967%. All three evaluated posed meshes pass fresh-process checks for manifoldness, n-gons,
loose/degenerate geometry, and outward-positive volume.

## Boundary

The dense reference and low cage share the authored correction hypothesis, so the run proves the
Blender mechanism, gating, and low-cage transfer—not autonomous anatomical discovery. It remains
one stylized limb-like form and one combined pose, without facial expressions or animator review.
