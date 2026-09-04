# Secondary-view component strategy

**Status:** controlled two-family transfer | real-prop runtime use open

## Problem

A front silhouette can conceal depth. A full-depth continuous housing and a narrow body carrying a
separate full-front plate may have the same front mask even though they require different topology,
component organization, and edit-mode strategy.

## Executable policy

`modeling_core.assembly` proposes explicit continuous and separate construction graphs, and
`modeling_core.component_fitting` fits at least two executable families per component against the
same registered views. If a primary view cannot discriminate candidates, the fit remains ambiguous
until a same-variant secondary view supplies a sufficient measured margin. The planner may request
that evidence, but it cannot choose the geometry itself.

`CONTINUOUS_MESH` evidence must describe exactly one object and one connected component. Joining
multiple disconnected shells or merely placing them in one collection does not satisfy continuity.

## Blender 5.2 experiment

The controlled run uses rectangular and 16-sided radial housing families. In each family:

- the continuous full-depth body and separate-faceplate control both score `1.0` front IoU;
- the continuous candidate remains `1.0` from the top;
- the separate control falls to `0.711577` (box) and `0.695574` (radial);
- the resulting secondary margins are `0.288423` and `0.304426`;
- a fresh Blender process confirms object count, connected-component count, dimensions, collection
  organization, and exact mask reproduction.

Evidence: `runs/2026-08-15_secondary-view-component-strategy/`.

## Boundary

The original standalone component-strategy scorer was removed after its policy was absorbed into
the fitted assembly path. This is synthetic reconstruction evidence, not automatic image understanding. It does not prove
that the system can discover the correct component boundary in a real photograph or that the
chosen construction improves a held-out prop. That requires a real multi-view task and human visual
review.
